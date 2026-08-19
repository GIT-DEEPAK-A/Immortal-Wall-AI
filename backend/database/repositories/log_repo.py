# backend/database/repositories/log_repo.py
"""LogRepository — all LogEntry table operations."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from backend.database.models import LogEntry


class LogRepository:
    """Single-responsibility repository for the LogEntry table."""

    def __init__(self, session: Session) -> None:
        self._s = session

    def create(
        self,
        level: str,
        component: str,
        message: str,
        metadata: Optional[Dict] = None,
    ) -> LogEntry:
        """Persist a new log entry and return the ORM instance."""
        entry = LogEntry(
            level        = level.upper(),
            component    = component,
            message      = message,
            log_metadata = metadata or {},
        )
        self._s.add(entry)
        self._s.commit()
        self._s.refresh(entry)
        return entry

    def get_many(
        self,
        limit: int = 100,
        level: Optional[str] = None,
        component: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Return log entries, newest first, with optional filters."""
        q = self._s.query(LogEntry).order_by(LogEntry.timestamp.desc())
        if level:
            q = q.filter(LogEntry.level == level.upper())
        if component:
            q = q.filter(LogEntry.component == component)
        rows = q.limit(limit).all()
        return [
            {
                "id":        r.id,
                "timestamp": r.timestamp.isoformat(),
                "level":     r.level,
                "component": r.component,
                "message":   r.message,
                "metadata":  r.log_metadata,
            }
            for r in rows
        ]
