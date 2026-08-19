# tests/test_auth.py
"""
Tests for email+password JWT authentication flow.

Covers:
  - Correct credentials return 200 + access_token
  - Wrong credentials return 401 (never 200 with success=False)
  - Missing body → 422
  - Protected endpoint without token → 401
  - Protected endpoint with valid token → 200
  - Protected endpoint with expired token → 401
  - WebSocket without token closes with code 1008
"""

import os
import sys
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Set JWT secret before any backend imports so tokens are predictable.
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-unit-tests")

from backend.app import app
from backend.core.security import create_access_token
from backend.database.db import DatabaseManager

# ── Isolated in-memory DatabaseManager used for auth tests ────────────────
# We do NOT mutate os.environ["DATABASE_URL"] because backend.container is
# already imported (module-level singleton). Instead we build a fresh
# in-memory db, seed the test user into it, and monkey-patch backend.container
# and backend.routes.auth_routes to use it for the duration of these tests.

_TEST_DB = DatabaseManager(db_path=":memory:")
_TEST_DB.create_user("analyst@immortalwall.ai", "test-password-123", "Admin")


def _patch_db(monkeypatch):
    """Replace the shared db singleton with the in-memory test db."""
    import backend.container as _c
    import backend.routes.auth_routes as _ar
    monkeypatch.setattr(_c,  "db", _TEST_DB)
    monkeypatch.setattr(_ar, "db", _TEST_DB)


# ── Helpers ────────────────────────────────────────────────────────────────

def _valid_token() -> str:
    return create_access_token(
        {"sub": "analyst@immortalwall.ai", "role": "Admin"},
        expires_delta=timedelta(hours=8),
    )


def _expired_token() -> str:
    return create_access_token(
        {"sub": "analyst@immortalwall.ai", "role": "Admin"},
        expires_delta=timedelta(seconds=-1),
    )


# ── Login endpoint tests ───────────────────────────────────────────────────

class TestLoginEndpoint:
    def test_login_correct_passkey(self, monkeypatch):
        """Correct email+password → 200, access_token present."""
        import backend.container as _c
        monkeypatch.setattr(_c.db, "verify_user_password", lambda e, p: True)
        # Minimal user object with .email and .role attributes
        from types import SimpleNamespace
        fake_user = SimpleNamespace(email="analyst@immortalwall.ai", role="Admin")
        monkeypatch.setattr(_c.db, "get_user_by_email", lambda e: fake_user)
        res = client.post("/api/auth/login", json={
            "email":    "analyst@immortalwall.ai",
            "password": "test-password-123",
        })
        assert res.status_code == 200, res.text
        body = res.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert len(body["access_token"]) > 20

    def test_login_wrong_passkey(self, monkeypatch):
        """Wrong password → 401, no access_token."""
        import backend.container as _c
        monkeypatch.setattr(_c.db, "verify_user_password", lambda e, p: False)
        res = client.post("/api/auth/login", json={
            "email":    "analyst@immortalwall.ai",
            "password": "totally-wrong",
        })
        assert res.status_code == 401
        assert "access_token" not in res.json()

    def test_login_missing_body(self):
        """Missing body → 422 validation error."""
        res = client.post("/api/auth/login", json={})
        assert res.status_code == 422


# ── Protected endpoint tests ───────────────────────────────────────────────

client = TestClient(app, raise_server_exceptions=False)


class TestProtectedEndpoints:
    def test_protected_endpoint_no_token(self):
        """GET /api/system-status without token → 401."""
        res = client.get("/api/system-status")
        assert res.status_code == 401

    def test_protected_endpoint_valid_token(self, monkeypatch):
        """GET /api/system-status with valid token → 200."""
        import backend.container as _c
        # Stub out the DB calls that system-status makes
        monkeypatch.setattr(_c.db, "get_threat_statistics", lambda: {
            "total_threats": 0, "threat_levels": {}, "threat_types": {},
            "recent_threats_24h": 0, "blocked_threats": 0,
            "average_threat_score": 0.0, "ml_predictions": 0,
        })
        monkeypatch.setattr(_c.db, "get_recent_threats", lambda limit=5: [])
        token = _valid_token()
        res = client.get(
            "/api/system-status",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200

    def test_protected_endpoint_expired_token(self):
        """GET /api/system-status with expired token → 401."""
        token = _expired_token()
        res = client.get(
            "/api/system-status",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 401

    def test_logs_no_token(self):
        """GET /api/logs without token → 401."""
        assert client.get("/api/logs").status_code == 401

    def test_threats_no_token(self):
        """GET /api/threats without token → 401."""
        assert client.get("/api/threats").status_code == 401

    def test_analytics_no_token(self):
        """GET /api/analytics without token → 401."""
        assert client.get("/api/analytics").status_code == 401

    def test_health_is_public(self):
        """GET /api/health is public — no token required."""
        assert client.get("/api/health").status_code == 200


# ── WebSocket auth tests ───────────────────────────────────────────────────

class TestWebSocketAuth:
    def test_ws_connection_no_token(self):
        """WebSocket without token parameter → closed with code 1008."""
        try:
            with client.websocket_connect("/ws") as ws:
                ws.receive_text()
                pytest.fail("Expected WebSocket to be closed with 1008")
        except Exception as exc:
            code = getattr(exc, "code", None)
            assert code == 1008, f"Expected 1008, got {code} ({exc!r})"

    def test_ws_connection_valid_token(self):
        """WebSocket with valid token → connection accepted."""
        token = _valid_token()
        with client.websocket_connect(f"/ws?token={token}") as ws:
            ws.send_text("ping")

    def test_ws_connection_invalid_token(self):
        """WebSocket with garbage token → closed with code 1008."""
        try:
            with client.websocket_connect("/ws?token=this.is.garbage") as ws:
                ws.receive_text()
                pytest.fail("Expected WebSocket to be closed with 1008")
        except Exception as exc:
            code = getattr(exc, "code", None)
            assert code == 1008, f"Expected 1008, got {code} ({exc!r})"
