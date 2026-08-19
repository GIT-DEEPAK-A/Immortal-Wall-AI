# backend/app.py

import asyncio
import os
import time
import threading
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import List

import uvicorn
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

load_dotenv()

from backend.routes import auth_routes, log_routes, status_routes, threat_routes
from backend.services.threat_engine import ThreatEngine
from backend.services.ml_engine import AdvancedMLEngine
from backend.services.response_engine import ResponseEngine
from backend.database.db import DatabaseManager
from agent.monitor import Monitor
from agent.collector import Collector
from agent.sender import Sender
from simulation.traffic_generator import TrafficGenerator
from utils.logger import setup_logger

logger = setup_logger("backend")

# ── Global singletons ──────────────────────────────────────────────────────
db_manager    = DatabaseManager()
threat_engine = ThreatEngine()
ml_engine     = AdvancedMLEngine()
response_engine = ResponseEngine()
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
        logger.info(f"WS connected — total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WS disconnected — total: {len(self.active_connections)}")

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
            status = _build_system_status()
            await manager.broadcast({
                "type": "system_status",
                "data": status,
                "timestamp": datetime.now().isoformat(),
            })
        except Exception as e:
            logger.error(f"Background monitoring error: {e}")
        await asyncio.sleep(5)


async def background_threat_processing():
    """Push the latest threats to all WS clients every 2 s."""
    while True:
        try:
            threats = db_manager.get_recent_threats(limit=10)
            if threats:
                await manager.broadcast({
                    "type": "new_threats",
                    "data": threats,
                    "timestamp": datetime.now().isoformat(),
                })
        except Exception as e:
            logger.error(f"Threat processing error: {e}")
        await asyncio.sleep(2)


# ── App lifespan ───────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Immortal Wall AI Backend v2.0.0 …")

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
        logger.error(f"Shutdown error: {e}")


# ── FastAPI app ────────────────────────────────────────────────────────────
app = FastAPI(
    title="Immortal Wall AI",
    description="AI-powered cybersecurity threat detection and automated defense.",
    version="2.0.0",
    lifespan=lifespan,
)

app.start_time = time.time()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://localhost:5177",
        "http://localhost:5178",
        "http://localhost:5179",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────
app.include_router(auth_routes.router,   prefix="/api/auth")
app.include_router(status_routes.router, prefix="/api/status")
app.include_router(log_routes.router,    prefix="/api/logs")
app.include_router(threat_routes.router, prefix="/api/threats")


# ── WebSocket ──────────────────────────────────────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()   # keep-alive; client pings
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WS error: {e}")
        manager.disconnect(websocket)


# ── Helpers ────────────────────────────────────────────────────────────────
def _build_system_status() -> dict:
    threat_stats   = db_manager.get_threat_statistics()
    recent_threats = db_manager.get_recent_threats(limit=5)
    return {
        "timestamp": datetime.now().isoformat(),
        "threats": threat_stats,
        "recent_threats": recent_threats,
        "system_metrics": {
            "uptime": time.time() - app.start_time,
            "active_connections": len(manager.active_connections),
            "threats_processed": threat_stats.get("total_threats", 0),
            "ml_predictions":    threat_stats.get("ml_predictions", 0),
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
    try:
        db_status = db_manager.health_check()
        ml_status = "operational" if ml_engine.model else "degraded"
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
            "status": overall,
            "timestamp": datetime.now().isoformat(),
            "components": {
                "database":   db_status,
                "ml_engine":  {"status": ml_status},
                "agents":     agent_status,
                "websocket":  {
                    "status": "operational",
                    "active_connections": len(manager.active_connections),
                },
            },
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/system-status")
async def get_system_status():
    try:
        return _build_system_status()
    except Exception as e:
        logger.error(f"System status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze-threat")
async def analyze_threat(threat_data: dict, background_tasks: BackgroundTasks):
    try:
        if not threat_data:
            raise HTTPException(status_code=400, detail="threat_data is required")
        threat_data.setdefault("timestamp", int(time.time()))

        loop   = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            manager.executor, threat_engine.analyze_threat, threat_data
        )
        db_manager.store_threat_analysis(result)

        await manager.broadcast({
            "type": "new_threat",
            "data": result,
            "timestamp": datetime.now().isoformat(),
        })
        return result
    except Exception as e:
        logger.error(f"analyze-threat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics")
async def get_analytics(timeframe: str = "24h"):
    try:
        now = datetime.now()
        delta_map = {"1h": timedelta(hours=1), "24h": timedelta(hours=24),
                     "7d": timedelta(days=7),  "30d": timedelta(days=30)}
        start_time = now - delta_map.get(timeframe, timedelta(hours=24))

        analytics = db_manager.get_analytics(start_time=start_time)
        analytics["real_time"] = {
            "active_connections": len(manager.active_connections),
            "threats_per_minute": db_manager.get_threats_per_minute(),
            "system_load": "normal",
        }
        return analytics
    except Exception as e:
        logger.error(f"Analytics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/response")
async def trigger_response(response_config: dict):
    try:
        if not response_config:
            raise HTTPException(status_code=400, detail="response_config is required")
        response_type = response_config.get("type")
        if response_type not in ["block_ip", "rate_limit", "alert", "isolate"]:
            raise HTTPException(status_code=400, detail="Invalid response type")

        result = response_engine.execute_response(response_config)
        await manager.broadcast({
            "type": "response_action",
            "data": {
                "response_type": response_type,
                "threat_id": response_config.get("threat_id"),
                "result": result,
                "timestamp": datetime.now().isoformat(),
            },
        })
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"Response error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/simulation/start")
async def start_simulation(config: dict = None):
    try:
        config = config or {"intensity": "medium"}
        TrafficGenerator().start()
        return {"status": "simulation_started", "config": config}
    except Exception as e:
        logger.error(f"Simulation start error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/simulation/stop")
async def stop_simulation():
    return {"status": "simulation_stopped"}


# ── Error handlers ─────────────────────────────────────────────────────────
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "timestamp": datetime.now().isoformat()},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "timestamp": datetime.now().isoformat()},
    )


if __name__ == "__main__":
    uvicorn.run("backend.app:app", host="0.0.0.0", port=8000, reload=True)
