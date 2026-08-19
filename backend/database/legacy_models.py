"""
backend/database/legacy_models.py
───────────────────────────────────
Retired ORM models kept here for migration reference only.

These models are NOT imported into models.py and will NOT create tables
on application startup.  If you need to run a data migration from an
older database that has an ``otps`` table, import from here.
"""

from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String
from backend.database.models import Base


class OTPEntry(Base):
    """
    One-time-password entries — retired in v2.1.0.
    Authentication now uses email + PBKDF2 password via UserRepository.
    """
    __tablename__ = "otps"
    __table_args__ = {"extend_existing": True}

    id          = Column(Integer, primary_key=True, autoincrement=True)
    email       = Column(String(255), index=True, nullable=False)
    otp_hash    = Column(String(128), nullable=False)
    expiry_time = Column(DateTime, nullable=False)
    attempts    = Column(Integer, default=0)
    created_at  = Column(DateTime, default=datetime.utcnow)
