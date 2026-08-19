# backend/app.py
"""
Immortal Wall AI — FastAPI application entry point.

Dependency injection
────────────────────
All shared singletons (DatabaseManager, ThreatEngine, MLEngine,
ResponseEngine) are created exactly once in ``backend.container`` and
imported here.  No route module or service instantiates its own copy.
"""

from __future__ import annotations

import asyncio
import time
import threading
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import List, Optional

import uvicorn
from dotenv import load_dotenv
from fastapi import (
    BackgroundTasks, Depends, FastAPI, HTTPException,
    Query, Request, WebSocket, WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

load_dotenv()

from backend import config
from backend.container import db, ml_engine, response_engine, threat_engine
from backend.core.security import create_access_token, decode_token, get_current_user
from backend.core.rate_limiter import (
    limiter, rate_limit_exceeded_handler,
    API_LIMIT, ANALYSIS_LIMIT,
)
from backend.routes import auth_routes, log_routes, status_routes, threat_routes
from backend.schemas import ThreatEventSchema          # Pydantic input model
from agent.monitor import Monitor
from agent.collector import Collector
from agent.sender import Sender
from utils.logger import setup_logger

logger = setup_logger("backend")

# ── Agent components ───────────────────────────────────────────────────────
monitor   = Monitor()
collector = Collector()
sender    = Sender()


# ── WebSocket hub ──────────────────────────────────────────────────────────
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.executor = ThreadPoolExecutor(max_workers=4)

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("WS connected — total: %d", len(self.active_connections))

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info("WS disconnected — total: %d", len(self.active_connections))

    async def broadcast(self, message: dict):
        dead = []
        for ws in self.active_connections:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


# ── Background tasks ───────────────────────────────────────────────────────
async def background_monitoring():
    """Push live system status to all WS clients every 5 s."""
    while True:
        try:
            status_data = _build_system_status()
            await manager.broadcast({
                "type":      "system_status",
                "data":      status_data,
                "timestamp": datetime.now().isoformat(),
            })
        except Exception as e:
            logger.error("Background monitoring error: %s", e)
        await asyncio.sleep(5)


async def background_threat_processing():
    """Push the latest threats to all WS clients every 2 s."""
    while True:
        try:
            threats = db.get_recent_threats(limit=10)
            if threats:
                await manager.broadcast({
                    "type":      "new_threats",
                    "data":      threats,
                    "timestamp": datetime.now().isoformat(),
                })
        except Exception as e:
            logger.error("Threat processing error: %s", e)
        await asyncio.sleep(2)


# ── App lifespan ───────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Immortal Wall AI Backend v2.1.0 …")

    monitoring_task = asyncio.create_task(background_monitoring())
    threat_task     = asyncio.create_task(background_threat_processing())

    monitor_thread = threading.Thread(target=monitor.start, daemon=True)
    monitor_thread.start()
    collector.start()
    sender.start()
    logger.info("All agent components started.")

    yield

    logger.info("Shutting down …")
    monitoring_task.cancel()
    threat_task.cancel()
    try:
        monitor.running = False
        if monitor_thread.is_alive():
            monitor_thread.join(timeout=5)
        collector.stop()
        sender.stop()
    except Exception as e:
        logger.error("Shutdown error: %s", e)


# ── FastAPI app ────────────────────────────────────────────────────────────
app = FastAPI(
    title       = "Immortal Wall AI",
    description = "AI-powered cybersecurity threat detection and automated defense.",
    version     = "2.1.0",
    lifespan    = lifespan,
)

app.start_time = time.time()

# ── Rate limiter ───────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# ── CORS ───────────────────────────────────────────────────────────────────
_cors_origins = getattr(config, "CORS_ORIGINS", [
    "http://localhost:5173", "http://localhost:5174",
    "http://localhost:3000", "http://127.0.0.1:3000",
])

app.add_middleware(
    CORSMiddleware,
    allow_origins     = _cors_origins,
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────
app.include_router(auth_routes.router,   prefix="/api/auth")
app.include_router(status_routes.router, prefix="/api/status")
app.include_router(log_routes.router,    prefix="/api/logs")
app.include_router(threat_routes.router, prefix="/api/threats")


# ── WebSocket — token required ─────────────────────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(default=None),
):
    """
    WebSocket endpoint.  Requires ``?token=<jwt>`` query parameter.
    Closes with code 1008 (Policy Violation) if the token is missing or invalid.
    """
    if not token:
        await websocket.close(code=1008, reason="Token required")
        return
    try:
        decode_token(token)
    except HTTPException:
        await websocket.close(code=1008, reason="Invalid or expired token")
        return

    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()   # keep-alive; client pings
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error("WS error: %s", e)
        manager.disconnect(websocket)


# ── Helpers ────────────────────────────────────────────────────────────────
def _build_system_status() -> dict:
    threat_stats   = db.get_threat_statistics()
    recent_threats = db.get_recent_threats(limit=5)
    return {
        "timestamp": datetime.now().isoformat(),
        "threats":   threat_stats,
        "recent_threats": recent_threats,
        "system_metrics": {
            "uptime":              time.time() - app.start_time,
            "active_connections":  len(manager.active_connections),
            "threats_processed":   threat_stats.get("total_threats", 0),
            "ml_predictions":      threat_stats.get("ml_predictions", 0),
        },
        "agent_status": {
            "monitor_active":   getattr(monitor,   "running", False),
            "collector_active": getattr(collector, "running", False),
            "sender_active":    getattr(sender,    "running", False),
        },
    }


# ── REST endpoints ─────────────────────────────────────────────────────────

@app.get("/api/health")
async def health_check():
    """Public health check — no auth required."""
    try:
        db_status  = db.health_check()
        ml_status  = "operational" if ml_engine.model else "degraded"
        agent_status = {
            "monitor":   getattr(monitor,   "running", False),
            "collector": getattr(collector, "running", False),
            "sender":    getattr(sender,    "running", False),
        }
        overall = "healthy" if (
            db_status.get("status") == "healthy"
            and ml_status == "operational"
            and sum(agent_status.values()) >= 2
        ) else "degraded"

        return {
            "status":    overall,
            "timestamp": datetime.now().isoformat(),
            "components": {
                "database":  db_status,
                "ml_engine": {"status": ml_status},
                "agents":    agent_status,
                "websocket": {
                    "status":             "operational",
                    "active_connections": len(manager.active_connections),
                },
            },
        }
    except Exception as e:
        logger.error("Health check error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/system-status")
@limiter.limit(API_LIMIT)
async def get_system_status(
    request: Request,
    _user: dict = Depends(get_current_user),
):
    """Return full system status. Requires bearer token."""
    try:
        return _build_system_status()
    except Exception as e:
        logger.error("System status error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze-threat")
@limiter.limit(ANALYSIS_LIMIT)
async def analyze_threat(
    request:        Request,
    threat_data:    ThreatEventSchema,
    background_tasks: BackgroundTasks,
    _user:          dict = Depends(get_current_user),
):
    """
    Run threat analysis on a validated event payload.
    Requires bearer token.
    """
    try:
        loop   = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            manager.executor,
            threat_engine.analyze_threat,
            threat_data.model_dump(),
        )
        db.store_threat_analysis(result)

        await manager.broadcast({
            "type":      "new_threat",
            "data":      result,
            "timestamp": datetime.now().isoformat(),
        })
        return result
    except Exception as e:
        logger.error("analyze-threat error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics")
@limiter.limit(API_LIMIT)
async def get_analytics(
    request:   Request,
    timeframe: str = "24h",
    _user:     dict = Depends(get_current_user),
):
    """Return analytics data. Requires bearer token."""
    try:
        now = datetime.now()
        delta_map = {
            "1h":  timedelta(hours=1),
            "24h": timedelta(hours=24),
            "7d":  timedelta(days=7),
            "30d": timedelta(days=30),
        }
        start_time = now - delta_map.get(timeframe, timedelta(hours=24))
        analytics  = db.get_analytics(start_time=start_time)
        analytics["real_time"] = {
            "active_connections": len(manager.active_connections),
            "threats_per_minute": db.get_threats_per_minute(),
            "system_load":        "normal",
        }
        return analytics
    except Exception as e:
        logger.error("Analytics error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ml/status")
@limiter.limit(API_LIMIT)
async def ml_status(
    request: Request,
    _user:   dict = Depends(get_current_user),
):
    """Return ML engine status and drift metrics. Requires bearer token."""
    try:
        meta = ml_engine.meta or {}
        return {
            "model_version":      meta.get("model_version", "unknown"),
            "trained_at":         meta.get("trained_at",    "unknown"),
            "n_features":         meta.get("n_features",    0),
            "f1_macro":           meta.get("f1_macro",      0.0),
            "drift_detected":     ml_engine.drift_detected,
            "recent_threat_rate": ml_engine.recent_threat_rate,
            "feature_importances": meta.get("feature_importances", {}),
        }
    except Exception as e:
        logger.error("ML status error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
