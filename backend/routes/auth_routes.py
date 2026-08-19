# backend/routes/auth_routes.py
"""
Email + password authentication.

POST /api/auth/login
  Body: { "email": "...", "password": "..." }
  200 → { "access_token": "...", "token_type": "bearer", "user": {...} }
  401 → invalid credentials (never reveals which field was wrong)

All password verification is delegated to UserRepository.verify_password()
which uses PBKDF2-HMAC-SHA256 with 100 000 iterations.

Rate-limited to 10 req/min per IP (AUTH_LIMIT) — defined in rate_limiter.py.
"""

from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, field_validator

from backend.container import db
from backend.core.rate_limiter import AUTH_LIMIT, limiter
from backend.core.security import create_access_token

router = APIRouter(tags=["auth"])

# ── Request schema ─────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email:    EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("password must not be empty")
        return v


# ── Login endpoint ─────────────────────────────────────────────────────────

@router.post("/login")
@limiter.limit(AUTH_LIMIT)
async def login(request: Request, body: LoginRequest):
    """
    Validate email + password against the users table.

    Returns 401 with a generic message on any failure so that timing
    differences and error messages cannot be used to enumerate valid emails.
    """
    _invalid = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Single DB call — returns False for unknown email and wrong password alike.
    authenticated = db.verify_user_password(body.email, body.password)
    if not authenticated:
        raise _invalid

    # Fetch role for the token payload.
    user = db.get_user_by_email(body.email)
    if user is None:
        raise _invalid

    token = create_access_token(
        data={"sub": user.email, "role": user.role},
        expires_delta=timedelta(hours=8),
    )

    return {
        "access_token": token,
        "token_type":   "bearer",
        "user": {
            "email": user.email,
            "role":  user.role,
        },
    }
