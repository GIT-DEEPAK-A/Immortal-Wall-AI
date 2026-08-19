"""
backend/database/db.py
───────────────────────
Session factory and FastAPI dependency for database access.

Session leak fix
────────────────
Every DatabaseManager method previously called self._session() and returned
a raw Session that was never closed.  All methods now use a context manager
(``with self._factory() as session``) so sessions are always returned to the
pool, even if an exception is raised mid-query.

Also re-exports DatabaseManager for backwards compatibility with any code
that does ``from backend.database.db import DatabaseManager``.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from backend.database.models import Base

# ── Path resolution ────────────────────────────────────────────────────────
_ROOT    = Path(__file__).parent.parent.parent
_DB_PATH = _ROOT / "data" / "immortal_wall.db"

_DB_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{_DB_PATH}")


# ── Engine & session factory ───────────────────────────────────────────────

def get_engine(db_url: str = None):
    """Return a configured SQLAlchemy engine."""
    url = db_url or _DB_URL
    if url.startswith("sqlite:///") and not url.endswith(":memory:"):
        db_file = Path(url.replace("sqlite:///", ""))
        db_file.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(url, connect_args={"check_same_thread": False}, echo=False)


def get_session_factory(engine=None) -> sessionmaker:
    """Return a configured sessionmaker bound to *engine*."""
    eng = engine or get_engine()
    return sessionmaker(autocommit=False, autoflush=False, bind=eng)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a database session and closes it afterwards.

    Usage
    ─────
    @router.get("/resource")
    def endpoint(db: Session = Depends(get_db)):
        ...
    """
    factory = get_session_factory()
    db = factory()
    try:
        yield db
    finally:
        db.close()


# ── DatabaseManager facade (backwards-compat) ──────────────────────────────

from backend.database.repositories.threat_repo    import ThreatRepository
from backend.database.repositories.log_repo       import LogRepository
from backend.database.repositories.user_repo      import UserRepository
from backend.database.repositories.blocked_ip_repo import BlockedIPRepository


class DatabaseManager:
    """
    Thin facade that delegates to repository classes.

    Session management
    ──────────────────
    Every public method opens a fresh session via _session() (a context
    manager), performs its work, and closes the session on exit — even
    if an exception is raised.  No session is ever left open.
    """

    def __init__(self, db_path: str = None) -> None:
        if db_path == ":memory:":
            db_url = "sqlite:///:memory:"
        elif db_path:
            db_url = f"sqlite:///{db_path}"
        else:
            db_url = _DB_URL

        self._engine  = get_engine(db_url)
        self._factory = get_session_factory(self._engine)

        # Create all tables (idempotent)
        Base.metadata.create_all(bind=self._engine)

        # Seed default users on first run
        with self._session() as s:
            UserRepository(s).seed_defaults()

    # ── Session helper (context manager) ──────────────────────────────────

    @contextmanager
    def _session(self) -> Generator[Session, None, None]:
        """Yield a session and guarantee it is closed on exit."""
        session = self._factory()
        try:
            yield session
        finally:
            session.close()

    def get_session(self) -> Session:
        """
        Return a raw session for callers that manage their own lifecycle.
        Prefer _session() (context manager) wherever possible.
        """
        return self._factory()

    # ── Health ─────────────────────────────────────────────────────────────

    def health_check(self) -> dict:
        """Return database connectivity status."""
        try:
            with self._session() as s:
                s.execute(text("SELECT 1")).scalar()
            return {
                "status":     "healthy",
                "connection": "ok",
                "tables":     len(Base.metadata.tables),
            }
        except Exception as e:
            return {"status": "unhealthy", "connection": "failed", "error": str(e)}

    # ── Threat delegation ──────────────────────────────────────────────────

    def store_threat_analysis(self, threat_data: dict) -> bool:
        """Persist a threat analysis result. Returns True on success."""
        try:
            with self._session() as s:
                ThreatRepository(s).create(threat_data)
            return True
        except Exception as e:
            import logging
            logging.getLogger("backend.db").error("store_threat_analysis error: %s", e)
            return False

    def get_threats(self, limit: int = 50, offset: int = 0, severity: str = None):
        with self._session() as s:
            return ThreatRepository(s).get_many(limit=limit, offset=offset, severity=severity)

    def get_threat_count(self, severity: str = None) -> int:
        with self._session() as s:
            return ThreatRepository(s).get_count(severity=severity)

    def get_recent_threats(self, limit: int = 10):
        with self._session() as s:
            return ThreatRepository(s).get_recent(limit=limit)

    def get_threat_statistics(self) -> dict:
        with self._session() as s:
            return ThreatRepository(s).get_statistics()

    def get_analytics(self, start_time=None) -> dict:
        with self._session() as s:
            return ThreatRepository(s).get_analytics(start_time=start_time)

    def get_threats_per_minute(self) -> float:
        with self._session() as s:
            return ThreatRepository(s).get_threats_per_minute()

    # ── Log delegation ─────────────────────────────────────────────────────

    def store_log_entry(self, level: str, component: str, message: str, metadata: dict = None) -> bool:
        try:
            with self._session() as s:
                LogRepository(s).create(level, component, message, metadata)
            return True
        except Exception as e:
            import logging
            logging.getLogger("backend.db").error("store_log_entry error: %s", e)
            return False

    def get_logs(self, limit: int = 100, level: str = None, component: str = None):
        with self._session() as s:
            return LogRepository(s).get_many(limit=limit, level=level, component=component)

    # ── User delegation ────────────────────────────────────────────────────

    def create_user(self, email: str, password: str, role: str = "Analyst") -> bool:
        with self._session() as s:
            return UserRepository(s).create(email, password, role)

    def get_user_by_email(self, email: str):
        with self._session() as s:
            return UserRepository(s).get_by_email(email)

    def verify_user_password(self, email: str, password: str) -> bool:
        with self._session() as s:
            return UserRepository(s).verify_password(email, password)

    # ── BlockedIP delegation ───────────────────────────────────────────────

    def get_blocked_ips(self, limit: int = 100, offset: int = 0):
        with self._session() as s:
            return BlockedIPRepository(s).get_all(limit=limit, offset=offset)

    def load_active_blocked_ips(self):
        with self._session() as s:
            return BlockedIPRepository(s).load_active_set()

    def block_ip_in_db(self, ip: str, hard_block: bool = True, reason: str = None):
        with self._session() as s:
            return BlockedIPRepository(s).block(ip, hard_block=hard_block, reason=reason)

    def unblock_ip_in_db(self, ip: str) -> bool:
        with self._session() as s:
            return BlockedIPRepository(s).unblock(ip)

    # ── System metrics ─────────────────────────────────────────────────────

    def store_system_metric(self, metric_name: str, value: float, metadata: dict = None) -> bool:
        from backend.database.models import SystemMetrics
        try:
            with self._session() as s:
                s.add(SystemMetrics(
                    metric_name     = metric_name,
                    metric_value    = value,
                    metric_metadata = metadata or {},
                ))
                s.commit()
            return True
        except Exception as e:
            import logging
            logging.getLogger("backend.db").error("store_system_metric error: %s", e)
            return False

    def get_system_metrics(self, metric_name: str = None, hours: int = 24):
        from datetime import datetime, timedelta
        from backend.database.models import SystemMetrics
        try:
            with self._session() as s:
                q = s.query(SystemMetrics).filter(
                    SystemMetrics.timestamp >= datetime.utcnow() - timedelta(hours=hours)
                ).order_by(SystemMetrics.timestamp.desc())
                if metric_name:
                    q = q.filter(SystemMetrics.metric_name == metric_name)
                return [
                    {
                        "id":          m.id,
                        "timestamp":   m.timestamp.isoformat(),
                        "metric_name": m.metric_name,
                        "value":       m.metric_value,
                        "metadata":    m.metric_metadata,
                    }
                    for m in q.limit(1000).all()
                ]
        except Exception as e:
            import logging
            logging.getLogger("backend.db").error("get_system_metrics error: %s", e)
            return []
