# backend/core/rate_limiter.py
"""
Centralised rate-limiting configuration using slowapi.

Import ``limiter`` and apply it to routes with the @limiter.limit() decorator.
Attach it to the FastAPI app with:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)
"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# ── Limiter instance ────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)

# ── Limit presets ───────────────────────────────────────────────────────────
AUTH_LIMIT     = "10/minute"    # login endpoint — brute-force resistant
API_LIMIT      = "120/minute"   # standard API endpoints
ANALYSIS_LIMIT = "30/minute"    # /api/analyze-threat — ML inference is expensive
WS_LIMIT       = "5/minute"     # new WebSocket connections

# Re-export the default handler so app.py can register it without importing slowapi directly
rate_limit_exceeded_handler = _rate_limit_exceeded_handler
