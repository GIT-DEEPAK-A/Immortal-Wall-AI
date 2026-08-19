# agent/monitor.py

import time
from .collector import Collector
from .config import MONITOR_INTERVAL
from .sender import send_event


class Monitor:
    """
    Continuous monitoring loop for system activity.
    Uses an iterative restart strategy instead of recursion
    to prevent unbounded call-stack growth on repeated errors.
    """

    def __init__(self):
        self.collector = Collector()
        self.running = True

    def start(self):
        """Start the monitoring loop. Restarts automatically on errors."""
        print("[Monitor] Starting continuous monitoring...")
        while self.running:
            try:
                self._run_loop()
            except KeyboardInterrupt:
                print("[Monitor] Stopped by user.")
                self.running = False
            except Exception as e:
                print(f"[Monitor Error] {e}")
                if self.running:
                    print("[Monitor] Restarting monitoring loop in 1s...")
                    time.sleep(1)
                    # Loop continues — no recursive call

    def _run_loop(self):
        """Inner event-collection loop."""
        while self.running:
            event = self.collector.collect()
            send_event(event)
            time.sleep(MONITOR_INTERVAL)


if __name__ == "__main__":
    monitor = Monitor()
    monitor.start()
