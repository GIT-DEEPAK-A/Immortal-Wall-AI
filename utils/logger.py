# utils/logger.py

import json
import threading
import os
import logging

lock = threading.Lock()  # Ensure thread-safe logging

def setup_logger(name: str) -> logging.Logger:
    """
    Setup a logger with the given name.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def log_event(event: dict, log_file_path: str):
    """
    Log an event dictionary to a log file as a single JSON line.
    Thread-safe and ensures the log directory exists.
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

        with lock:
            with open(log_file_path, "a") as f:
                f.write(json.dumps(event) + "\n")
    except Exception as e:
        print(f"[Logger Error] Failed to write to {log_file_path}: {e}")