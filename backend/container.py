"""
backend/container.py
────────────────────
Application-level dependency container.

Creates exactly ONE instance of each shared singleton and exposes them as
module-level names.  All routes, services, and the lifespan hook import
from here — there is never a second DatabaseManager or a second
ResponseEngine with a stale blocked_ips cache.

Usage
─────
    from backend.container import db, response_engine, threat_engine, ml_engine

FastAPI dependency injection
────────────────────────────
    from backend.container import get_db_manager
    def endpoint(db_mgr = Depends(get_db_manager)): ...
"""

from __future__ import annotations

from backend.database.db import DatabaseManager
from backend.services.ml_engine import AdvancedMLEngine
from backend.services.response_engine import ResponseEngine
from backend.services.threat_engine import ThreatEngine

# ── Shared singletons (created once at import time) ────────────────────────
db: DatabaseManager = DatabaseManager()
ml_engine: AdvancedMLEngine = AdvancedMLEngine()
response_engine: ResponseEngine = ResponseEngine(db_manager=db)
threat_engine: ThreatEngine = ThreatEngine(
    ml_engine=ml_engine,
    response_engine=response_engine,
)


# ── FastAPI dependency helpers ─────────────────────────────────────────────

def get_db_manager() -> DatabaseManager:
    """Yield the shared DatabaseManager (FastAPI Depends helper)."""
    return db


def get_response_engine() -> ResponseEngine:
    """Yield the shared ResponseEngine (FastAPI Depends helper)."""
    return response_engine


def get_threat_engine() -> ThreatEngine:
    """Yield the shared ThreatEngine (FastAPI Depends helper)."""
    return threat_engine
