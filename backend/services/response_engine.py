"""
backend/services/response_engine.py
─────────────────────────────────────
Automated response engine for Immortal Wall AI.

Key design decisions
────────────────────
- blocked_ips      : persisted in the BlockedIP database table.
                     An in-memory set provides O(1) hot-path checks (is_blocked).
- whitelisted_ips  : static set in code; extend to a DB table if runtime
                     management is needed.
- send_alert()     : writes a CRITICAL LogEntry to the database.  No file I/O.
- _log_action()    : uses the structured application logger, not print().
- Dependency injection: DatabaseManager is passed in via __init__ so the
  application shares one DB instance and one blocked_ips cache.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Optional, Set

if TYPE_CHECKING:
    from backend.database.db import DatabaseManager

logger = logging.getLogger("backend.response_engine")

# Whitelist is intentionally kept static in code.
# Add IPs that must never be blocked (loopback, management, etc.).
_STATIC_WHITELIST: Set[str] = {
    "127.0.0.1",
    "::1",
    "10.0.0.1",
}


class ResponseEngine:
    """
    DB-backed response engine.

    Parameters
    ----------
    db_manager : DatabaseManager, optional
        Shared database manager.  If not provided, a new one is created
        (backwards-compatible behaviour for tests that instantiate directly).
    """

    def __init__(self, db_manager: Optional["DatabaseManager"] = None) -> None:
        if db_manager is None:
            # Lazy import to avoid circular dependency at module load time.
            from backend.database.db import DatabaseManager as _DM
            db_manager = _DM()

        self._db = db_manager
        self.whitelisted_ips: Set[str] = set(_STATIC_WHITELIST)
        # Load all currently-blocked IPs from DB into the in-memory set.
        self.blocked_ips: Set[str] = self._db.load_active_blocked_ips()
        logger.info(
            "ResponseEngine initialised — %d IPs pre-loaded from DB.",
            len(self.blocked_ips),
        )

    # ── Core blocking ──────────────────────────────────────────────────────

    def block_ip(self, ip: str, hard: bool = True, reason: Optional[str] = None) -> str:
        """
        Block an IP address.

        Writes to the BlockedIP table and updates the in-memory set.
        Returns a short action string ("HARD BLOCK" / "SOFT BLOCK").
        Whitelisted IPs are never blocked.
        """
        if ip in self.whitelisted_ips:
            logger.debug("block_ip skipped — %s is whitelisted.", ip)
            return f"IP {ip} is whitelisted — block skipped."

        action = "HARD BLOCK" if hard else "SOFT BLOCK"
        self._db.block_ip_in_db(ip, hard_block=hard, reason=reason or f"Automated {action.lower()}")
        self.blocked_ips.add(ip)
        logger.warning("[ResponseEngine] %s applied to %s", action, ip)
        return action

    def apply_soft_block(self, ip: str, duration: int = 5) -> str:
        """Soft-block an IP (rate-limit signal; not a permanent hard block)."""
        if ip in self.whitelisted_ips:
            return f"IP {ip} is whitelisted — soft block skipped."
        self._db.block_ip_in_db(ip, hard_block=False, reason=f"Soft block ({duration}s)")
        self.blocked_ips.add(ip)
        logger.warning("[ResponseEngine] SOFT BLOCK applied to %s for %ds", ip, duration)
        return f"SOFT BLOCK ({duration}s)"

    def unblock_ip(self, ip: str) -> bool:
        """
        Unblock an IP.

        Sets unblocked_at in the DB and removes from the in-memory set.
        Returns True if the IP was found and unblocked.
        """
        success = self._db.unblock_ip_in_db(ip)
        if success:
            self.blocked_ips.discard(ip)
            logger.info("[ResponseEngine] IP %s unblocked.", ip)
        return success

    # ── Status checks ──────────────────────────────────────────────────────

    def is_blocked(self, ip: str) -> bool:
        """O(1) check using the in-memory set — no DB hit on the hot path."""
        return ip in self.blocked_ips

    def is_whitelisted(self, ip: str) -> bool:
        return ip in self.whitelisted_ips

    # ── Whitelist management ───────────────────────────────────────────────

    def add_to_whitelist(self, ip: str) -> bool:
        """Add an IP to the in-memory whitelist and unblock it if blocked."""
        if ip not in self.whitelisted_ips:
            self.whitelisted_ips.add(ip)
            self.unblock_ip(ip)
            return True
        return False

    def remove_from_whitelist(self, ip: str) -> bool:
        if ip in self.whitelisted_ips:
            self.whitelisted_ips.discard(ip)
            return True
        return False

    # ── Alerting ───────────────────────────────────────────────────────────

    def send_alert(self, ip: str, threat_level: str, reason: str) -> dict:
        """
        Record a CRITICAL alert as a LogEntry in the database.
        Returns the alert dict for callers that need it.
        """
        alert = {
            "timestamp":    datetime.utcnow().isoformat() + "Z",
            "ip":           ip,
            "threat_level": threat_level,
            "reason":       reason,
        }
        self._db.store_log_entry(
            level     = "CRITICAL",
            component = "response_engine",
            message   = f"[ALERT] {threat_level.upper()} from {ip}: {reason}",
            metadata  = alert,
        )
        logger.critical("[ALERT] %s from %s — %s", threat_level.upper(), ip, reason)
        return alert

    # ── Unified executor ───────────────────────────────────────────────────

    def execute_response(self, response_config: dict) -> dict:
        """
        Execute a response action based on the provided configuration.

        Expected keys in response_config:
            type        : "block_ip" | "rate_limit" | "alert" | "isolate"
            ip          : target IP address
            threat_id   : optional identifier
            threat_level: optional severity label
            reason      : optional human-readable reason
            hard        : bool — for block_ip; whether to hard-block (default True)
            duration    : int  — seconds for rate_limit (default 10)
        """
        response_type = response_config.get("type", "alert")
        ip            = response_config.get("ip", "unknown")
        threat_level  = response_config.get("threat_level", "unknown")
        reason        = response_config.get("reason", "Automated response")
        threat_id     = response_config.get("threat_id", "N/A")

        result: dict = {
            "type":      response_type,
            "ip":        ip,
            "threat_id": threat_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "success":   False,
            "details":   "",
        }

        try:
            if response_type == "block_ip":
                hard   = response_config.get("hard", True)
                action = self.block_ip(ip, hard=hard, reason=reason)
                result["success"] = True
                result["details"] = action

            elif response_type == "rate_limit":
                duration = int(response_config.get("duration", 10))
                action   = self.apply_soft_block(ip, duration=duration)
                result["success"] = True
                result["details"] = action

            elif response_type == "alert":
                alert = self.send_alert(ip, threat_level, reason)
                result["success"] = True
                result["details"] = f"Alert logged: {alert}"

            elif response_type == "isolate":
                block_action = self.block_ip(ip, hard=True, reason=f"[ISOLATE] {reason}")
                alert        = self.send_alert(ip, threat_level, f"[ISOLATE] {reason}")
                result["success"] = True
                result["details"] = f"{block_action}; alert logged"

            else:
                result["details"] = f"Unknown response type: {response_type}"

        except Exception as e:
            result["details"] = f"Error executing response: {e}"
            logger.error("[ResponseEngine] execute_response error: %s", e, exc_info=True)

        return result
