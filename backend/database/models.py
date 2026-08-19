# backend/database/models.py
"""
SQLAlchemy ORM model definitions only.
Business logic lives in the repository classes under backend/database/repositories/.

OTPEntry
────────
The OTPEntry model has been retired.  It is preserved in
``backend/database/legacy_models.py`` for reference / migration history but
is NOT imported here and will NOT create a table on startup.
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Threat(Base):
    __tablename__ = "threats"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    timestamp       = Column(DateTime, default=datetime.utcnow, index=True)
    ip_address      = Column(String(45), index=True)
    threat_level    = Column(String(20), index=True)   # normal | suspicious | malicious
    threat_score    = Column(Float, default=0.0)
    confidence      = Column(Float, default=0.0)
    threat_type     = Column(String(50), index=True)
    description     = Column(Text)
    user_agent      = Column(Text)
    request_data    = Column(JSON)
    ml_prediction   = Column(JSON)
    rule_matches    = Column(JSON)
    response_actions = Column(JSON)
    blocked         = Column(Boolean, default=False)
    source          = Column(String(50), default="unknown")


class LogEntry(Base):
    __tablename__ = "logs"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    timestamp    = Column(DateTime, default=datetime.utcnow, index=True)
    level        = Column(String(10), index=True)    # INFO | WARNING | ERROR | CRITICAL
    component    = Column(String(50), index=True)
    message      = Column(Text)
    log_metadata = Column(JSON)


class AnalyticsCache(Base):
    __tablename__ = "analytics_cache"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    cache_key  = Column(String(100), unique=True, index=True)
    data       = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)


class SystemMetrics(Base):
    __tablename__ = "system_metrics"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    timestamp       = Column(DateTime, default=datetime.utcnow, index=True)
    metric_name     = Column(String(100), index=True)
    metric_value    = Column(Float)
    metric_metadata = Column(JSON)


class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    email         = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    salt          = Column(String(64), nullable=False)
    role          = Column(String(20), default="Analyst")
    created_at    = Column(DateTime, default=datetime.utcnow)


class BlockedIP(Base):
    """Persistent record of every IP block/unblock action."""
    __tablename__ = "blocked_ips"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    ip           = Column(String(45), unique=True, index=True, nullable=False)
    blocked_at   = Column(DateTime, default=datetime.utcnow, nullable=False)
    hard_block   = Column(Boolean, default=True, nullable=False)
    reason       = Column(Text, nullable=True)
    unblocked_at = Column(DateTime, nullable=True)   # NULL means still blocked
