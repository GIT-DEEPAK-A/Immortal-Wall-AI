# agent/collector.py
"""
Collector — gathers system events and forwards them to the backend.

Operating modes
───────────────
  Real mode (default, SIMULATE=false):
    Reads actual failed-login counts, request rates, and IP activity from
    the OS / log files.  Falls back gracefully when sources are unavailable.

  Simulation mode (SIMULATE=true or IMMORTAL_WALL_SIMULATE=true):
    Generates synthetic traffic for demos and development.  Every synthetic
    event is tagged with ``"source": "simulation"`` so the dashboard and
    database can clearly distinguish fake data from real observations.

Set the environment variable to enable simulation:
    export IMMORTAL_WALL_SIMULATE=true
"""

from __future__ import annotations

import os
import random
import threading
import time
from typing import Optional

from .config import THRESHOLDS, LOG_PATH
from .sender import send_event
from utils.logger import log_event

# ── Mode switch ────────────────────────────────────────────────────────────
_SIMULATE: bool = os.getenv("IMMORTAL_WALL_SIMULATE", "false").lower() in ("true", "1", "yes")


class Collector:
    """
    Collects or generates system-activity events.

    Parameters
    ----------
    simulate : bool, optional
        Override the env-var mode switch.  Useful in tests.
    """

    def __init__(self, simulate: Optional[bool] = None) -> None:
        self.simulate       = _SIMULATE if simulate is None else simulate
        self.failed_logins: dict  = {}
        self.request_count: dict  = {}
        self.ip_activity:   dict  = {}
        self.running        = False
        self._thread: Optional[threading.Thread] = None

        mode = "SIMULATION" if self.simulate else "REAL"
        print(f"[Collector] Initialised in {mode} mode.")

    def start(self) -> None:
        if not self.running:
            self.running  = True
            self._thread  = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
            print("[Collector] Started")

    def stop(self) -> None:
        self.running = False
        if self._thread:
            self._thread.join(timeout=5)
        print("[Collector] Stopped")

    # ── Main loop ──────────────────────────────────────────────────────────

    def _run(self) -> None:
        while self.running:
            try:
                event = self.collect()
                send_event(event)
                time.sleep(2)
            except Exception as e:
                print(f"[Collector] Error in run loop: {e}")
                time.sleep(5)

    # ── Public collect API ─────────────────────────────────────────────────

    def collect(self) -> dict:
        """Return one structured event, tagged by source."""
        if self.simulate:
            return self._collect_simulated()
        return self._collect_real()

    # ── Real-data collection ───────────────────────────────────────────────

    def _collect_real(self) -> dict:
        """
        Collect actual system signals.

        Current signals read:
          - /var/log/auth.log  (Linux) for failed SSH logins
          - psutil (optional)  for per-process network activity

        Falls back to a minimal event dict if sources are unavailable.
        """
        event: dict = {
            "timestamp":  time.time(),
            "source":     "real",
            "event_type": "system_poll",
            "status":     "ok",
        }

        # ── Failed login count from auth.log ───────────────────────────────
        auth_log = "/var/log/auth.log"
        if os.path.exists(auth_log):
            try:
                with open(auth_log, "r", errors="ignore") as f:
                    lines = f.readlines()[-500:]   # last 500 lines only
                failed = sum(
                    1 for ln in lines
                    if "Failed password" in ln or "authentication failure" in ln
                )
                event["failed_logins"]  = failed
                event["event_type"]     = "login"
                event["status"]         = "failed" if failed > 0 else "ok"
            except PermissionError:
                pass   # no read permission — skip silently

        # ── Optional: psutil network stats ────────────────────────────────
        try:
            import psutil
            net = psutil.net_connections(kind="inet")
            established = [c for c in net if c.status == "ESTABLISHED"]
            event["distinct_paths"] = len(established)
            event["request_rate"]   = len(established) / 10.0
            if established:
                # Use the first remote IP as the event IP
                first = established[0]
                if first.raddr:
                    event["ip"] = first.raddr.ip
        except ImportError:
            pass   # psutil not installed — skip
        except Exception:
            pass

        threat_flags = self._compute_flags(event)
        event["threat_flags"] = threat_flags
        log_event(event, LOG_PATH)
        return event

    # ── Simulation mode ────────────────────────────────────────────────────

    def _collect_simulated(self) -> dict:
        """
        Generate a synthetic event for demos / development.

        Every simulated event is explicitly tagged ``source=simulation``
        so it can be filtered out in analytics, reporting, and tests.
        """
        event_types = ["login", "request", "file_access"]
        ip          = f"192.168.1.{random.randint(1, 255)}"
        event_type  = random.choice(event_types)

        event: dict = {
            "timestamp":  time.time(),
            "source":     "simulation",          # ← explicit label
            "ip":         ip,
            "username":   f"user{random.randint(1, 20)}",
            "event_type": event_type,
        }

        # 10 % login failure rate
        if event_type == "login" and random.random() < 0.1:
            self.failed_logins[ip] = self.failed_logins.get(ip, 0) + 1
            event["status"] = "failed"
        else:
            event["status"] = "success"

        self.request_count[ip] = self.request_count.get(ip, 0) + 1
        self.ip_activity[ip]   = self.ip_activity.get(ip, 0) + 1

        event["threat_flags"] = self._compute_flags(event)
        log_event(event, LOG_PATH)
        return event

    # ── Internal helpers ───────────────────────────────────────────────────

    def _compute_flags(self, event: dict) -> dict:
        ip = event.get("ip", "")
        return {
            "failed_login":           self.failed_logins.get(ip, 0)  > THRESHOLDS["failed_logins"],
            "high_request_rate":      self.request_count.get(ip, 0)  > THRESHOLDS["request_rate"],
            "suspicious_ip_activity": self.ip_activity.get(ip, 0)    > THRESHOLDS["suspicious_ip_activity"],
        }
