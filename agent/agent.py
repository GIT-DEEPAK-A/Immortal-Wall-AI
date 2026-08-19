# agent/agent.py

from .monitor import Monitor
import time
import sys
import traceback

class Agent:
    """
    Main entry point for the Immortal Wall AI agent.
    Runs continuous monitoring with error handling.
    """

    def __init__(self):
        self.monitor = Monitor()
        self.running = True

    def start(self):
        """
        Start the agent with robust error handling.
        """
        print("[Agent] Starting Immortal Wall AI Agent...")
        while self.running:
            try:
                self.monitor.start()
            except Exception as e:
                print(f"[Agent Error] {e}")
                traceback.print_exc()
                print("[Agent] Restarting monitor in 2 seconds...")
                time.sleep(2)  # Delay before restart

    def stop(self):
        """
        Stop the agent gracefully.
        """
        print("[Agent] Stopping agent...")
        self.running = False
        self.monitor.running = False

# --- Entry point ---
if __name__ == "__main__":
    agent = Agent()
    try:
        agent.start()
    except KeyboardInterrupt:
        agent.stop()
        print("[Agent] Agent stopped by user.")
        sys.exit(0)