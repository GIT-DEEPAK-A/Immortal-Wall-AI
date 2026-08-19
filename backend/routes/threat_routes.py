# backend/routes/threat_routes.py
"""
Threat listing and per-event analysis routes.

All shared singletons come from backend.container — no local instantiation.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from backend.container import db, threat_engine
from backend.core.security import get_current_user

logger = logging.getLogger("backend.threat_routes")
router = APIRouter()


@router.get("")
def list_threats(
    limit:    int  = 50,
    offset:   int  = 0,
    severity: str  = None,
    _user:    dict = Depends(get_current_user),
):
    """Return paginated list of stored threat records. Requires bearer token."""
    try:
        threats = db.get_threats(limit=limit, offset=offset, severity=severity)
        total   = db.get_threat_count(severity=severity)
        return {"threats": threats, "total": total, "limit": limit, "offset": offset}
    except Exception as e:
        logger.error("Error listing threats: %s", e)
        return {"threats": [], "total": 0, "limit": limit, "offset": offset}


@router.post("/analyze")
def analyze_event(
    event: dict,
    _user: dict = Depends(get_current_user),
):
    """Analyze a single event through the full threat pipeline. Requires bearer token."""
    try:
        result = threat_engine.analyze_event(event)
        return {"result": result}
    except Exception as e:
        logger.error("Error analyzing event: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
