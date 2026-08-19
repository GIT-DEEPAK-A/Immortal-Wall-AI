# backend/routes/status_routes.py
"""
System status and raw-event ingest routes.

All shared singletons come from backend.container — no local instantiation.
"""

from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from backend.container import db, response_engine, threat_engine
from backend.core.security import get_current_user
from backend.schemas import RawEventSchema

logger = logging.getLogger("backend.status_routes")
router = APIRouter()


@router.get("/system_status")
def system_status(
    _user: dict = Depends(get_current_user),
):
    """Return basic agent/ML/honeypot status flags. Requires bearer token."""
    return {
        "agent_active":    True,
        "ml_running":      True,
        "honeypot_active": True,
        "timestamp":       datetime.utcnow().isoformat() + "Z",
    }


@router.get("/blocked_ips")
def blocked_ips(
    _user: dict = Depends(get_current_user),
):
    """Return the in-memory blocked IP set. Requires bearer token."""
    return {"blocked_ips": list(response_engine.blocked_ips)}


@router.post("/event")
def receive_event(event: RawEventSchema):
    """
    Receive a raw event from the agent or honeypot and run it through
    the full threat pipeline.

    Public — no auth required so the honeypot forwarder can POST without
    a token.  Input is validated by RawEventSchema.
    """
    try:
        analysis = threat_engine.analyze_event(event.model_dump())
        # Store to DB so the dashboard picks it up
        db.store_threat_analysis(analysis)
        return {"analysis": analysis}
    except Exception as e:
        logger.error("Error in /status/event: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
