"""
backend/schemas.py
───────────────────
Pydantic request/response schemas for all public endpoints.

All inbound payloads are validated here before reaching services.
Using strict typing prevents type-coercion surprises and gives FastAPI
enough information to generate accurate OpenAPI docs.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
import re

# ── Reusable validators ────────────────────────────────────────────────────

_IPV4_RE = re.compile(
    r"^(\d{1,3}\.){3}\d{1,3}$"
)
_IPV6_RE = re.compile(
    r"^([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}$"
)

def _is_valid_ip(v: str) -> bool:
    return bool(_IPV4_RE.match(v) or _IPV6_RE.match(v) or v in ("unknown", "localhost"))


# ── Threat event (used by /api/analyze-threat and /api/status/event) ───────

class ThreatFlagsSchema(BaseModel):
    """Optional pre-computed threat flags from the agent."""
    failed_login:            bool = False
    high_request_rate:       bool = False
    suspicious_ip_activity:  bool = False


class ThreatEventSchema(BaseModel):
    """
    Validated inbound event for threat analysis.

    All fields are optional — the engine degrades gracefully on missing data.
    Constraints prevent obviously malformed inputs from reaching the ML pipeline.
    """
    # Identity
    ip:           str  = Field(default="unknown", max_length=45)
    ip_address:   Optional[str] = Field(default=None, max_length=45)  # alias accepted
    username:     Optional[str] = Field(default=None, max_length=255)

    # Request info
    event_type:   Optional[str] = Field(default=None, max_length=50)
    status:       Optional[str] = Field(default=None, max_length=20)
    method:       Optional[str] = Field(default="GET", max_length=10)
    path:         Optional[str] = Field(default=None, max_length=2048)
    response_code: Optional[int] = Field(default=200, ge=100, le=599)

    # Payload
    payload:        Optional[str]   = Field(default=None, max_length=65_536)
    payload_length: Optional[float] = Field(default=0.0, ge=0)

    # Behavioural signals
    request_rate:    Optional[float] = Field(default=0.0, ge=0)
    failed_logins:   Optional[int]   = Field(default=0,   ge=0, le=10_000)
    distinct_paths:  Optional[int]   = Field(default=0,   ge=0)
    session_duration: Optional[float] = Field(default=0.0, ge=0)

    # Identity enrichment
    user_agent:   Optional[str] = Field(default=None, max_length=1024)
    port:         Optional[int] = Field(default=None, ge=1, le=65535)

    # Timestamps & source
    timestamp:    Optional[float] = Field(default=None)
    source:       Optional[str]   = Field(default="api", max_length=50)
    attack_type:  Optional[str]   = Field(default=None, max_length=50)

    # Pre-computed flags from the agent
    threat_flags: ThreatFlagsSchema = Field(default_factory=ThreatFlagsSchema)

    # Pass-through data blob
    data:         Optional[Dict[str, Any]] = Field(default=None)

    @field_validator("ip", "ip_address", mode="before")
    @classmethod
    def validate_ip(cls, v):
        if v is None:
            return v
        s = str(v).strip()
        if s and not _is_valid_ip(s):
            # Sanitise but don't reject — log the anomaly
            return "unknown"
        return s

    @field_validator("method", mode="before")
    @classmethod
    def normalise_method(cls, v):
        if v is None:
            return "GET"
        return str(v).upper()[:10]

    @model_validator(mode="after")
    def resolve_ip_alias(self) -> "ThreatEventSchema":
        """Allow callers that send ip_address instead of ip."""
        if self.ip == "unknown" and self.ip_address:
            self.ip = self.ip_address
        return self

    model_config = {"extra": "ignore"}   # silently drop unknown keys


# ── Raw agent / honeypot event (used by POST /api/status/event) ────────────

class RawEventSchema(BaseModel):
    """
    Minimal schema for events POSTed by the agent or honeypot.
    Less strict than ThreatEventSchema — the engine tolerates missing fields.
    """
    ip:           Optional[str]   = Field(default="unknown", max_length=45)
    event_type:   Optional[str]   = Field(default=None,      max_length=50)
    status:       Optional[str]   = Field(default=None,      max_length=20)
    username:     Optional[str]   = Field(default=None,      max_length=255)
    timestamp:    Optional[float] = Field(default=None)
    source:       Optional[str]   = Field(default="agent",   max_length=50)
    threat_flags: Optional[Dict[str, bool]] = Field(default=None)

    # Allow extra fields so agent events with custom keys pass through.
    model_config = {"extra": "allow"}
