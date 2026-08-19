# agent/config.py

import os

# --- Monitoring Settings ---
MONITOR_INTERVAL = 2  # seconds between each data collection

# --- Thresholds for threat flags ---
THRESHOLDS = {
    "failed_logins": 2,              # e.g., >2 failed logins is suspicious
    "request_rate": 5,              # >5 requests in monitoring interval
    "suspicious_ip_activity": 3     # >3 actions per IP
}

# --- Log File Path ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_PATH = os.path.join(BASE_DIR, "logs", "events.log")