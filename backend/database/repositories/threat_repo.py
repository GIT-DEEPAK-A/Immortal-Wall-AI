# backend/database/repositories/threat_repo.py
"""ThreatRepository — all Threat table operations."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import func, literal_column
from sqlalchemy.orm import Session

from backend.database.models import Threat


def _hour_bucket_expr(session: Session, col_name: str = "threats.timestamp"):
    """
    Return a DB-portable SQL expression that truncates a timestamp to the hour.

    Dialect detection is done via the session's bind URL so a single codebase
    works with SQLite (development), PostgreSQL (production), and MySQL.

    Returns a SQLAlchemy ``text()`` label-compatible clause.
    """
    try:
        dialect = session.get_bind().dialect.name
    except Exception:
        dialect = "sqlite"

    if dialect == "postgresql":
        # Returns "YYYY-MM-DD HH24:00:00"
        return literal_column(
            f"to_char(date_trunc('hour', {col_name}), 'YYYY-MM-DD HH24:00:00')"
        )
    elif dialect in ("mysql", "mariadb"):
        return literal_column(f"DATE_FORMAT({col_name}, '%Y-%m-%d %H:00:00')")
    else:
        # SQLite (default)
        return func.strftime("%Y-%m-%d %H:00:00", literal_column(col_name))


class ThreatRepository:
    """Single-responsibility repository for the Threat table."""

    def __init__(self, session: Session) -> None:
        self._s = session

    # ── Write ──────────────────────────────────────────────────────────────

    def create(self, threat_data: Dict[str, Any]) -> Threat:
        """Persist a new threat record and return the ORM instance."""
        raw_ts = threat_data.get("timestamp", datetime.utcnow().timestamp())
        # Accept int/float epoch or datetime
        if isinstance(raw_ts, (int, float)):
            ts = datetime.utcfromtimestamp(raw_ts)
        else:
            ts = raw_ts

        threat = Threat(
            timestamp        = ts,
            ip_address       = threat_data.get("ip_address", threat_data.get("ip", "unknown")),
            threat_level     = threat_data.get("threat_level", "unknown"),
            threat_score     = float(threat_data.get("threat_score", 0.0)),
            confidence       = float(threat_data.get("confidence", 0.0)),
            threat_type      = threat_data.get("threat_type", "unknown"),
            description      = threat_data.get("description", ""),
            user_agent       = threat_data.get("user_agent", ""),
            request_data     = threat_data.get("request_data", {}),
            ml_prediction    = threat_data.get("ml_result", {}),
            rule_matches     = threat_data.get("rule_matches", []),
            response_actions = threat_data.get("response_actions", []),
            blocked          = bool(threat_data.get("blocked", False)),
            source           = threat_data.get("source", "unknown"),
        )
        self._s.add(threat)
        self._s.commit()
        self._s.refresh(threat)
        return threat

    # ── Read ───────────────────────────────────────────────────────────────

    def get_many(
        self,
        limit: int = 50,
        offset: int = 0,
        severity: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Return paginated threats, newest first."""
        q = self._s.query(Threat).order_by(Threat.timestamp.desc())
        if severity:
            q = q.filter(Threat.threat_level == severity)
        rows = q.offset(offset).limit(limit).all()
        return [self._to_dict(t) for t in rows]

    def get_count(self, severity: Optional[str] = None) -> int:
        """Return total threat count, optionally filtered by severity."""
        q = self._s.query(func.count(Threat.id))
        if severity:
            q = q.filter(Threat.threat_level == severity)
        return q.scalar() or 0

    def get_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Return the *limit* most recent threats."""
        return self.get_many(limit=limit, offset=0)

    def get_statistics(self) -> Dict[str, Any]:
        """Return aggregate statistics used by the dashboard."""
        total = self._s.query(func.count(Threat.id)).scalar() or 0

        levels = {
            lvl: cnt
            for lvl, cnt in self._s.query(Threat.threat_level, func.count(Threat.id))
            .group_by(Threat.threat_level)
            .all()
        }
        types = {
            t: cnt
            for t, cnt in self._s.query(Threat.threat_type, func.count(Threat.id))
            .group_by(Threat.threat_type)
            .all()
        }
        yesterday = datetime.utcnow() - timedelta(hours=24)
        recent_24h = (
            self._s.query(func.count(Threat.id))
            .filter(Threat.timestamp >= yesterday)
            .scalar() or 0
        )
        blocked = (
            self._s.query(func.count(Threat.id))
            .filter(Threat.blocked == True)   # noqa: E712
            .scalar() or 0
        )
        avg_score = self._s.query(func.avg(Threat.threat_score)).scalar() or 0.0

        return {
            "total_threats":        total,
            "threat_levels":        levels,
            "threat_types":         types,
            "recent_threats_24h":   recent_24h,
            "blocked_threats":      blocked,
            "average_threat_score": float(avg_score),
            "ml_predictions":       total,
        }

    def get_analytics(self, start_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Return time-series analytics for the dashboard."""
        if start_time is None:
            start_time = datetime.utcnow() - timedelta(hours=24)

        hour_expr = _hour_bucket_expr(self._s)

        hourly = (
            self._s.query(
                hour_expr.label("hour"),
                func.count(Threat.id).label("count"),
            )
            .filter(Threat.timestamp >= start_time)
            .group_by(hour_expr)
            .order_by("hour")
            .all()
        )

        top_ips = (
            self._s.query(Threat.ip_address, func.count(Threat.id).label("count"))
            .filter(Threat.timestamp >= start_time)
            .group_by(Threat.ip_address)
            .order_by(func.count(Threat.id).desc())
            .limit(10)
            .all()
        )

        level_dist = (
            self._s.query(Threat.threat_level, func.count(Threat.id))
            .filter(Threat.timestamp >= start_time)
            .group_by(Threat.threat_level)
            .all()
        )

        return {
            "threat_trends":       [{"hour": h, "count": c} for h, c in hourly],
            "top_threat_sources":  [{"ip": ip, "count": cnt} for ip, cnt in top_ips],
            "threat_distribution": {lvl: cnt for lvl, cnt in level_dist},
            "response_effectiveness": {},
            "time_range": {
                "start": start_time.isoformat(),
                "end":   datetime.utcnow().isoformat(),
            },
        }

    def get_threats_per_minute(self) -> float:
        """Return the average threat rate over the last 10 minutes."""
        ten_ago = datetime.utcnow() - timedelta(minutes=10)
        count = (
            self._s.query(func.count(Threat.id))
            .filter(Threat.timestamp >= ten_ago)
            .scalar() or 0
        )
        return count / 10.0

    # ── Internal ───────────────────────────────────────────────────────────

    @staticmethod
    def _to_dict(t: Threat) -> Dict[str, Any]:
        return {
            "id":           t.id,
            "timestamp":    t.timestamp.isoformat(),
            "ip_address":   t.ip_address,
            "threat_level": t.threat_level,
            "threat_score": t.threat_score,
            "confidence":   t.confidence,
            "threat_type":  t.threat_type,
            "description":  t.description,
            "user_agent":   t.user_agent,
            "blocked":      t.blocked,
            "source":       t.source,
        }
