from fastapi import APIRouter
import os
import json
from datetime import datetime
from backend.services.response_engine import ResponseEngine
from backend.services.threat_engine import ThreatEngine

router = APIRouter()
response_engine = ResponseEngine()
threat_engine = ThreatEngine()

LOGS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs", "events.log")
ALERTS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs", "alerts.log")

# Get system status
@router.get("/system_status")
def system_status():
    status = {
        "agent_active": True,   # In production, check actual agent process
        "ml_running": True,     # Example flag
        "honeypot_active": True
    }
    return status

# Get latest threat alerts
@router.get("/threats")
def get_threats(limit: int = 50):
    alerts = []
    if os.path.exists(ALERTS_PATH):
        with open(ALERTS_PATH, "r") as f:
            lines = f.readlines()
            for line in lines[-limit:]:
                alerts.append(json.loads(line.strip()))
    return {"alerts": alerts}

# Get recent events/logs
@router.get("/logs")
def get_logs(limit: int = 50):
    logs = []
    if os.path.exists(LOGS_PATH):
        with open(LOGS_PATH, "r") as f:
            lines = f.readlines()
            for line in lines[-limit:]:
                logs.append(json.loads(line.strip()))
    return {"logs": logs}

# Get blocked IPs
@router.get("/blocked_ips")
def blocked_ips():
    return {"blocked_ips": list(response_engine.blocked_ips)}

# Receive event from agent
@router.post("/event")
def receive_event(event: dict):
    try:
        # Analyze the event
        analysis = threat_engine.analyze_event(event)
        # Log the event
        with open(LOGS_PATH, "a") as f:
            f.write(json.dumps(event) + "\n")
        return {"analysis": analysis}
    except Exception as e:
        print(f"Error in event: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}