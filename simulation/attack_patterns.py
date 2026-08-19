# simulation/attack_patterns.py
"""
Realistic event generators for 7 distinct attack categories.
Each generator returns a fully-formed event dict that matches the
feature schema expected by ml_engine.FeatureExtractor.

Used by:
  - simulation/traffic_generator.py  (live simulation)
  - backend/services/ml_engine.py    (synthetic training data)
"""

import time
import random
import string

# ── IP pools ──────────────────────────────────────────────────────────────
_NORMAL_IPS = [f"10.0.{i}.{j}" for i in range(1, 5) for j in range(1, 50)]
_ATTACKER_IPS = [
    "195.154.92.47",  "185.220.100.255", "91.199.119.66",
    "45.142.212.100", "194.165.16.77",   "198.51.100.5",
    "203.0.113.10",   "192.0.2.200",     "5.188.206.26",
    "80.82.77.139",   "185.234.216.37",  "193.32.162.73",
]
_NORMAL_UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
]
_ATTACK_UAS = [
    "sqlmap/1.7.8#stable (https://sqlmap.org)",
    "Nmap Scripting Engine",
    "python-requests/2.31.0",
    "curl/7.88.1",
    "masscan/1.3",
    "nikto/2.1.6",
    "Mozilla/5.0 zgrab/0.x",
    "dirbuster/1.0-RC1",
]

# ── Helpers ────────────────────────────────────────────────────────────────

def _ts(offset_seconds: float = 0.0) -> float:
    return time.time() + offset_seconds


def _rand_ip(attacker: bool) -> str:
    return random.choice(_ATTACKER_IPS if attacker else _NORMAL_IPS)


def _rand_ua(suspicious: bool) -> str:
    return random.choice(_ATTACK_UAS if suspicious else _NORMAL_UAS)


def _rand_path(pool: list) -> str:
    return random.choice(pool)


def _sql_payload() -> str:
    payloads = [
        "' OR '1'='1", "'; DROP TABLE users; --", "1 UNION SELECT NULL,NULL,NULL--",
        "admin'--", "' OR 1=1--", "1; EXEC xp_cmdshell('whoami')--",
        "' AND SLEEP(5)--", "1' ORDER BY 3--",
    ]
    return random.choice(payloads)


def _xss_payload() -> str:
    payloads = [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert(1)>",
        "javascript:alert(document.cookie)",
        "<svg/onload=alert(1)>",
        "';alert(String.fromCharCode(88,83,83))//",
    ]
    return random.choice(payloads)


def _rand_port() -> int:
    return random.choice([22, 23, 25, 80, 110, 143, 443, 445, 3306, 3389, 5432, 6379, 8080, 8443, 27017])


def _night_ts() -> float:
    """Return a timestamp biased toward 01:00–05:00 UTC."""
    import datetime
    now = datetime.datetime.utcnow()
    attack_hour = random.randint(1, 5)
    dt = now.replace(hour=attack_hour, minute=random.randint(0, 59), second=random.randint(0, 59))
    return dt.timestamp()


# ── Attack generators ──────────────────────────────────────────────────────

def brute_force(n_attempts: int = None) -> dict:
    """
    SSH / HTTP login brute-force.
    High failed-login count, rapid requests, attacker IP, bad UA.
    """
    n = n_attempts or random.randint(8, 50)
    ip = _rand_ip(attacker=True)
    return {
        "timestamp":        _night_ts(),
        "ip":               ip,
        "username":         random.choice(["admin", "root", "user", "test", "administrator"]),
        "event_type":       "login",
        "status":           "failed",
        "path":             "/login",
        "method":           "POST",
        "user_agent":       _rand_ua(suspicious=True),
        "response_code":    401,
        "payload":          "",
        "payload_length":   random.randint(20, 60),
        "session_duration": random.uniform(0.5, 5.0),
        "failed_logins":    n,
        "request_rate":     random.uniform(8.0, 30.0),   # req/s
        "distinct_paths":   1,
        "port":             random.choice([22, 80, 443]),
        "threat_flags": {
            "failed_login":           True,
            "high_request_rate":      True,
            "suspicious_ip_activity": True,
        },
        "attack_type": "brute_force",
    }


def request_flood(intensity: int = None) -> dict:
    """
    HTTP flood / DDoS — very high request rate, minimal payload.
    """
    rate = intensity or random.uniform(50.0, 500.0)
    ip = _rand_ip(attacker=True)
    return {
        "timestamp":        time.time(),
        "ip":               ip,
        "username":         "",
        "event_type":       "request",
        "status":           "success",
        "path":             random.choice(["/", "/index.html", "/api/data", "/health"]),
        "method":           "GET",
        "user_agent":       _rand_ua(suspicious=True),
        "response_code":    200,
        "payload":          "",
        "payload_length":   random.randint(0, 50),
        "session_duration": random.uniform(0.01, 1.0),
        "failed_logins":    0,
        "request_rate":     rate,
        "distinct_paths":   random.randint(1, 3),
        "port":             80,
        "threat_flags": {
            "failed_login":           False,
            "high_request_rate":      True,
            "suspicious_ip_activity": True,
        },
        "attack_type": "ddos",
    }


def sql_injection() -> dict:
    """
    SQL injection probe — payload contains SQL metacharacters.
    """
    payload = _sql_payload()
    ip = _rand_ip(attacker=True)
    paths = ["/login", "/search", "/api/users", "/admin/query", "/db"]
    return {
        "timestamp":        time.time(),
        "ip":               ip,
        "username":         "' OR '1'='1",
        "event_type":       "request",
        "status":           "error",
        "path":             _rand_path(paths),
        "method":           random.choice(["POST", "GET"]),
        "user_agent":       _rand_ua(suspicious=True),
        "response_code":    random.choice([400, 500, 200]),
        "payload":          payload,
        "payload_length":   len(payload),
        "session_duration": random.uniform(1.0, 10.0),
        "failed_logins":    random.randint(0, 2),
        "request_rate":     random.uniform(1.0, 10.0),
        "distinct_paths":   random.randint(3, 15),
        "port":             80,
        "threat_flags": {
            "failed_login":           False,
            "high_request_rate":      False,
            "suspicious_ip_activity": True,
        },
        "attack_type": "sql_injection",
    }


def xss_attack() -> dict:
    """
    Cross-site scripting probe — payload contains script tags / event handlers.
    """
    payload = _xss_payload()
    ip = _rand_ip(attacker=True)
    paths = ["/search", "/comment", "/profile", "/feedback", "/api/message"]
    return {
        "timestamp":        time.time(),
        "ip":               ip,
        "username":         random.choice(["guest", "anonymous", ""]),
        "event_type":       "request",
        "status":           "success",
        "path":             _rand_path(paths),
        "method":           "POST",
        "user_agent":       _rand_ua(suspicious=random.random() > 0.4),
        "response_code":    200,
        "payload":          payload,
        "payload_length":   len(payload),
        "session_duration": random.uniform(5.0, 60.0),
        "failed_logins":    0,
        "request_rate":     random.uniform(0.5, 5.0),
        "distinct_paths":   random.randint(2, 8),
        "port":             80,
        "threat_flags": {
            "failed_login":           False,
            "high_request_rate":      False,
            "suspicious_ip_activity": True,
        },
        "attack_type": "xss",
    }


def port_scan() -> dict:
    """
    Port scanning — many distinct ports probed, low response codes (closed/reset).
    """
    ip = _rand_ip(attacker=True)
    return {
        "timestamp":        time.time(),
        "ip":               ip,
        "username":         "",
        "event_type":       "request",
        "status":           "failed",
        "path":             "/",
        "method":           "GET",
        "user_agent":       _rand_ua(suspicious=True),
        "response_code":    random.choice([0, 111, 403, 404, 500]),
        "payload":          "",
        "payload_length":   0,
        "session_duration": random.uniform(0.001, 0.5),
        "failed_logins":    0,
        "request_rate":     random.uniform(20.0, 100.0),
        "distinct_paths":   random.randint(20, 65535),
        "port":             _rand_port(),
        "threat_flags": {
            "failed_login":           False,
            "high_request_rate":      True,
            "suspicious_ip_activity": True,
        },
        "attack_type": "port_scan",
    }


def credential_stuffing() -> dict:
    """
    Credential stuffing — many different usernames tried at moderate rate.
    """
    ip = _rand_ip(attacker=True)
    usernames = [
        "john.doe", "jane.smith", "admin@company.com", "user1234",
        "test_account", "bob.jones", "alice@example.com",
    ]
    return {
        "timestamp":        _night_ts(),
        "ip":               ip,
        "username":         random.choice(usernames),
        "event_type":       "login",
        "status":           "failed",
        "path":             "/login",
        "method":           "POST",
        "user_agent":       _rand_ua(suspicious=True),
        "response_code":    401,
        "payload":          "",
        "payload_length":   random.randint(30, 80),
        "session_duration": random.uniform(1.0, 15.0),
        "failed_logins":    random.randint(3, 20),
        "request_rate":     random.uniform(2.0, 15.0),
        "distinct_paths":   1,
        "port":             443,
        "threat_flags": {
            "failed_login":           True,
            "high_request_rate":      True,
            "suspicious_ip_activity": True,
        },
        "attack_type": "credential_stuffing",
    }


def malware_upload() -> dict:
    """
    Malicious file upload — oversized / script payload, suspicious path.
    """
    ip = _rand_ip(attacker=True)
    exts = [".php", ".jsp", ".asp", ".sh", ".exe", ".bat", ".py"]
    filename = "".join(random.choices(string.ascii_lowercase, k=8)) + random.choice(exts)
    payload_size = random.randint(50_000, 2_000_000)
    paths = ["/upload", "/admin/upload", "/api/files", "/wp-admin/upload.php"]
    return {
        "timestamp":        time.time(),
        "ip":               ip,
        "username":         random.choice(["guest", "anonymous", "attacker"]),
        "event_type":       "file_access",
        "status":           "success",
        "path":             _rand_path(paths) + "/" + filename,
        "method":           "POST",
        "user_agent":       _rand_ua(suspicious=True),
        "response_code":    random.choice([200, 201, 500]),
        "payload":          filename,
        "payload_length":   payload_size,
        "session_duration": random.uniform(5.0, 120.0),
        "failed_logins":    0,
        "request_rate":     random.uniform(0.1, 3.0),
        "distinct_paths":   random.randint(2, 10),
        "port":             80,
        "threat_flags": {
            "failed_login":           False,
            "high_request_rate":      False,
            "suspicious_ip_activity": True,
        },
        "attack_type": "malware_upload",
    }


def normal_traffic() -> dict:
    """
    Legitimate user traffic — low rates, standard UA, normal paths.
    """
    ip = _rand_ip(attacker=False)
    paths = [
        "/", "/about", "/contact", "/products", "/blog",
        "/api/health", "/login", "/dashboard", "/settings",
    ]
    method = random.choices(["GET", "POST"], weights=[0.8, 0.2])[0]
    status = random.choices(["success", "failed"], weights=[0.95, 0.05])[0]
    return {
        "timestamp":        time.time(),
        "ip":               ip,
        "username":         f"user{random.randint(1, 500)}",
        "event_type":       random.choice(["request", "login", "file_access"]),
        "status":           status,
        "path":             _rand_path(paths),
        "method":           method,
        "user_agent":       _rand_ua(suspicious=False),
        "response_code":    random.choices([200, 201, 301, 304, 404], weights=[0.6, 0.1, 0.1, 0.1, 0.1])[0],
        "payload":          "",
        "payload_length":   random.randint(0, 500),
        "session_duration": random.uniform(30.0, 1800.0),
        "failed_logins":    0 if status == "success" else 1,
        "request_rate":     random.uniform(0.1, 2.0),
        "distinct_paths":   random.randint(1, 8),
        "port":             443,
        "threat_flags": {
            "failed_login":           status == "failed",
            "high_request_rate":      False,
            "suspicious_ip_activity": False,
        },
        "attack_type": "normal",
    }


# ── Convenience dispatch ───────────────────────────────────────────────────

ATTACK_GENERATORS = {
    "brute_force":         brute_force,
    "ddos":                request_flood,
    "sql_injection":       sql_injection,
    "xss":                 xss_attack,
    "port_scan":           port_scan,
    "credential_stuffing": credential_stuffing,
    "malware_upload":      malware_upload,
    "normal":              normal_traffic,
}

LABEL_MAP = {
    "normal":              0,
    "brute_force":         2,   # malicious
    "ddos":                2,
    "sql_injection":       2,
    "xss":                 1,   # suspicious → can escalate
    "port_scan":           1,
    "credential_stuffing": 2,
    "malware_upload":      2,
}


def generate_event(attack_type: str = None) -> dict:
    """Generate one event of the given type (random if None)."""
    if attack_type is None:
        attack_type = random.choices(
            list(ATTACK_GENERATORS.keys()),
            weights=[40, 10, 10, 8, 8, 8, 8, 8],  # normal traffic dominates
        )[0]
    return ATTACK_GENERATORS[attack_type]()
