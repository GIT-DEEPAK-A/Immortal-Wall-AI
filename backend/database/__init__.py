# backend/database/__init__.py
# Re-export DatabaseManager so existing imports keep working:
#   from backend.database import db_manager, get_db_manager
#   from backend.database.db import DatabaseManager

from backend.database.db import DatabaseManager, get_db

# Module-level singleton
db_manager = DatabaseManager()


def get_db_manager() -> DatabaseManager:
    """FastAPI dependency — return the global DatabaseManager."""
    return db_manager
