# backend/routes/log_routes.py
"""
Log and blocked-IP routes.

All shared singletons come from backend.container — no local instantiation.
File-based log reading is kept for the /events and /alerts routes that
tail the agent's event log.  All other reads go to the database.
"""

from __future__ import annotations

import json
import logging
import os

from fastapi import APIRouter, Depends

from backend.config import EVENTS_LOG, ALERTS_LOG
from backend.container import db, response_engine
from backend.core.security import get_current_user

logger = logging.getLogger("backend.log_routes")
router = APIRouter()


@router.get("")
def list_logs(
    limit:     int  = 100,
    level:     str  = None,
    component: str  = None,
    _user:     dict = Depends(get_current_user),
):
    """Return stored log entries from the database. Requires bearer token."""
    try:
        logs = db.get_logs(limit=limit, level=level, component=component)
        return {"logs": logs, "total": len(logs)}
    except Exception as e:
        logger.error("Error listing logs: %s", e)
        return {"logs": [], "total": 0}


@router.get("/events")
def get_events(
    limit: int  = 50,
    _user: dict = Depends(get_current_user),
):
    """Return raw events from the agent events log file. Requires bearer token."""
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
            logger.error("Error reading events log: %s", e)
    return {"events": result}


@router.get("/alerts")
def get_alerts(
    limit: int  = 50,
    _user: dict = Depends(get_current_user),
):
    """Return alerts from the alerts log file. Requires bearer token."""
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
            logger.error("Error reading alerts log: %s", e)
    return {"alerts": alerts}


@router.get("/blocked")
def get_blocked_ips_from_db(
    limit:  int  = 100,
    offset: int  = 0,
    _user:  dict = Depends(get_current_user),
):
    """
    Return paginated list of blocked IPs from the BlockedIP table.
    Fields: ip, blocked_at, reason, hard_block, unblocked_at.
    Requires bearer token.
    """
    try:
        records = db.get_blocked_ips(limit=limit, offset=offset)
        return {"blocked_ips": records, "total": len(records)}
    except Exception as e:
        logger.error("Error fetching blocked IPs: %s", e)
        return {"blocked_ips": [], "total": 0}


@router.get("/blocked_ips")
def get_blocked_ips_memory(
    _user: dict = Depends(get_current_user),
):
    """Return in-memory blocked IPs set (O(1) cache). Requires bearer token."""
    return {"blocked_ips": list(response_engine.blocked_ips)}


@router.get("/whitelist")
def get_whitelist(
    _user: dict = Depends(get_current_user),
):
    """Return in-memory whitelisted IPs set. Requires bearer token."""
    return {"whitelist": list(response_engine.whitelisted_ips)}
