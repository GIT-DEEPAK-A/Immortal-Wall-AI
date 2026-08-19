# honeypot/routes/dashboard.py
"""
Honeypot attacker-lure routes.

Every request is logged via log_honeypot_event() so the main dashboard
threat feed captures all attacker probes.
"""

import io
from flask import Blueprint, Response, jsonify, render_template, request
from honeypot.logger import log_honeypot_event

dashboard_bp = Blueprint("dashboard_bp", __name__)


def _capture(route: str, extra: dict = None) -> None:
    """Log an attacker interaction with request metadata."""
    event = {
        "route":      route,
        "ip":         request.remote_addr,
        "method":     request.method,
        "user_agent": request.headers.get("User-Agent", "unknown"),
        "args":       dict(request.args),
    }
    if extra:
        event.update(extra)
    log_honeypot_event(event)


# ── /admin ─────────────────────────────────────────────────────────────────

@dashboard_bp.route("/admin")
def admin_dashboard():
    """Fake admin dashboard — attacker thinks they got in."""
    _capture("/admin")
    return render_template("admin.html")


# ── /phpmyadmin ────────────────────────────────────────────────────────────

@dashboard_bp.route("/phpmyadmin")
@dashboard_bp.route("/phpMyAdmin")
@dashboard_bp.route("/pma")
def phpmyadmin():
    """Fake phpMyAdmin interface."""
    _capture("/phpmyadmin")
    return render_template("phpmyadmin.html")


# ── /api/v1/users ─────────────────────────────────────────────────────────

@dashboard_bp.route("/api/v1/users")
def fake_users_api():
    """Return a convincing but entirely fake JSON user list."""
    _capture("/api/v1/users")
    users = [
        {"id": 1,  "username": "admin",      "email": "admin@nexuscorp.internal",  "role": "superadmin", "password_hash": "$2b$12$abc123fakehashabcdef"},
        {"id": 2,  "username": "j.morrison", "email": "j.morrison@nexuscorp.com",  "role": "admin",      "password_hash": "$2b$12$def456fakehashabcdef"},
        {"id": 3,  "username": "s.patel",    "email": "s.patel@nexuscorp.com",     "role": "dba",        "password_hash": "$2b$12$ghi789fakehashabcdef"},
        {"id": 4,  "username": "l.chen",     "email": "l.chen@nexuscorp.com",      "role": "analyst",    "password_hash": "$2b$12$jkl012fakehashabcdef"},
        {"id": 5,  "username": "api_service","email": "svc@nexuscorp.internal",    "role": "service",    "password_hash": "$2b$12$mno345fakehashabcdef"},
    ]
    return jsonify({"users": users, "total": len(users), "page": 1})


# ── /backup.zip ────────────────────────────────────────────────────────────

@dashboard_bp.route("/backup.zip")
@dashboard_bp.route("/backup.tar.gz")
@dashboard_bp.route("/db_backup.sql")
def fake_backup():
    """Return 200 with a tiny decoy text file — captures the download attempt."""
    _capture("/backup.zip")
    content = (
        b"NEXUS CORPORATE BACKUP v3.4.1\n"
        b"Generated: 2024-11-15 02:00:00 UTC\n"
        b"[Encrypted payload — contact security@nexuscorp.com for decryption key]\n"
        b"\x00" * 512   # zero padding to look like a real archive
    )
    return Response(
        content,
        status=200,
        mimetype="application/zip",
        headers={"Content-Disposition": "attachment; filename=backup.zip"},
    )


# ── /.env ─────────────────────────────────────────────────────────────────

@dashboard_bp.route("/.env")
def fake_env():
    """Return a convincing but fake .env file."""
    _capture("/.env")
    fake = (
        "APP_ENV=production\n"
        "APP_KEY=base64:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=\n"
        "DB_HOST=10.0.1.20\n"
        "DB_DATABASE=nexus_prod\n"
        "DB_USERNAME=nexus_app\n"
        "DB_PASSWORD=Ch@ng3M3_N0tR3al!\n"
        "REDIS_HOST=10.0.1.40\n"
        "MAIL_HOST=smtp.nexuscorp.internal\n"
        "AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE\n"
        "AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY\n"
    )
    return Response(fake, status=200, mimetype="text/plain")


# ── /wp-admin ─────────────────────────────────────────────────────────────

@dashboard_bp.route("/wp-admin")
@dashboard_bp.route("/wp-login.php")
def fake_wp_admin():
    """Fake WordPress admin redirect — just logs the probe."""
    _capture("/wp-admin")
    html = (
        "<html><head><title>WordPress Login</title></head>"
        "<body style='background:#f0f0f1;font-family:Arial'>"
        "<div style='width:320px;margin:80px auto;background:#fff;padding:26px;border:1px solid #ccc'>"
        "<h2 style='color:#3c3c3c;text-align:center'>WordPress</h2>"
        "<form method='POST'>"
        "<label>Username</label><br>"
        "<input name='log' type='text' style='width:100%;margin:4px 0 12px'><br>"
        "<label>Password</label><br>"
        "<input name='pwd' type='password' style='width:100%;margin:4px 0 16px'><br>"
        "<input type='submit' value='Log In' style='background:#0073aa;color:#fff;border:none;padding:8px 14px;cursor:pointer'>"
        "</form></div></body></html>"
    )
    return Response(html, status=200, mimetype="text/html")
