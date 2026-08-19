# backend/services/rule_engine.py
"""
Deterministic rule engine for Immortal Wall AI.

Each rule evaluates a specific threat pattern and returns a partial score
(0.0–1.0) plus a descriptive tag.  Rules are additive and independent —
the combined score is capped at 1.0 before being handed off to the
ThreatEngine for fusion with the ML score.

Rule categories:
  AUTH     — brute force, credential stuffing
  FLOOD    — HTTP/TCP flood, DDoS
  INJECT   — SQL injection, XSS
  RECON    — port scan, directory traversal
  IDENTITY — known-bad IP, suspicious user-agent, geo anomaly
  TEMPORAL — off-hours activity
  PAYLOAD  — oversized or script-embedded payloads
"""

from __future__ import annotations

import re
from typing import Dict, List, Tuple

# ── Tunable thresholds ─────────────────────────────────────────────────────
_T_FAILED_LOGINS        = 3       # failed logins before brute-force flag
_T_REQUEST_RATE_SOFT    = 10.0    # req/s → suspicious
_T_REQUEST_RATE_HARD    = 50.0    # req/s → malicious
_T_DISTINCT_PATHS       = 30      # distinct paths → port/dir scan
_T_PAYLOAD_SOFT_KB      = 200     # KB → large payload suspicious
_T_PAYLOAD_HARD_KB      = 2048    # KB → very large payload malicious
_T_SESSION_SHORT_SEC    = 2.0     # session too short → automated tool

# ── Known bad identifiers (mirrors ml_engine for consistency) ─────────────
_KNOWN_BAD_IPS = frozenset({
    "195.154.92.47", "185.220.100.255", "91.199.119.66",
    "45.142.212.100", "194.165.16.77",  "198.51.100.5",
    "203.0.113.10",   "192.0.2.200",    "5.188.206.26",
    "80.82.77.139",   "185.234.216.37", "193.32.162.73",
})

_GEO_BAD_PREFIXES = (
    "185.220.", "195.154.", "91.199.", "45.142.",
    "194.165.", "80.82.",   "5.188.",  "193.32.",
)

_SUSPICIOUS_UA = (
    "sqlmap", "nmap", "masscan", "nikto", "metasploit",
    "burpsuite", "dirbuster", "zgrab", "python-requests",
    "curl/", "wget/", "go-http-client", "libwww",
    "scrapy", "mechanize", "httpclient",
)

_SUSPICIOUS_PATHS_RE = re.compile(
    r"(/admin|/phpmyadmin|/\.env|/wp-admin|/shell|"
    r"/config|/\.git|/backup|/db|/sql|/passwd|"
    r"/etc/shadow|/proc/|/cmd|/\.htaccess|/\.htpasswd)",
    re.IGNORECASE,
)

_SQL_INJECTION_RE = re.compile(
    r"('|\"|\;|--|/\*|\*/|xp_|exec\s*\(|union\s+|select\s+|insert\s+|drop\s+|alter\s+|"
    r"cast\s*\(|convert\s*\(|sleep\s*\(|benchmark\s*\(|or\s+1=1|and\s+1=1)",
    re.IGNORECASE,
)

_XSS_RE = re.compile(
    r"(<script|onerror\s*=|onload\s*=|javascript:|alert\s*\(|"
    r"<svg|<img[^>]+onerror|document\.cookie|eval\s*\(|"
    r"String\.fromCharCode|&#[0-9]+;|%3cscript)",
    re.IGNORECASE,
)

# ── Rule result type ───────────────────────────────────────────────────────
# Each rule returns (score: float, tag: str) or None if it doesn't fire.
RuleResult = Tuple[float, str]


# ── Individual rules ──────────────────────────────────────────────────────

def _rule_brute_force(event: dict):
    """AUTH-001: Repeated failed login attempts."""
    if event.get("event_type") != "login":
        return None
    if event.get("status") != "failed":
        return None
    count = int(event.get("failed_logins", 0))
    flags = event.get("threat_flags", {})
    if count >= _T_FAILED_LOGINS or flags.get("failed_login"):
        # Score scales with count
        score = min(0.5 + (count - _T_FAILED_LOGINS) * 0.02, 0.9)
        return (score, f"brute_force ({count} failed logins)")
    return None


def _rule_credential_stuffing(event: dict):
    """AUTH-002: High failed-login rate with varying usernames (automated)."""
    if event.get("event_type") != "login":
        return None
    rate    = float(event.get("request_rate", 0))
    count   = int(event.get("failed_logins", 0))
    ua      = str(event.get("user_agent", "")).lower()
    bad_ua  = any(tok in ua for tok in _SUSPICIOUS_UA)
    if count >= 3 and rate >= 2.0 and bad_ua:
        return (0.75, "credential_stuffing (automated login tool)")
    return None


def _rule_http_flood(event: dict):
    """FLOOD-001: HTTP request flood / DDoS."""
    rate = float(event.get("request_rate", 0))
    flags = event.get("threat_flags", {})
    if rate >= _T_REQUEST_RATE_HARD or flags.get("high_request_rate"):
        score = 0.9 if rate >= _T_REQUEST_RATE_HARD else 0.6
        return (score, f"http_flood ({rate:.1f} req/s)")
    if rate >= _T_REQUEST_RATE_SOFT:
        return (0.45, f"elevated_request_rate ({rate:.1f} req/s)")
    return None


def _rule_port_scan(event: dict):
    """RECON-001: Port or directory scan — many distinct paths probed."""
    paths = int(event.get("distinct_paths", 0))
    rate  = float(event.get("request_rate", 0))
    sess  = float(event.get("session_duration", 999))
    if paths >= _T_DISTINCT_PATHS and rate >= 5.0:
        score = min(0.5 + paths / 200.0, 0.95)
        return (score, f"port_scan ({paths} distinct paths)")
    if paths >= 10 and sess < _T_SESSION_SHORT_SEC:
        return (0.45, f"directory_scan ({paths} paths, {sess:.1f}s session)")
    return None


def _rule_sql_injection(event: dict):
    """INJECT-001: SQL injection chars or keywords in payload / path."""
    payload = str(event.get("payload", ""))
    path    = str(event.get("path", ""))
    target  = payload + " " + path
    if _SQL_INJECTION_RE.search(target):
        # Hard severity if it's in a login/admin path
        path_lower = path.lower()
        is_critical = any(p in path_lower for p in ("/login", "/admin", "/db", "/api"))
        score = 0.95 if is_critical else 0.80
        return (score, "sql_injection")
    return None


def _rule_xss(event: dict):
    """INJECT-002: Cross-site scripting chars or event handlers in payload."""
    payload = str(event.get("payload", ""))
    if _XSS_RE.search(payload):
        return (0.70, "xss_attempt")
    return None


def _rule_suspicious_path(event: dict):
    """RECON-002: Request targeting a sensitive or hidden path."""
    path = str(event.get("path", ""))
    if _SUSPICIOUS_PATHS_RE.search(path):
        return (0.55, f"suspicious_path_access ({path[:60]})")
    return None


def _rule_known_bad_ip(event: dict):
    """IDENTITY-001: IP address matches known-bad threat-intelligence list."""
    ip = str(event.get("ip", ""))
    if ip in _KNOWN_BAD_IPS:
        return (0.90, f"known_bad_ip ({ip})")
    return None


def _rule_geo_anomaly(event: dict):
    """IDENTITY-002: Traffic from high-risk geographic prefix."""
    ip = str(event.get("ip", ""))
    if any(ip.startswith(pfx) for pfx in _GEO_BAD_PREFIXES):
        return (0.45, f"geo_anomaly ({ip})")
    return None


def _rule_suspicious_ua(event: dict):
    """IDENTITY-003: Known attack-tool user-agent string."""
    ua = str(event.get("user_agent", "")).lower()
    for tok in _SUSPICIOUS_UA:
        if tok in ua:
            return (0.65, f"attack_tool_ua ({tok})")
    return None


def _rule_large_payload(event: dict):
    """PAYLOAD-001: Abnormally large request body."""
    length_bytes = float(event.get("payload_length", 0))
    if length_bytes >= _T_PAYLOAD_HARD_KB * 1024:
        return (0.70, f"oversized_payload ({length_bytes/1024:.0f} KB)")
    if length_bytes >= _T_PAYLOAD_SOFT_KB * 1024:
        return (0.40, f"large_payload ({length_bytes/1024:.0f} KB)")
    return None


def _rule_off_hours(event: dict):
    """TEMPORAL-001: Activity during typical off-hours (01:00–05:00 UTC)."""
    import time
    from datetime import datetime, timezone
    ts  = float(event.get("timestamp") or time.time())
    dt  = datetime.fromtimestamp(ts, tz=timezone.utc)
    if dt.hour in (1, 2, 3, 4, 5):
        return (0.20, f"off_hours ({dt.hour:02d}:00 UTC)")
    return None


def _rule_suspicious_ip_flag(event: dict):
    """IDENTITY-004: Agent-level suspicious IP activity flag."""
    if event.get("threat_flags", {}).get("suspicious_ip_activity"):
        return (0.35, "suspicious_ip_activity_flag")
    return None


# ── Rule registry ──────────────────────────────────────────────────────────
_RULES = [
    _rule_known_bad_ip,        # highest priority first
    _rule_sql_injection,
    _rule_brute_force,
    _rule_credential_stuffing,
    _rule_http_flood,
    _rule_port_scan,
    _rule_xss,
    _rule_large_payload,
    _rule_suspicious_path,
    _rule_suspicious_ua,
    _rule_off_hours,
    _rule_geo_anomaly,
    _rule_suspicious_ip_flag,
]


# ── Public API ─────────────────────────────────────────────────────────────

def evaluate_rules(event: dict) -> Tuple[float, Dict[str, bool], str]:
    """
    Run all rules against *event*.

    Returns
    -------
    score   : float  0.0–1.0  combined rule score (capped)
    flags   : dict   {flag_name: bool}  legacy compatibility
    reason  : str    pipe-separated list of fired rule tags
    """
    fired:   List[RuleResult] = []
    raw_score = 0.0

    for rule in _RULES:
        try:
            result = rule(event)
        except Exception:
            continue
        if result is not None:
            score, tag = result
            fired.append(result)
            raw_score += score

    # Diminishing returns: cap at 1.0 with soft-clipping
    combined_score = float(min(raw_score, 1.0))

    # Legacy flags for backward-compat with old routes
    tags = [tag for _, tag in fired]
    flags = {
        "failed_login":           any("brute_force" in t or "credential" in t for t in tags),
        "high_request_rate":      any("flood" in t or "elevated" in t for t in tags),
        "suspicious_ip_activity": any(
            "known_bad" in t or "geo_anomaly" in t or "suspicious_ip" in t
            for t in tags
        ),
    }

    reason = " | ".join(tags) if tags else "normal behavior"
    return combined_score, flags, reason


def classify_attack_type(event: dict) -> str:
    """
    Best-effort attack classification based on which rules fire.
    Returns a human-readable attack category string.
    """
    payload = str(event.get("payload", "")).lower()
    path    = str(event.get("path", "")).lower()
    ua      = str(event.get("user_agent", "")).lower()

    if _SQL_INJECTION_RE.search(payload + " " + path):
        return "sql_injection"
    if _XSS_RE.search(payload):
        return "xss"
    if event.get("event_type") == "login" and event.get("status") == "failed":
        if float(event.get("request_rate", 0)) >= 2.0 and any(tok in ua for tok in _SUSPICIOUS_UA):
            return "credential_stuffing"
        return "brute_force"
    if float(event.get("request_rate", 0)) >= _T_REQUEST_RATE_HARD:
        return "ddos"
    if int(event.get("distinct_paths", 0)) >= _T_DISTINCT_PATHS:
        return "port_scan"
    pay_len = float(event.get("payload_length", 0))
    if pay_len >= _T_PAYLOAD_SOFT_KB * 1024:
        return "malware_upload"
    return "unknown"
