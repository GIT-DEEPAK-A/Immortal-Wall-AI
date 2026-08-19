# backend/database/queries.py
# Convenience query helpers used across routes and services.
# All functions accept an open SQLAlchemy Session as their first argument.

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from .models import Threat, LogEntry, SystemMetrics


# ── Threat queries ─────────────────────────────────────────────────────────


def get_threats_by_ip(session: Session, ip: str, limit: int = 50) -> List[Threat]:
    """Return all threat records for a specific IP, most recent first."""
    return (
        session.query(Threat)
        .filter(Threat.ip_address == ip)
        .order_by(Threat.timestamp.desc())
        .limit(limit)
        .all()
    )


def get_threats_in_window(
    session: Session, hours: int = 24, severity: Optional[str] = None
) -> List[Threat]:
    """Return threats from the last N hours, optionally filtered by severity."""
    since = datetime.utcnow() - timedelta(hours=hours)
    q = session.query(Threat).filter(Threat.timestamp >= since)
    if severity:
        q = q.filter(Threat.threat_level == severity)
    return q.order_by(Threat.timestamp.desc()).all()


def count_threats_by_level(session: Session) -> Dict[str, int]:
    """Return a dict mapping threat_level → count."""
    rows = session.query(Threat.threat_level, func.count(Threat.id)).group_by(Threat.threat_level).all()
    return {level: count for level, count in rows}


def top_attacking_ips(session: Session, limit: int = 10, hours: int = 24) -> List[Dict[str, Any]]:
    """Return the top N IPs by threat count within the given window."""
    since = datetime.utcnow() - timedelta(hours=hours)
    rows = (
        session.query(Threat.ip_address, func.count(Threat.id).label("count"))
        .filter(Threat.timestamp >= since)
        .group_by(Threat.ip_address)
        .order_by(func.count(Threat.id).desc())
        .limit(limit)
        .all()
    )
    return [{"ip": ip, "count": count} for ip, count in rows]


def get_hourly_threat_counts(session: Session, hours: int = 24) -> List[Dict[str, Any]]:
    """Return threat counts bucketed by hour for the last N hours (DB-portable)."""
    from backend.database.repositories.threat_repo import _hour_bucket_expr
    since     = datetime.utcnow() - timedelta(hours=hours)
    hour_expr = _hour_bucket_expr(session)
    rows = (
        session.query(
            hour_expr.label("hour"),
            func.count(Threat.id).label("count"),
        )
        .filter(Threat.timestamp >= since)
        .group_by(hour_expr)
        .order_by("hour")
        .all()
    )
    return [{"hour": hour, "count": count} for hour, count in rows]


def get_blocked_threat_count(session: Session) -> int:
    """Return the total number of blocked threats."""
    return session.query(func.count(Threat.id)).filter(Threat.blocked == True).scalar() or 0


# ── Log queries ────────────────────────────────────────────────────────────


def get_logs_by_component(session: Session, component: str, limit: int = 100) -> List[LogEntry]:
    """Return log entries for a specific component, most recent first."""
    return (
        session.query(LogEntry)
        .filter(LogEntry.component == component)
        .order_by(LogEntry.timestamp.desc())
        .limit(limit)
        .all()
    )


def get_error_logs(session: Session, limit: int = 50) -> List[LogEntry]:
    """Return ERROR and CRITICAL log entries."""
    return (
        session.query(LogEntry)
        .filter(LogEntry.level.in_(["ERROR", "CRITICAL"]))
        .order_by(LogEntry.timestamp.desc())
        .limit(limit)
        .all()
    )


# ── Metric queries ─────────────────────────────────────────────────────────


def get_latest_metric(session: Session, metric_name: str) -> Optional[SystemMetrics]:
    """Return the most recent record for a given metric name."""
    return (
        session.query(SystemMetrics)
        .filter(SystemMetrics.metric_name == metric_name)
        .order_by(SystemMetrics.timestamp.desc())
        .first()
    )


def get_metric_average(session: Session, metric_name: str, hours: int = 24) -> float:
    """Return the average value of a metric over the last N hours."""
    since = datetime.utcnow() - timedelta(hours=hours)
    result = (
        session.query(func.avg(SystemMetrics.metric_value))
        .filter(SystemMetrics.metric_name == metric_name, SystemMetrics.timestamp >= since)
        .scalar()
    )
    return float(result) if result is not None else 0.0
