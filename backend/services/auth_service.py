# backend/services/auth_service.py
"""
Authentication service.

Delegates all credential verification to UserRepository so the hashing
logic lives in exactly one place (PBKDF2-HMAC-SHA256, 100 000 iterations).
"""

from __future__ import annotations

from backend.container import db


class AuthService:
    """Thin wrapper around UserRepository for auth operations."""

    @staticmethod
    def verify_credentials(email: str, password: str) -> bool:
        """Return True if email + password match a record in the users table."""
        return db.verify_user_password(email, password)

    @staticmethod
    def get_user(email: str):
        """Return the User ORM instance for *email*, or None."""
        return db.get_user_by_email(email)
