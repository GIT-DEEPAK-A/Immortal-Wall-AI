# tests/test_response_engine.py
"""
Tests for the database-backed ResponseEngine.

Covers:
  - block_ip writes to BlockedIP table
  - unblock_ip sets unblocked_at
  - is_blocked uses the in-memory cache (no extra DB hit)
  - whitelisted IP is not blocked
  - execute_response for block_ip type
  - execute_response for alert type
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.database.db import DatabaseManager
from backend.services.response_engine import ResponseEngine


# ── Fixture: isolated ResponseEngine backed by in-memory DB ───────────────

@pytest.fixture
def engine():
    """Return a ResponseEngine that uses an in-memory SQLite database."""
    # Patch DatabaseManager inside ResponseEngine to use in-memory DB
    db = DatabaseManager(db_path=":memory:")

    re = ResponseEngine.__new__(ResponseEngine)
    re._db            = db
    re.whitelisted_ips = {"127.0.0.1", "::1", "10.0.0.1"}
    re.blocked_ips     = db.load_active_blocked_ips()   # empty set
    return re, db


# ═══════════════════════════════════════════════════════════════════════════
# Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestResponseEngine:

    def test_block_ip_writes_to_db(self, engine):
        """block_ip() must persist a BlockedIP record to the database."""
        re, db = engine
        re.block_ip("1.2.3.4", hard=True, reason="test block")

        records = db.get_blocked_ips(limit=10)
        assert any(r["ip"] == "1.2.3.4" for r in records), \
            "Expected 1.2.3.4 in blocked_ips table"

    def test_block_ip_updates_memory_cache(self, engine):
        """block_ip() must add the IP to the in-memory blocked_ips set."""
        re, db = engine
        re.block_ip("2.3.4.5", hard=True)
        assert "2.3.4.5" in re.blocked_ips

    def test_unblock_ip_sets_unblocked_at(self, engine):
        """unblock_ip() must set unblocked_at in the DB and remove from cache."""
        re, db = engine
        re.block_ip("3.4.5.6", hard=True)
        assert "3.4.5.6" in re.blocked_ips

        result = re.unblock_ip("3.4.5.6")
        assert result is True
        assert "3.4.5.6" not in re.blocked_ips

        # Verify the DB record has unblocked_at set
        records = db.get_blocked_ips(limit=10)
        record  = next((r for r in records if r["ip"] == "3.4.5.6"), None)
        assert record is not None
        assert record["unblocked_at"] is not None

    def test_is_blocked_uses_memory_cache(self, engine):
        """is_blocked() must reflect the in-memory set without DB calls."""
        re, db = engine
        assert re.is_blocked("9.9.9.9") is False
        re.blocked_ips.add("9.9.9.9")               # simulate cache only
        assert re.is_blocked("9.9.9.9") is True

    def test_whitelisted_ip_not_blocked(self, engine):
        """block_ip() must refuse to block a whitelisted IP."""
        re, db = engine
        result = re.block_ip("127.0.0.1", hard=True)
        assert "whitelisted" in result.lower()
        assert "127.0.0.1" not in re.blocked_ips

    def test_execute_response_block_type(self, engine):
        """execute_response with type=block_ip must block the IP."""
        re, db = engine
        config = {
            "type":   "block_ip",
            "ip":     "5.5.5.5",
            "reason": "automated block test",
            "hard":   True,
        }
        result = re.execute_response(config)
        assert result["success"] is True
        assert "5.5.5.5" in re.blocked_ips

    def test_execute_response_alert_type(self, engine):
        """execute_response with type=alert must write a CRITICAL log entry."""
        re, db = engine
        config = {
            "type":         "alert",
            "ip":           "6.6.6.6",
            "threat_level": "malicious",
            "reason":       "test alert",
        }
        result = re.execute_response(config)
        assert result["success"] is True

        # Verify a CRITICAL log entry was written
        logs = db.get_logs(limit=20, level="CRITICAL")
        assert any("6.6.6.6" in log["message"] for log in logs), \
            "Expected a CRITICAL log entry for the alert"

    def test_execute_response_unknown_type(self, engine):
        """execute_response with an unknown type must not crash."""
        re, db = engine
        config = {"type": "teleport", "ip": "7.7.7.7"}
        result = re.execute_response(config)
        assert result["success"] is False
        assert "Unknown" in result["details"]

    def test_soft_block_uses_false_hard_flag(self, engine):
        """apply_soft_block() must set hard_block=False in the DB."""
        re, db = engine
        re.apply_soft_block("8.8.8.8", duration=10)
        records = db.get_blocked_ips(limit=10)
        record  = next((r for r in records if r["ip"] == "8.8.8.8"), None)
        assert record is not None
        assert record["hard_block"] is False

    def test_execute_response_isolate_type(self, engine):
        """execute_response with type=isolate must block AND alert."""
        re, db = engine
        config = {
            "type":         "isolate",
            "ip":           "11.11.11.11",
            "threat_level": "malicious",
            "reason":       "isolation test",
        }
        result = re.execute_response(config)
        assert result["success"] is True
        assert "11.11.11.11" in re.blocked_ips
        logs = db.get_logs(limit=20, level="CRITICAL")
        assert any("11.11.11.11" in log["message"] for log in logs)
