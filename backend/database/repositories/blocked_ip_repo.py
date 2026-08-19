# backend/database/repositories/blocked_ip_repo.py
"""BlockedIPRepository — all BlockedIP table operations."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from sqlalchemy.orm import Session

from backend.database.models import BlockedIP


class BlockedIPRepository:
    """Single-responsibility repository for the BlockedIP table."""

    def __init__(self, session: Session) -> None:
        self._s = session

    def block(
        self,
        ip: str,
        hard_block: bool = True,
        reason: Optional[str] = None,
    ) -> BlockedIP:
        """
        Insert or update a BlockedIP record.

        If the IP already has an active record (unblocked_at IS NULL),
        update it in-place.  If it was previously unblocked, clear
        unblocked_at so it is active again.
        """
        existing = self._s.query(BlockedIP).filter(BlockedIP.ip == ip).first()
        if existing:
            existing.hard_block   = hard_block
            existing.reason       = reason or existing.reason
            existing.blocked_at   = datetime.utcnow()
            existing.unblocked_at = None
            self._s.commit()
            self._s.refresh(existing)
            return existing

        record = BlockedIP(
            ip           = ip,
            hard_block   = hard_block,
            reason       = reason,
            blocked_at   = datetime.utcnow(),
            unblocked_at = None,
        )
        self._s.add(record)
        self._s.commit()
        self._s.refresh(record)
        return record

    def unblock(self, ip: str) -> bool:
        """
        Mark an IP as unblocked by setting unblocked_at.

        Returns True if a record was found and updated, False otherwise.
        """
        record = (
            self._s.query(BlockedIP)
            .filter(BlockedIP.ip == ip, BlockedIP.unblocked_at == None)   # noqa: E711
            .first()
        )
        if not record:
            return False
        record.unblocked_at = datetime.utcnow()
        self._s.commit()
        return True

    def get_active(self, limit: int = 1000, offset: int = 0) -> List[Dict[str, Any]]:
        """Return all IPs that are currently blocked (unblocked_at IS NULL)."""
        rows = (
            self._s.query(BlockedIP)
            .filter(BlockedIP.unblocked_at == None)   # noqa: E711
            .order_by(BlockedIP.blocked_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [self._to_dict(r) for r in rows]

    def get_all(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Return all block records (including previously unblocked IPs)."""
        rows = (
            self._s.query(BlockedIP)
            .order_by(BlockedIP.blocked_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [self._to_dict(r) for r in rows]

    def load_active_set(self) -> Set[str]:
        """
        Return all currently-blocked IPs as a plain Python set.
        Used at startup to populate the in-memory cache.
        """
        rows = (
            self._s.query(BlockedIP.ip)
            .filter(BlockedIP.unblocked_at == None)   # noqa: E711
            .all()
        )
        return {row.ip for row in rows}

    # ── Internal ───────────────────────────────────────────────────────────

    @staticmethod
    def _to_dict(r: BlockedIP) -> Dict[str, Any]:
        return {
            "id":           r.id,
            "ip":           r.ip,
            "blocked_at":   r.blocked_at.isoformat() if r.blocked_at else None,
            "hard_block":   r.hard_block,
            "reason":       r.reason,
            "unblocked_at": r.unblocked_at.isoformat() if r.unblocked_at else None,
        }
