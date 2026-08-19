# honeypot/routes/login.py

from datetime import datetime
from flask import Blueprint, request, render_template, redirect
from honeypot.logger import log_honeypot_event

login_bp = Blueprint("login_bp", __name__)


@login_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "unknown")
        password = request.form.get("password", "unknown")
        ip = request.remote_addr

        # Fixed: request.date does not exist — use datetime.now().isoformat()
        log_honeypot_event({
            "username": username,
            "password": password,
            "ip": ip,
            "time": datetime.now().isoformat(),
        })

        # Redirect attacker to the real dashboard (deception)
        return redirect("http://localhost:5175")

    # GET → show fake login page
    return render_template("login.html")
