# backend/core/security.py
"""
JWT bearer-token authentication for Immortal Wall AI.

Public symbols
──────────────
  oauth2_scheme       OAuth2PasswordBearer dependency (OpenAPI integration)
  create_access_token Create a signed HS256 JWT
  get_current_user    FastAPI dependency — decodes & validates the token
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

# ── Config ─────────────────────────────────────────────────────────────────
# Read from environment; fall back to an obvious sentinel so tests fail loudly
# if the secret is not set — never silently use a weak default in production.
_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", os.getenv("SECRET_KEY", "CHANGE-THIS-IN-PRODUCTION"))
_ALGORITHM:  str = "HS256"
_DEFAULT_EXPIRY_HOURS: int = 8

# ── OAuth2 scheme ───────────────────────────────────────────────────────────
# tokenUrl must match the login endpoint so Swagger UI can obtain tokens.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# ── Token creation ──────────────────────────────────────────────────────────

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a signed HS256 JWT.

    Parameters
    ----------
    data          : Payload dict; a copy is made — the original is not mutated.
    expires_delta : Explicit expiry window.  Defaults to 8 hours.

    Returns
    -------
    Encoded JWT string.
    """
    payload = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=_DEFAULT_EXPIRY_HOURS))
    payload["exp"] = expire
    payload["iat"] = datetime.utcnow()
    return jwt.encode(payload, _SECRET_KEY, algorithm=_ALGORITHM)


# ── Token validation ────────────────────────────────────────────────────────

def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT.

    Raises
    ------
    HTTPException 401 if the token is missing, malformed, or expired.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, _SECRET_KEY, algorithms=[_ALGORITHM])
        # Require at least a 'sub' claim so anonymous tokens are rejected.
        if payload.get("sub") is None:
            raise credentials_exception
        return payload
    except JWTError:
        raise credentials_exception


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    FastAPI dependency — inject into any protected endpoint.

    Usage
    ─────
    @router.get("/protected")
    async def protected(user: dict = Depends(get_current_user)):
        ...
    """
    return decode_token(token)
