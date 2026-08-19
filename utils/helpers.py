# utils/helpers.py
# General-purpose utility functions used across the project.

import re
import ipaddress
import hashlib
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional


# ── IP utilities ───────────────────────────────────────────────────────────


def is_valid_ip(ip: str) -> bool:
    """Return True if *ip* is a valid IPv4 or IPv6 address."""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def is_private_ip(ip: str) -> bool:
    """Return True if *ip* is in an RFC-1918 private range."""
    try:
        return ipaddress.ip_address(ip).is_private
    except ValueError:
        return False


def ip_to_int(ip: str) -> int:
    """Convert a dotted-decimal IPv4 string to its integer representation."""
    try:
        return int(ipaddress.IPv4Address(ip))
    except ValueError:
        return 0


# ── Timestamp helpers ──────────────────────────────────────────────────────


def now_utc() -> datetime:
    """Return the current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)


def ts_to_iso(ts: float) -> str:
    """Convert a UNIX timestamp float to an ISO-8601 string (UTC)."""
    return datetime.utcfromtimestamp(ts).isoformat() + "Z"


def iso_to_ts(iso: str) -> float:
    """Convert an ISO-8601 string to a UNIX timestamp float. Returns 0.0 on error."""
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.timestamp()
    except Exception:
        return 0.0


def elapsed_seconds(start_ts: float) -> float:
    """Return the number of seconds elapsed since *start_ts* (UNIX time)."""
    return time.time() - start_ts


# ── String / security helpers ──────────────────────────────────────────────


def truncate(text: str, max_len: int = 200, suffix: str = "…") -> str:
    """Truncate *text* to *max_len* characters, appending *suffix* if trimmed."""
    if len(text) <= max_len:
        return text
    return text[: max_len - len(suffix)] + suffix


def sanitize_log_string(value: str) -> str:
    """
    Strip control characters and common log-injection sequences from a string.
    Prevents CRLF injection in log files.
    """
    # Remove newlines, carriage returns, and null bytes
    value = re.sub(r"[\r\n\x00]", " ", value)
    # Strip ANSI escape codes
    value = re.sub(r"\x1b\[[0-9;]*m", "", value)
    return value.strip()


def sha256_hex(data: str) -> str:
    """Return the lowercase hex-encoded SHA-256 digest of *data*."""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


# ── Event helpers ──────────────────────────────────────────────────────────


def enrich_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add computed fields to a raw event dict if they are missing.
    Returns the enriched dict (mutates in place).
    """
    if "timestamp" not in event:
        event["timestamp"] = time.time()

    if "ip" not in event:
        event["ip"] = "0.0.0.0"

    # Derive simple geo hint: private vs public
    ip = event.get("ip", "0.0.0.0")
    event.setdefault("is_private_ip", is_private_ip(ip))

    return event


def flatten_threat_flags(threat_flags: Dict[str, bool]) -> int:
    """
    Reduce a threat_flags dict to a bitmask integer for quick comparisons.
    Bit 0 = failed_login, Bit 1 = high_request_rate, Bit 2 = suspicious_ip_activity
    """
    mapping = {
        "failed_login": 0,
        "high_request_rate": 1,
        "suspicious_ip_activity": 2,
    }
    result = 0
    for key, bit in mapping.items():
        if threat_flags.get(key):
            result |= (1 << bit)
    return result


def safe_get(d: Dict, *keys: str, default: Any = None) -> Any:
    """Traverse nested dicts safely. Returns *default* if any key is missing."""
    current = d
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key, default)
    return current


# ── Formatting helpers ─────────────────────────────────────────────────────


def format_bytes(num_bytes: int) -> str:
    """Return a human-readable file size string, e.g. '1.23 KB'."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(num_bytes) < 1024:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.2f} PB"


def format_duration(seconds: float) -> str:
    """Return a human-readable duration string, e.g. '2h 15m 30s'."""
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    parts = []
    if h:
        parts.append(f"{h}h")
    if m:
        parts.append(f"{m}m")
    parts.append(f"{s}s")
    return " ".join(parts)
