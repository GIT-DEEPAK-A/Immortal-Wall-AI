# utils/constants.py
# Project-wide constants shared across backend, agent, honeypot, and simulation.

# ── Threat levels ──────────────────────────────────────────────────────────
THREAT_LEVEL_NORMAL     = "normal"
THREAT_LEVEL_SUSPICIOUS = "suspicious"
THREAT_LEVEL_MALICIOUS  = "malicious"

THREAT_LEVELS = [THREAT_LEVEL_NORMAL, THREAT_LEVEL_SUSPICIOUS, THREAT_LEVEL_MALICIOUS]

# Numeric thresholds that map a combined score to a level
SCORE_SUSPICIOUS_THRESHOLD = 0.4
SCORE_MALICIOUS_THRESHOLD  = 0.7

# ── Response action types ──────────────────────────────────────────────────
RESPONSE_BLOCK_IP   = "block_ip"
RESPONSE_RATE_LIMIT = "rate_limit"
RESPONSE_ALERT      = "alert"
RESPONSE_ISOLATE    = "isolate"

RESPONSE_TYPES = [RESPONSE_BLOCK_IP, RESPONSE_RATE_LIMIT, RESPONSE_ALERT, RESPONSE_ISOLATE]

# ── Event types ────────────────────────────────────────────────────────────
EVENT_TYPE_LOGIN       = "login"
EVENT_TYPE_REQUEST     = "request"
EVENT_TYPE_FILE_ACCESS = "file_access"
EVENT_TYPE_SCAN        = "scan"
EVENT_TYPE_UPLOAD      = "upload"

EVENT_TYPES = [EVENT_TYPE_LOGIN, EVENT_TYPE_REQUEST, EVENT_TYPE_FILE_ACCESS,
               EVENT_TYPE_SCAN, EVENT_TYPE_UPLOAD]

# ── Log levels ────────────────────────────────────────────────────────────
LOG_LEVEL_DEBUG    = "DEBUG"
LOG_LEVEL_INFO     = "INFO"
LOG_LEVEL_WARNING  = "WARNING"
LOG_LEVEL_ERROR    = "ERROR"
LOG_LEVEL_CRITICAL = "CRITICAL"

# ── Attack categories ──────────────────────────────────────────────────────
ATTACK_BRUTE_FORCE       = "brute_force"
ATTACK_SQL_INJECTION     = "sql_injection"
ATTACK_XSS               = "xss"
ATTACK_DDOS              = "ddos"
ATTACK_CREDENTIAL_STUFF  = "credential_stuffing"
ATTACK_PORT_SCAN         = "port_scan"
ATTACK_MALWARE_UPLOAD    = "malware_upload"

ATTACK_TYPES = [
    ATTACK_BRUTE_FORCE, ATTACK_SQL_INJECTION, ATTACK_XSS,
    ATTACK_DDOS, ATTACK_CREDENTIAL_STUFF, ATTACK_PORT_SCAN, ATTACK_MALWARE_UPLOAD,
]

# ── Suspicious user-agent substrings detected by the ML engine ────────────
SUSPICIOUS_USER_AGENTS = [
    "sqlmap", "nmap", "metasploit", "burp", "owasp",
    "nikto", "masscan", "zap", "python-requests", "curl/",
]

# ── Known test / documentation IP ranges (RFC 5737) ───────────────────────
RESERVED_IP_PREFIXES = ["203.0.113.", "198.51.100.", "192.0.2."]

# ── Honeypot port defaults ─────────────────────────────────────────────────
HONEYPOT_PORT        = 5001
HONEYPOT_ADMIN_PATH  = "/admin"
HONEYPOT_LOGIN_PATH  = "/login"
HONEYPOT_DB_PATH     = "/db"
HONEYPOT_API_PATH    = "/api/data"

# ── Backend defaults ───────────────────────────────────────────────────────
BACKEND_HOST         = "0.0.0.0"
BACKEND_PORT         = 8000
BACKEND_RELOAD       = False

# ── Agent defaults ─────────────────────────────────────────────────────────
AGENT_SEND_URL       = "http://127.0.0.1:8000/api/status/event"
AGENT_MONITOR_INTERVAL = 2   # seconds between collection cycles
