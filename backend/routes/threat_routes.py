from fastapi import APIRouter
from backend.services.threat_engine import ThreatEngine
from backend.database.db import DatabaseManager

router = APIRouter()
engine = ThreatEngine()
_db = DatabaseManager()


@router.get("")
def list_threats(limit: int = 50, offset: int = 0, severity: str = None):
    """Return paginated list of stored threat records."""
    try:
        threats = _db.get_threats(limit=limit, offset=offset, severity=severity)
        total = _db.get_threat_count(severity=severity)
        return {"threats": threats, "total": total, "limit": limit, "offset": offset}
    except Exception as e:
        print(f"[Threat Routes] Error listing threats: {e}")
        return {"threats": [], "total": 0, "limit": limit, "offset": offset}


@router.post("/analyze")
def analyze_event(event: dict):
    try:
        result = engine.analyze_event(event)
        return {"result": result}
    except Exception as e:
        print(f"[Threat Routes] Error analyzing event: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}
