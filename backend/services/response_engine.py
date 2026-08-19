# backend/services/response_engine.py

import os
import json
import time
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BLOCKLIST_PATH = os.path.join(BASE_DIR, "data", "blocked_ips.json")
WHITELIST_PATH = os.path.join(BASE_DIR, "data", "whitelisted_ips.json")

# Ensure data directory and files exist
os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
for _path in [BLOCKLIST_PATH, WHITELIST_PATH]:
    if not os.path.exists(_path):
        with open(_path, "w") as _f:
            json.dump([], _f)


def load_ips(path: str) -> list:
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def save_ips(path: str, ip_list: list) -> None:
    with open(path, "w") as f:
        json.dump(ip_list, f, indent=2)


class ResponseEngine:
    def __init__(self):
        self.blocked_ips = set(load_ips(BLOCKLIST_PATH))
        self.whitelisted_ips = set(load_ips(WHITELIST_PATH))

    # ------------------------------------------------------------------
    # Core blocking methods
    # ------------------------------------------------------------------

    def block_ip(self, ip: str, hard: bool = True) -> str:
        """Block an IP address. hard=True → fully block; hard=False → soft block."""
        if ip in self.whitelisted_ips:
            return f"IP {ip} is whitelisted, not blocking."

        if hard:
            if ip not in self.blocked_ips:
                self.blocked_ips.add(ip)
                save_ips(BLOCKLIST_PATH, list(self.blocked_ips))
            action = "HARD BLOCK"
        else:
            action = self.apply_soft_block(ip)

        print(f"[ResponseEngine] {action} applied to {ip}")
        return action

    def apply_soft_block(self, ip: str, duration: int = 5) -> str:
        """Apply a soft block to slow down a suspicious IP."""
        if ip in self.whitelisted_ips:
            return f"IP {ip} is whitelisted, cannot apply soft block."
        # In production this integrates with firewall/rate-limiter.
        # Here we just record the action without actually sleeping the server.
        print(f"[ResponseEngine] SOFT BLOCK applied to {ip} for {duration}s")
        return f"SOFT BLOCK ({duration}s)"

    def unblock_ip(self, ip: str) -> bool:
        if ip in self.blocked_ips:
            self.blocked_ips.remove(ip)
            save_ips(BLOCKLIST_PATH, list(self.blocked_ips))
            print(f"[ResponseEngine] IP {ip} unblocked")
            return True
        return False

    # ------------------------------------------------------------------
    # Whitelist management
    # ------------------------------------------------------------------

    def add_to_whitelist(self, ip: str) -> bool:
        if ip not in self.whitelisted_ips:
            self.whitelisted_ips.add(ip)
            save_ips(WHITELIST_PATH, list(self.whitelisted_ips))
            print(f"[ResponseEngine] IP {ip} added to whitelist")
            return True
        return False

    def remove_from_whitelist(self, ip: str) -> bool:
        if ip in self.whitelisted_ips:
            self.whitelisted_ips.remove(ip)
            save_ips(WHITELIST_PATH, list(self.whitelisted_ips))
            print(f"[ResponseEngine] IP {ip} removed from whitelist")
            return True
        return False

    # ------------------------------------------------------------------
    # Status helpers
    # ------------------------------------------------------------------

    def is_blocked(self, ip: str) -> bool:
        return ip in self.blocked_ips

    def is_whitelisted(self, ip: str) -> bool:
        return ip in self.whitelisted_ips

    # ------------------------------------------------------------------
    # Alerting
    # ------------------------------------------------------------------

    def send_alert(self, ip: str, threat_level: str, reason: str) -> dict:
        """Write an alert entry to alerts.log and return it."""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "ip": ip,
            "threat_level": threat_level,
            "reason": reason,
        }
        alert_path = os.path.join(BASE_DIR, "logs", "alerts.log")
        os.makedirs(os.path.dirname(alert_path), exist_ok=True)
        with open(alert_path, "a") as f:
            f.write(json.dumps(alert) + "\n")
        print(f"[ALERT] Threat detected: {alert}")
        return alert

    # ------------------------------------------------------------------
    # Unified response executor (called by app.py /api/response endpoint)
    # ------------------------------------------------------------------

    def execute_response(self, response_config: dict) -> dict:
        """
        Execute a response action based on the provided configuration.

        Expected keys in response_config:
            type        : str  — one of "block_ip", "rate_limit", "alert", "isolate"
            ip          : str  — target IP address
            threat_id   : str  — optional threat identifier
            threat_level: str  — optional severity label
            reason      : str  — optional human-readable reason
            hard        : bool — for block_ip; whether to hard-block (default True)
        """
        response_type = response_config.get("type", "alert")
        ip = response_config.get("ip", "unknown")
        threat_level = response_config.get("threat_level", "unknown")
        reason = response_config.get("reason", "Automated response")
        threat_id = response_config.get("threat_id", "N/A")

        result: dict = {
            "type": response_type,
            "ip": ip,
            "threat_id": threat_id,
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "details": "",
        }

        try:
            if response_type == "block_ip":
                hard = response_config.get("hard", True)
                action = self.block_ip(ip, hard=hard)
                result["success"] = True
                result["details"] = action

            elif response_type == "rate_limit":
                action = self.apply_soft_block(ip, duration=response_config.get("duration", 10))
                result["success"] = True
                result["details"] = action

            elif response_type == "alert":
                alert = self.send_alert(ip, threat_level, reason)
                result["success"] = True
                result["details"] = f"Alert logged: {alert}"

            elif response_type == "isolate":
                # Hard-block + alert for full isolation
                block_action = self.block_ip(ip, hard=True)
                alert = self.send_alert(ip, threat_level, f"[ISOLATE] {reason}")
                result["success"] = True
                result["details"] = f"{block_action}; alert logged"

            else:
                result["details"] = f"Unknown response type: {response_type}"

        except Exception as e:
            result["details"] = f"Error executing response: {e}"
            print(f"[ResponseEngine] Error in execute_response: {e}")

        return result
