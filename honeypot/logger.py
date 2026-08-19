# honeypot/logger.py
"""
Honeypot event logger.

Writes every captured interaction to logs/honeypot.log, then forwards it
to the main backend at http://localhost:8000/api/status/event so the
attacker activity appears in the dashboard threat feed.
"""

from __future__ import annotations

import json
import os
from datetime import datetime

BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_PATH  = os.path.join(BASE_DIR, "logs", "honeypot.log")

# Backend event ingest endpoint (no auth required — public POST)
_BACKEND_EVENT_URL = "http://localhost:8000/api/status/event"


def log_honeypot_event(event: dict) -> None:
    """
    Log a honeypot interaction.

    1. Stamps the event with the current ISO timestamp.
    2. Appends a JSON line to logs/honeypot.log.
    3. Forwards the event to the backend /api/status/event so it appears
       in the main dashboard threat feed.  Forward failures are silenced
       so a dead backend never crashes the honeypot.
    """
    event = dict(event)   # make a copy — do not mutate caller's dict
    event["timestamp"] = datetime.utcnow().isoformat() + "Z"
    event.setdefault("source", "honeypot")

    # ── 1. Local log ───────────────────────────────────────────────────────
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(event) + "\n")
    except Exception as exc:
        print(f"[Honeypot Logger] Failed to write to file: {exc}")

    print(f"[Honeypot] Captured: {event.get('route', '?')} from {event.get('ip', '?')}")

    # ── 2. Forward to backend ──────────────────────────────────────────────
    try:
        import urllib.request
        payload  = json.dumps(event).encode("utf-8")
        req      = urllib.request.Request(
            _BACKEND_EVENT_URL,
            data    = payload,
            method  = "POST",
            headers = {"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=2)
    except Exception:
        # Backend may not be running — silently drop the forward
        pass
