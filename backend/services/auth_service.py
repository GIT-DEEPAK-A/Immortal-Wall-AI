# backend/services/auth_service.py
# Passkey-only authentication. No SMTP, no OTP, no registration.

import os


SYSTEM_PASSKEY = os.getenv("SYSTEM_PASSKEY", "123456")


class AuthService:
    """
    Minimal auth service: validates the single system passkey.
    Extend this to add JWT tokens, RBAC, or audit logging when needed.
    """

    @staticmethod
    def verify_passkey(passkey: str) -> bool:
        """Return True if the provided passkey matches the system passkey."""
        return passkey == SYSTEM_PASSKEY
