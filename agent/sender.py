# agent/sender.py
import requests
import threading
import time

from .config import LOG_PATH
from utils.logger import log_event

BACKEND_URL = "http://127.0.0.1:8000/api/status/event"


class Sender:
    def __init__(self):
        self.running = False
        self.thread  = None

    def start(self):
        if not self.running:
            self.running = True
            self.thread  = threading.Thread(target=self._run, daemon=True)
            self.thread.start()
            print("[Sender] Started")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("[Sender] Stopped")

    def _run(self):
        while self.running:
            try:
                time.sleep(10)
            except Exception as e:
                print(f"[Sender] Run loop error: {e}")
                time.sleep(5)

    def send_event(self, event: dict):
        _send(event)


def send_event(event: dict):
    """Module-level helper used by collector and monitor."""
    _send(event)


def _send(event: dict):
    """Internal: POST event to backend, fallback to local log on failure."""
    try:
        response = requests.post(BACKEND_URL, json=event, timeout=3)
        if response.status_code == 200:
            analysis = response.json().get("analysis", {})
            level    = analysis.get("threat_level", "unknown")
            print(f"[Sender] → backend OK  threat_level={level}")
        else:
            print(f"[Sender] Backend returned {response.status_code}")
    except requests.exceptions.ConnectionError:
        # Backend not running yet — silent fallback
        pass
    except Exception as e:
        print(f"[Sender] Error: {e}")

    # Always write locally as audit trail
    log_event(event, LOG_PATH)
