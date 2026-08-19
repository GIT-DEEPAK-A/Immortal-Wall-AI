# backend/routes/auth_routes.py
# Simple passkey authentication — no OTP, no registration.
# The system passkey is 123456 (configured in SYSTEM_PASSKEY env var).

import os
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["auth"])

SYSTEM_PASSKEY = os.getenv("SYSTEM_PASSKEY", "123456")


class PasskeyRequest(BaseModel):
    passkey: str


@router.post("/login")
async def login(request: PasskeyRequest):
    """
    Validate the system passkey.
    Returns 200 on success, 401 on failure.
    """
    if request.passkey == SYSTEM_PASSKEY:
        return {
            "success": True,
            "message": "Access granted",
            "user": {
                "name": "Security Analyst",
                "role": "Admin",
            },
        }
    return {
        "success": False,
        "message": "Invalid passkey",
    }
