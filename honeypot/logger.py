# honeypot/logger.py

import os
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_PATH = os.path.join(BASE_DIR, "logs", "honeypot.log")

def log_honeypot_event(event: dict):
    """
    Log all honeypot activity to honeypot.log
    """
    try:
        event["timestamp"] = datetime.now().isoformat()
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "a") as f:
            f.write(json.dumps(event) + "\n")
        print(f"[Honeypot] Logged event: {event}")
    except Exception as e:
        print(f"[Honeypot Error] Failed to log event: {e}")