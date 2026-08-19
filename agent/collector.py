# agent/collector.py

import os
import sys
import time
import random
import threading

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from .config import THRESHOLDS, LOG_PATH
from .sender import send_event
from utils.logger import log_event


class Collector:
    """
    Collector class: Simulates or collects system activity
    and formats it for the agent.
    """

    def __init__(self):
        self.failed_logins: dict = {}
        self.request_count: dict = {}
        self.ip_activity: dict = {}
        self.running = False
        self.thread = None

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()
            print("[Collector] Started")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("[Collector] Stopped")

    def _run(self):
        while self.running:
            try:
                event = self.collect()
                send_event(event)
                time.sleep(2)
            except Exception as e:
                print(f"[Collector] Error in run loop: {e}")
                time.sleep(5)

    def generate_event(self) -> dict:
        """Simulate system activity for demonstration."""
        event_types = ["login", "request", "file_access"]
        ip = f"192.168.1.{random.randint(1, 255)}"
        event_type = random.choice(event_types)
        username = f"user{random.randint(1, 20)}"
        timestamp = time.time()

        event = {
            "timestamp": timestamp,
            "ip": ip,
            "username": username,
            "event_type": event_type,
        }

        # Track failed logins (10 % failure rate)
        if event_type == "login" and random.random() < 0.1:
            self.failed_logins[ip] = self.failed_logins.get(ip, 0) + 1
            event["status"] = "failed"
        else:
            event["status"] = "success"

        # Track request frequency
        self.request_count[ip] = self.request_count.get(ip, 0) + 1

        # Track suspicious IP activity
        self.ip_activity[ip] = self.ip_activity.get(ip, 0) + 1

        return event

    def collect(self) -> dict:
        """Collect a structured event ready to send to the backend."""
        event = self.generate_event()

        threat_flags = {
            "failed_login": self.failed_logins.get(event["ip"], 0) > THRESHOLDS["failed_logins"],
            "high_request_rate": self.request_count.get(event["ip"], 0) > THRESHOLDS["request_rate"],
            "suspicious_ip_activity": self.ip_activity.get(event["ip"], 0) > THRESHOLDS["suspicious_ip_activity"],
        }

        event["threat_flags"] = threat_flags

        # Write to local log file
        log_event(event, LOG_PATH)

        return event
