# honeypot/routes/dashboard.py

from flask import Blueprint, render_template

dashboard_bp = Blueprint("dashboard_bp", __name__)

@dashboard_bp.route("/dashboard")
def dashboard():
    """
    Fake admin dashboard to lure attackers.
    """
    fake_data = {
        "users": ["admin", "guest", "test"],
        "files": ["secret.txt", "backup.db", "config.yaml"],
        "settings": ["network", "firewall", "system"]
    }
    return render_template("dashboard.html", data=fake_data)