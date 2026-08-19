# simulation/config.py
# Configuration for the traffic generator and attack simulation modules.

import os

# ── General simulation settings ────────────────────────────────────────────
DEFAULT_INTERVAL     = float(os.getenv("SIM_INTERVAL", "2"))        # seconds between events
DEFAULT_ATTACK_CHANCE = float(os.getenv("SIM_ATTACK_CHANCE", "0.3")) # 30% of events are attacks
DEFAULT_DURATION     = int(os.getenv("SIM_DURATION", "300"))          # default run time in seconds

# ── Target backend URL ─────────────────────────────────────────────────────
BACKEND_EVENT_URL = os.getenv("BACKEND_EVENT_URL", "http://127.0.0.1:8000/api/status/event")

# ── Synthetic attack intensities ───────────────────────────────────────────
INTENSITY_PRESETS = {
    "low":    {"interval": 5.0,  "attack_chance": 0.1},
    "medium": {"interval": 2.0,  "attack_chance": 0.3},
    "high":   {"interval": 0.5,  "attack_chance": 0.6},
    "storm":  {"interval": 0.1,  "attack_chance": 0.9},
}

# ── IP pools ───────────────────────────────────────────────────────────────
NORMAL_IP_POOL   = [f"10.0.0.{i}"      for i in range(1, 101)]
ATTACKER_IP_POOL = [f"192.168.100.{i}" for i in range(1, 51)] + [
    "203.0.113.10", "198.51.100.5", "91.199.119.66",
    "185.220.100.255", "195.154.92.47",
]

# ── Simulated usernames ────────────────────────────────────────────────────
NORMAL_USERS  = [f"user{i}"     for i in range(1, 21)]
ATTACKER_USERS = ["admin", "root", "test", "guest", "administrator",
                  "sa", "oracle", "postgres", "ubuntu", "pi"]

# ── Log paths (relative to project root) ──────────────────────────────────
BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVENTS_LOG   = os.path.join(BASE_DIR, "logs", "events.log")
ATTACKS_LOG  = os.path.join(BASE_DIR, "logs", "attacks.log")
