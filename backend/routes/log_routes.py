from fastapi import APIRouter
import os
import json
from backend.config import EVENTS_LOG, ALERTS_LOG
from backend.database.db import DatabaseManager
from backend.services.response_engine import ResponseEngine

router = APIRouter()
response_engine = ResponseEngine()
_db = DatabaseManager()


@router.get("")
def list_logs(limit: int = 100, level: str = None, component: str = None):
    """Return stored log entries from the database."""
    try:
        logs = _db.get_logs(limit=limit, level=level, component=component)
        return {"logs": logs, "total": len(logs)}
    except Exception as e:
        print(f"[Log Routes] Error listing logs: {e}")
        return {"logs": [], "total": 0}


@router.get("/events")
def get_events(limit: int = 50):
    result = []
    if os.path.exists(EVENTS_LOG):
        try:
            with open(EVENTS_LOG, "r") as f:
                lines = f.readlines()
                for line in lines[-limit:]:
                    try:
                        result.append(json.loads(line.strip()))
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"[Log Routes] Error reading events: {e}")
    return {"events": result}


@router.get("/alerts")
def get_alerts(limit: int = 50):
    alerts = []
    if os.path.exists(ALERTS_LOG):
        try:
            with open(ALERTS_LOG, "r") as f:
                lines = f.readlines()
                for line in lines[-limit:]:
                    try:
                        alerts.append(json.loads(line.strip()))
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"[Log Routes] Error reading alerts: {e}")
    return {"alerts": alerts}


@router.get("/blocked_ips")
def get_blocked_ips():
    return {"blocked_ips": list(response_engine.blocked_ips)}


@router.get("/whitelist")
def get_whitelist():
    return {"whitelist": list(response_engine.whitelisted_ips)}
