import os
from pathlib import Path

# Project root directory
ROOT_DIR = Path(__file__).parent.parent

# Directory configuration
LOG_DIR = ROOT_DIR / "logs"
DATA_DIR = ROOT_DIR / "data"
EVENTS_LOG = LOG_DIR / "events.log"
ALERTS_LOG = LOG_DIR / "alerts.log"
BLOCKED_IPS_PATH = DATA_DIR / "blocked_ips.json"
WHITELIST_PATH = DATA_DIR / "whitelisted_ips.json"

# Create directories if they don't exist
LOG_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR}/immortal_wall.db")
DB_PATH = os.getenv("DB_PATH", f"{DATA_DIR}/immortal_wall.db")

# SMTP Email Configuration
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_SENDER = os.getenv("SMTP_SENDER", "deepakananthan4@gmail.com")
SMTP_APP_PASSWORD = os.getenv("SMTP_APP_PASSWORD", "")

# OTP Configuration
OTP_TTL_MINUTES = int(os.getenv("OTP_TTL_MINUTES", "10"))
OTP_MAX_ATTEMPTS = int(os.getenv("OTP_MAX_ATTEMPTS", "3"))

# Session Configuration
SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "your_secret_key_change_this_in_production")

# Server Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
UVICORN_WORKERS = int(os.getenv("UVICORN_WORKERS", "4"))

# Security Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key_change_this_in_production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", f"{LOG_DIR}/backend.log")

# CORS Configuration
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:5179,http://localhost:3000").split(",")

