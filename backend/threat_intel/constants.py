"""
backend/threat_intel/constants.py
──────────────────────────────────
Single source of truth for all threat-intelligence constants.

Both rule_engine.py and ml_engine.py import from here so that updating
the blocklist or UA tokens is a one-line change in one place.
"""

from __future__ import annotations

# ── Known-bad exact IPs ────────────────────────────────────────────────────
KNOWN_BAD_IPS: frozenset = frozenset({
    "195.154.92.47",  "185.220.100.255", "91.199.119.66",
    "45.142.212.100", "194.165.16.77",   "198.51.100.5",
    "203.0.113.10",   "192.0.2.200",     "5.188.206.26",
    "80.82.77.139",   "185.234.216.37",  "193.32.162.73",
})

# ── High-risk geographic IP prefixes ──────────────────────────────────────
GEO_BAD_PREFIXES: tuple = (
    "185.220.", "195.154.", "91.199.", "45.142.",
    "194.165.", "80.82.",   "5.188.",  "193.32.",
)

# ── Known attack-tool user-agent tokens (lowercase) ───────────────────────
SUSPICIOUS_UA_TOKENS: tuple = (
    "sqlmap", "nmap", "masscan", "nikto", "metasploit",
    "burpsuite", "dirbuster", "zgrab", "python-requests",
    "curl/", "wget/", "go-http-client", "libwww",
    "scrapy", "mechanize", "httpclient",
)

# ── Sensitive paths targeted by recon tools ───────────────────────────────
SUSPICIOUS_PATHS: tuple = (
    "/admin", "/phpmyadmin", "/.env", "/wp-admin", "/shell",
    "/config", "/.git", "/backup", "/db", "/sql",
    "/passwd", "/etc/shadow", "/proc/", "/cmd",
    "/.htaccess", "/.htpasswd",
)

# ── SQL injection token fragments (lowercase) ─────────────────────────────
SQL_INJECTION_TOKENS: tuple = (
    "'", '"', ";", "--", "/*", "*/", "xp_", "exec(",
    "union ", "select ", "insert ", "drop ",
    "cast(", "convert(", "sleep(", "benchmark(", "or 1=1", "and 1=1",
)

# ── XSS token fragments (lowercase) ──────────────────────────────────────
XSS_TOKENS: tuple = (
    "<script", "onerror=", "onload=", "javascript:", "alert(",
    "<svg", "<img ", "document.cookie", "eval(", "string.fromcharcode",
)
