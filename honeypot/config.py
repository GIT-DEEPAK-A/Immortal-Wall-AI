# honeypot/config.py
# Configuration for the Flask-based honeypot server.

import os

# ── Server settings ────────────────────────────────────────────────────────
HONEYPOT_HOST  = os.getenv("HONEYPOT_HOST", "0.0.0.0")
HONEYPOT_PORT  = int(os.getenv("HONEYPOT_PORT", "5001"))
HONEYPOT_DEBUG = os.getenv("HONEYPOT_DEBUG", "false").lower() == "true"

# Secret key used by Flask for session signing
SECRET_KEY = os.getenv("HONEYPOT_SECRET_KEY", "honeypot-secret-change-in-production")

# ── Decoy routes ───────────────────────────────────────────────────────────
# These are the fake endpoints that attract and trap attackers.
DECOY_ROUTES = {
    "login":    "/login",
    "admin":    "/admin",
    "database": "/phpMyAdmin",
    "api":      "/api/v1/users",
    "backup":   "/backup.zip",
}

# ── Logging ────────────────────────────────────────────────────────────────
BASE_DIR       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR        = os.path.join(BASE_DIR, "logs")
HONEYPOT_LOG   = os.path.join(LOG_DIR, "honeypot.log")

# ── Redirect after capture ─────────────────────────────────────────────────
# Where to redirect attackers after their credentials are captured.
REDIRECT_URL   = os.getenv("HONEYPOT_REDIRECT_URL", "http://localhost:5175")

# ── Backend reporting ──────────────────────────────────────────────────────
# Forward honeypot events to the main backend for ML analysis.
BACKEND_EVENT_URL = os.getenv("BACKEND_EVENT_URL", "http://127.0.0.1:8000/api/status/event")
REPORT_TO_BACKEND = os.getenv("HONEYPOT_REPORT_BACKEND", "true").lower() == "true"
