# backend/database/repositories/user_repo.py
"""UserRepository — all User table operations."""

from __future__ import annotations

import hashlib
import uuid
from typing import Optional

from sqlalchemy.orm import Session

from backend.database.models import User


def _hash_password(password: str, salt: str) -> str:
    """PBKDF2-HMAC-SHA256, 100 000 iterations."""
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100_000,
    ).hex()


class UserRepository:
    """Single-responsibility repository for the User table."""

    def __init__(self, session: Session) -> None:
        self._s = session

    def create(self, email: str, password: str, role: str = "Analyst") -> bool:
        """
        Create a new user with a salted PBKDF2 hash.

        Returns True on success, False if the email already exists.
        """
        existing = self._s.query(User).filter(User.email == email.lower()).first()
        if existing:
            return False

        salt          = uuid.uuid4().hex
        password_hash = _hash_password(password, salt)

        user = User(
            email         = email.lower(),
            password_hash = password_hash,
            salt          = salt,
            role          = role,
        )
        self._s.add(user)
        self._s.commit()
        return True

    def get_by_email(self, email: str) -> Optional[User]:
        """Return the User with the given email address, or None."""
        return self._s.query(User).filter(User.email == email.lower()).first()

    def verify_password(self, email: str, password: str) -> bool:
        """Return True if *password* matches the stored hash for *email*."""
        user = self.get_by_email(email)
        if not user:
            return False
        return _hash_password(password, user.salt) == user.password_hash

    def seed_defaults(self) -> None:
        """
        Idempotently create the default admin user on first run.

        The password is read from the ADMIN_PASSWORD environment variable.
        If the variable is not set, a secure random password is generated and
        printed to stdout exactly once so the operator can record it.
        Called once at application startup.
        """
        import os
        import secrets

        admin_email    = os.getenv("ADMIN_EMAIL",    "analyst@immortalwall.ai")
        admin_password = os.getenv("ADMIN_PASSWORD", "")
        admin_role     = os.getenv("ADMIN_ROLE",     "Admin")

        if self.get_by_email(admin_email):
            return   # already seeded — nothing to do

        if not admin_password:
            admin_password = secrets.token_urlsafe(16)
            print(
                f"\n[UserRepository] *** FIRST RUN ***\n"
                f"  Admin account created: {admin_email}\n"
                f"  Auto-generated password: {admin_password}\n"
                f"  Set ADMIN_PASSWORD in your .env to use a fixed password.\n"
            )

        self.create(admin_email, admin_password, admin_role)
