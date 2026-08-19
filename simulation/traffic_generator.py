# simulation/traffic_generator.py

import os
import sys
import random
import time
import threading

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from utils.logger import log_event

# Log file paths relative to project root
EVENTS_LOG = os.path.join(ROOT_DIR, "logs", "events.log")
ATTACKS_LOG = os.path.join(ROOT_DIR, "logs", "attacks.log")

NORMAL_USERS = [f"user{i}" for i in range(1, 21)]
ATTACKERS = [f"attacker{i}" for i in range(1, 6)]
IP_POOL = [f"192.168.1.{i}" for i in range(2, 255)]


def generate_normal_activity() -> dict:
    event = {
        "timestamp": time.time(),
        "ip": random.choice(IP_POOL),
        "username": random.choice(NORMAL_USERS),
        "event_type": random.choice(["login", "request", "file_access"]),
        "status": "success",
        "threat_flags": {
            "failed_login": False,
            "high_request_rate": False,
            "suspicious_ip_activity": False,
        },
    }
    # Fixed: log_event(event, path) — event dict first, path second
    log_event(event, EVENTS_LOG)
    return event


def generate_attack_activity() -> dict:
    event = {
        "timestamp": time.time(),
        "ip": random.choice(IP_POOL),
        "username": random.choice(ATTACKERS),
        "event_type": random.choice(["login", "request", "file_access"]),
        "status": "failed",
        "threat_flags": {
            "failed_login": True,
            "high_request_rate": True,
            "suspicious_ip_activity": True,
        },
    }
    # Fixed: log_event(event, path) — event dict first, path second
    log_event(event, ATTACKS_LOG)
    return event


def start_simulation(interval: float = 2, attack_chance: float = 0.3):
    print("[Simulation] Starting traffic generator...")
    while True:
        if random.random() < attack_chance:
            event = generate_attack_activity()
            print(f"[Attack]  {event}")
        else:
            event = generate_normal_activity()
            print(f"[Normal]  {event}")
        time.sleep(interval)


class TrafficGenerator:
    def __init__(self, interval: float = 2, attack_chance: float = 0.3):
        self.running = False
        self.interval = interval
        self.attack_chance = attack_chance
        self.thread = None

    def start(self):
        """Start the traffic generator in a background thread."""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()
            print("[TrafficGenerator] Started")

    def stop(self):
        """Stop the traffic generator."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("[TrafficGenerator] Stopped")

    def _run(self):
        while self.running:
            try:
                if random.random() < self.attack_chance:
                    event = generate_attack_activity()
                    print(f"[Attack]  {event}")
                else:
                    event = generate_normal_activity()
                    print(f"[Normal]  {event}")
                time.sleep(self.interval)
            except Exception as e:
                print(f"[TrafficGenerator] Error: {e}")
                time.sleep(5)


if __name__ == "__main__":
    start_simulation()
