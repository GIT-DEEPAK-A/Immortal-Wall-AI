from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Text, Boolean, JSON, func, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import hashlib
import uuid
import json
import os
from pathlib import Path

Base = declarative_base()

class Threat(Base):
    __tablename__ = "threats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    ip_address = Column(String(45), index=True)
    threat_level = Column(String(20), index=True)  # normal, suspicious, malicious
    threat_score = Column(Float, default=0.0)
    confidence = Column(Float, default=0.0)
    threat_type = Column(String(50), index=True)
    description = Column(Text)
    user_agent = Column(Text)
    request_data = Column(JSON)
    ml_prediction = Column(JSON)  # Store ML engine results
    rule_matches = Column(JSON)  # Store rule engine results
    response_actions = Column(JSON)  # Store response engine actions
    blocked = Column(Boolean, default=False)
    source = Column(String(50), default="unknown")  # honeypot, network, api

class LogEntry(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    level = Column(String(10), index=True)  # INFO, WARNING, ERROR, CRITICAL
    component = Column(String(50), index=True)  # monitor, collector, ml_engine, etc.
    message = Column(Text)
    log_metadata = Column(JSON)

class AnalyticsCache(Base):
    __tablename__ = "analytics_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cache_key = Column(String(100), unique=True, index=True)
    data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)

class SystemMetrics(Base):
    __tablename__ = "system_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    metric_name = Column(String(100), index=True)
    metric_value = Column(Float)
    metric_metadata = Column(JSON)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    salt = Column(String(64), nullable=False)
    role = Column(String(20), default="Analyst")
    created_at = Column(DateTime, default=datetime.utcnow)

class OTPEntry(Base):
    __tablename__ = "otps"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), index=True, nullable=False)
    otp_hash = Column(String(128), nullable=False)
    expiry_time = Column(DateTime, nullable=False)
    attempts = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class DatabaseManager:
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Default to project root
            project_root = Path(__file__).parent.parent.parent
            db_path = project_root / "data" / "immortal_wall.db"

        # Handle in-memory database for testing
        if db_path == ":memory:":
            self.db_url = "sqlite:///:memory:"
        else:
            db_path = Path(db_path)
            db_path.parent.mkdir(exist_ok=True)
            self.db_url = f"sqlite:///{db_path}"

        self.engine = create_engine(self.db_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        # Create tables
        Base.metadata.create_all(bind=self.engine)
        self._seed_default_users()

    def _seed_default_users(self) -> None:
        """Create demo users if they do not already exist."""
        default_users = [
            {"email": "deepakananthan4@gmail.com", "password": "password", "role": "Admin"},
            {"email": "analyst@immortalwall.ai", "password": "password", "role": "Analyst"}
        ]
        for user in default_users:
            existing = self.get_user_by_email(user["email"])
            if not existing:
                self.create_user(user["email"], user["password"], user["role"])

    def get_session(self) -> Session:
        return self.SessionLocal()

    def health_check(self) -> Dict[str, Any]:
        """Check database health"""
        try:
            with self.get_session() as session:
                # Simple query to test connection
                session.execute(text("SELECT 1")).scalar()
                return {
                    "status": "healthy",
                    "connection": "ok",
                    "tables": len(Base.metadata.tables)
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "connection": "failed",
                "error": str(e)
            }

    def store_threat_analysis(self, threat_data: Dict[str, Any]) -> bool:
        """Store threat analysis result"""
        try:
            with self.get_session() as session:
                threat = Threat(
                    timestamp=datetime.fromtimestamp(threat_data.get("timestamp", datetime.utcnow().timestamp())),
                    ip_address=threat_data.get("ip_address", threat_data.get("ip", "unknown")),
                    threat_level=threat_data.get("threat_level", "unknown"),
                    threat_score=threat_data.get("threat_score", 0.0),
                    confidence=threat_data.get("confidence", 0.0),
                    threat_type=threat_data.get("threat_type", "unknown"),
                    description=threat_data.get("description", ""),
                    user_agent=threat_data.get("user_agent", ""),
                    request_data=threat_data.get("request_data", {}),
                    ml_prediction=threat_data.get("ml_result", {}),
                    rule_matches=threat_data.get("rule_matches", []),
                    response_actions=threat_data.get("response_actions", []),
                    blocked=threat_data.get("blocked", False),
                    source=threat_data.get("source", "unknown")
                )
                session.add(threat)
                session.commit()
                return True
        except Exception as e:
            print(f"[Database] Error storing threat: {e}")
            return False

    def get_threats(self, limit: int = 50, offset: int = 0, severity: str = None) -> List[Dict[str, Any]]:
        """Get threats with pagination and filtering"""
        try:
            with self.get_session() as session:
                query = session.query(Threat).order_by(Threat.timestamp.desc())

                if severity:
                    query = query.filter(Threat.threat_level == severity)

                threats = query.offset(offset).limit(limit).all()

                return [{
                    "id": t.id,
                    "timestamp": t.timestamp.isoformat(),
                    "ip_address": t.ip_address,
                    "threat_level": t.threat_level,
                    "threat_score": t.threat_score,
                    "confidence": t.confidence,
                    "threat_type": t.threat_type,
                    "description": t.description,
                    "user_agent": t.user_agent,
                    "blocked": t.blocked,
                    "source": t.source
                } for t in threats]
        except Exception as e:
            print(f"[Database] Error getting threats: {e}")
            return []

    def get_threat_count(self, severity: str = None) -> int:
        """Get total threat count"""
        try:
            with self.get_session() as session:
                query = session.query(func.count(Threat.id))
                if severity:
                    query = query.filter(Threat.threat_level == severity)
                return query.scalar() or 0
        except Exception as e:
            print(f"[Database] Error getting threat count: {e}")
            return 0

    def get_recent_threats(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most recent threats"""
        return self.get_threats(limit=limit, offset=0)

    def get_threat_statistics(self) -> Dict[str, Any]:
        """Get comprehensive threat statistics"""
        try:
            with self.get_session() as session:
                # Total threats
                total_threats = session.query(func.count(Threat.id)).scalar() or 0

                # Threats by level
                threat_levels = session.query(
                    Threat.threat_level,
                    func.count(Threat.id)
                ).group_by(Threat.threat_level).all()

                levels_dict = {level: count for level, count in threat_levels}

                # Threats by type
                threat_types = session.query(
                    Threat.threat_type,
                    func.count(Threat.id)
                ).group_by(Threat.threat_type).all()

                types_dict = {t_type: count for t_type, count in threat_types}

                # Recent activity (last 24 hours)
                yesterday = datetime.utcnow() - timedelta(hours=24)
                recent_threats = session.query(func.count(Threat.id)).filter(
                    Threat.timestamp >= yesterday
                ).scalar() or 0

                # Blocked threats
                blocked_threats = session.query(func.count(Threat.id)).filter(
                    Threat.blocked == True
                ).scalar() or 0

                # Average threat score
                avg_score = session.query(func.avg(Threat.threat_score)).scalar() or 0.0

                return {
                    "total_threats": total_threats,
                    "threat_levels": levels_dict,
                    "threat_types": types_dict,
                    "recent_threats_24h": recent_threats,
                    "blocked_threats": blocked_threats,
                    "average_threat_score": float(avg_score),
                    "ml_predictions": total_threats  # Assuming all threats have ML analysis
                }
        except Exception as e:
            print(f"[Database] Error getting threat statistics: {e}")
            return {
                "total_threats": 0,
                "threat_levels": {},
                "threat_types": {},
                "recent_threats_24h": 0,
                "blocked_threats": 0,
                "average_threat_score": 0.0,
                "ml_predictions": 0
            }

    def get_analytics(self, start_time: datetime = None) -> Dict[str, Any]:
        """Get analytics data for dashboard"""
        try:
            with self.get_session() as session:
                if start_time is None:
                    start_time = datetime.utcnow() - timedelta(hours=24)

                # Threat trends over time (hourly)
                hourly_threats = session.query(
                    func.strftime('%Y-%m-%d %H:00:00', Threat.timestamp).label('hour'),
                    func.count(Threat.id).label('count')
                ).filter(
                    Threat.timestamp >= start_time
                ).group_by(
                    func.strftime('%Y-%m-%d %H:00:00', Threat.timestamp)
                ).order_by('hour').all()

                threat_trends = [{"hour": h, "count": c} for h, c in hourly_threats]

                # Top threat sources
                top_sources = session.query(
                    Threat.ip_address,
                    func.count(Threat.id).label('count')
                ).filter(
                    Threat.timestamp >= start_time
                ).group_by(Threat.ip_address).order_by(
                    func.count(Threat.id).desc()
                ).limit(10).all()

                top_ips = [{"ip": ip, "count": count} for ip, count in top_sources]

                # Threat level distribution
                level_dist = session.query(
                    Threat.threat_level,
                    func.count(Threat.id)
                ).filter(
                    Threat.timestamp >= start_time
                ).group_by(Threat.threat_level).all()

                threat_distribution = {level: count for level, count in level_dist}

                # Response effectiveness
                response_stats = session.query(
                    func.json_extract(Threat.response_actions, '$[0].type'),
                    func.count(Threat.id)
                ).filter(
                    Threat.timestamp >= start_time,
                    Threat.response_actions.isnot(None)
                ).group_by(
                    func.json_extract(Threat.response_actions, '$[0].type')
                ).all()

                response_effectiveness = {action: count for action, count in response_stats if action}

                return {
                    "threat_trends": threat_trends,
                    "top_threat_sources": top_ips,
                    "threat_distribution": threat_distribution,
                    "response_effectiveness": response_effectiveness,
                    "time_range": {
                        "start": start_time.isoformat(),
                        "end": datetime.utcnow().isoformat()
                    }
                }
        except Exception as e:
            print(f"[Database] Error getting analytics: {e}")
            return {
                "threat_trends": [],
                "top_threat_sources": [],
                "threat_distribution": {},
                "response_effectiveness": {},
                "time_range": {
                    "start": start_time.isoformat() if start_time else datetime.utcnow().isoformat(),
                    "end": datetime.utcnow().isoformat()
                }
            }

    def get_threats_per_minute(self) -> float:
        """Get current threats per minute rate"""
        try:
            with self.get_session() as session:
                # Last 10 minutes of data
                ten_minutes_ago = datetime.utcnow() - timedelta(minutes=10)
                recent_count = session.query(func.count(Threat.id)).filter(
                    Threat.timestamp >= ten_minutes_ago
                ).scalar() or 0

                # Calculate rate
                return recent_count / 10.0
        except Exception as e:
            print(f"[Database] Error calculating threats per minute: {e}")
            return 0.0

    def store_log_entry(self, level: str, component: str, message: str, metadata: Dict = None) -> bool:
        """Store log entry"""
        try:
            with self.get_session() as session:
                log_entry = LogEntry(
                    level=level.upper(),
                    component=component,
                    message=message,
                    log_metadata=metadata or {}
                )
                session.add(log_entry)
                session.commit()
                return True
        except Exception as e:
            print(f"[Database] Error storing log: {e}")
            return False

    def get_logs(self, limit: int = 100, level: str = None, component: str = None) -> List[Dict[str, Any]]:
        """Get log entries"""
        try:
            with self.get_session() as session:
                query = session.query(LogEntry).order_by(LogEntry.timestamp.desc())

                if level:
                    query = query.filter(LogEntry.level == level.upper())
                if component:
                    query = query.filter(LogEntry.component == component)

                logs = query.limit(limit).all()

                return [{
                    "id": log.id,
                    "timestamp": log.timestamp.isoformat(),
                    "level": log.level,
                    "component": log.component,
                    "message": log.message,
                    "metadata": log.log_metadata
                } for log in logs]
        except Exception as e:
            print(f"[Database] Error getting logs: {e}")
            return []

    def store_system_metric(self, metric_name: str, value: float, metadata: Dict = None) -> bool:
        """Store system metric"""
        try:
            with self.get_session() as session:
                metric = SystemMetrics(
                    metric_name=metric_name,
                    metric_value=value,
                    metric_metadata=metadata or {}
                )
                session.add(metric)
                session.commit()
                return True
        except Exception as e:
            print(f"[Database] Error storing metric: {e}")
            return False

    def get_system_metrics(self, metric_name: str = None, hours: int = 24) -> List[Dict[str, Any]]:
        """Get system metrics"""
        try:
            with self.get_session() as session:
                query = session.query(SystemMetrics).filter(
                    SystemMetrics.timestamp >= datetime.utcnow() - timedelta(hours=hours)
                ).order_by(SystemMetrics.timestamp.desc())

                if metric_name:
                    query = query.filter(SystemMetrics.metric_name == metric_name)

                metrics = query.limit(1000).all()

                return [{
                    "id": m.id,
                    "timestamp": m.timestamp.isoformat(),
                    "metric_name": m.metric_name,
                    "value": m.metric_value,
                    "metadata": m.metric_metadata
                } for m in metrics]
        except Exception as e:
            print(f"[Database] Error getting metrics: {e}")
            return []

    def _hash_password(self, password: str, salt: str) -> str:
        return hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            100000
        ).hex()

    def create_user(self, email: str, password: str, role: str = "Analyst") -> bool:
        try:
            with self.get_session() as session:
                existing = session.query(User).filter(User.email == email).first()
                if existing:
                    return False

                salt = uuid.uuid4().hex
                password_hash = self._hash_password(password, salt)

                user = User(
                    email=email.lower(),
                    password_hash=password_hash,
                    salt=salt,
                    role=role
                )
                session.add(user)
                session.commit()
                return True
        except Exception as e:
            print(f"[Database] Error creating user: {e}")
            return False

    def get_user_by_email(self, email: str) -> Optional[User]:
        try:
            with self.get_session() as session:
                return session.query(User).filter(User.email == email.lower()).first()
        except Exception as e:
            print(f"[Database] Error fetching user: {e}")
            return None

    def verify_user_password(self, email: str, password: str) -> bool:
        try:
            user = self.get_user_by_email(email)
            if not user:
                return False

            password_hash = self._hash_password(password, user.salt)
            return password_hash == user.password_hash
        except Exception as e:
            print(f"[Database] Error verifying password: {e}")
            return False

    def invalidate_otp(self, email: str) -> None:
        try:
            with self.get_session() as session:
                session.query(OTPEntry).filter(OTPEntry.email == email.lower()).delete()
                session.commit()
        except Exception as e:
            print(f"[Database] Error invalidating OTP: {e}")

    def create_otp_entry(self, email: str, otp: str, expiry_minutes: int = 2) -> bool:
        try:
            with self.get_session() as session:
                self.invalidate_otp(email)
                otp_hash = hashlib.sha256(otp.encode("utf-8")).hexdigest()
                expiry_time = datetime.utcnow() + timedelta(minutes=expiry_minutes)
                otp_entry = OTPEntry(
                    email=email.lower(),
                    otp_hash=otp_hash,
                    expiry_time=expiry_time,
                    attempts=0
                )
                session.add(otp_entry)
                session.commit()
                return True
        except Exception as e:
            print(f"[Database] Error creating OTP entry: {e}")
            return False

    def get_active_otp(self, email: str) -> Optional[OTPEntry]:
        try:
            with self.get_session() as session:
                otp_entry = session.query(OTPEntry).filter(OTPEntry.email == email.lower()).first()
                if not otp_entry:
                    return None
                if otp_entry.expiry_time < datetime.utcnow() or otp_entry.attempts >= 3:
                    session.delete(otp_entry)
                    session.commit()
                    return None
                return otp_entry
        except Exception as e:
            print(f"[Database] Error fetching OTP entry: {e}")
            return None

    def increment_otp_attempts(self, email: str) -> None:
        try:
            with self.get_session() as session:
                otp_entry = session.query(OTPEntry).filter(OTPEntry.email == email.lower()).first()
                if otp_entry:
                    otp_entry.attempts += 1
                    session.commit()
        except Exception as e:
            print(f"[Database] Error incrementing OTP attempts: {e}")
