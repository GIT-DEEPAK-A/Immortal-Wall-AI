from .models import DatabaseManager

# Global database manager instance
db_manager = DatabaseManager()

def get_db_manager() -> DatabaseManager:
    """Dependency injection function for FastAPI"""
    return db_manager