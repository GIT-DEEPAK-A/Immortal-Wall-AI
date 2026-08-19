# tests/test_backend.py
"""
Backend unit tests.

Covers:
  - AdvancedMLEngine  (feature extraction, prediction, batch, heuristic)
  - RuleEngine        (individual rule firings)
  - ThreatEngine      (fusion weights, response actions)
  - DatabaseManager   (via repository layer)
  - Performance benchmarks
"""

import os
import sys
import time
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.services.ml_engine import (
    AdvancedMLEngine,
    FeatureExtractor,
    N_FEATURES,
    FEATURE_NAMES,
    generate_training_data,
)
from backend.services.rule_engine import evaluate_rules, classify_attack_type
from backend.services.threat_engine import ThreatEngine
from backend.database.db import DatabaseManager


# ═══════════════════════════════════════════════════════════════════════════
# TestAdvancedMLEngine
# ═══════════════════════════════════════════════════════════════════════════

class TestAdvancedMLEngine:
    """Tests for AdvancedMLEngine and FeatureExtractor."""

    def setup_method(self):
        self.ml_engine = AdvancedMLEngine()
        self.extractor = FeatureExtractor()

    # ── Feature extraction ─────────────────────────────────────────────────

    def test_extract_features_length(self):
        """Feature vector must have exactly 18 elements."""
        event = {
            "ip": "192.168.1.100",
            "threat_flags": {
                "failed_login": True,
                "high_request_rate": False,
                "suspicious_ip_activity": True,
            },
            "user_agent": "Mozilla/5.0 (compatible; Nmap Scripting Engine)",
            "timestamp": int(datetime.now().timestamp()),
        }
        features = self.extractor.extract(event)
        assert len(features) == 18

    def test_extract_features_returns_zero_vector_on_bad_input(self):
        """Malformed event must return a zero-vector of length 18."""
        import numpy as np
        vec = self.extractor.extract({"timestamp": "not-a-number"})
        assert len(vec) == 18
        assert all(v == 0.0 for v in vec)

    def test_extract_features_binary_flags(self):
        """Binary flag features map correctly."""
        event = {
            "threat_flags": {
                "failed_login":           True,
                "high_request_rate":      False,
                "suspicious_ip_activity": True,
            },
        }
        features = self.extractor.extract(event)
        assert features[0] == 1.0   # failed_login
        assert features[1] == 0.0   # high_request_rate
        assert features[2] == 1.0   # suspicious_ip

    def test_extract_features_nmap_ua_detected(self):
        """Nmap user-agent must set is_suspicious_ua (index 15)."""
        event = {"user_agent": "Nmap Scripting Engine"}
        features = self.extractor.extract(event)
        assert features[15] == 1.0

    def test_ml_engine_has_model(self):
        """Engine must load or train a model at construction time."""
        assert self.ml_engine.model is not None


# ═══════════════════════════════════════════════════════════════════════════
# TestMLEngine  (predict / batch)
# ═══════════════════════════════════════════════════════════════════════════

class TestMLEngine:
    """Tests for AdvancedMLEngine.predict() and predict_batch()."""

    def setup_method(self):
        self.engine = AdvancedMLEngine()

    def _brute_force_event(self):
        return {
            "ip": "195.154.92.47",
            "event_type": "login",
            "status": "failed",
            "failed_logins": 20,
            "request_rate": 15.0,
            "user_agent": "sqlmap/1.7",
            "threat_flags": {
                "failed_login": True,
                "high_request_rate": True,
                "suspicious_ip_activity": True,
            },
            "timestamp": int(datetime.now().timestamp()),
        }

    def _normal_event(self):
        return {
            "ip": "10.0.0.5",
            "event_type": "request",
            "status": "success",
            "failed_logins": 0,
            "request_rate": 0.5,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "threat_flags": {
                "failed_login": False,
                "high_request_rate": False,
                "suspicious_ip_activity": False,
            },
            "timestamp": int(datetime.now().timestamp()),
        }

    def test_predict_returns_required_keys(self):
        """predict() must return all seven required keys."""
        result = self.engine.predict(self._normal_event())
        for key in ("ml_score", "ml_level", "confidence", "ml_reason",
                    "probabilities", "feature_values", "attribution"):
            assert key in result, f"Missing key: {key}"

    def test_predict_brute_force_is_malicious(self):
        """A strong brute-force event must be classified as suspicious or malicious."""
        result = self.engine.predict(self._brute_force_event())
        assert result["ml_level"] in ("suspicious", "malicious")
        assert result["ml_score"] > 0.3

    def test_predict_normal_is_normal(self):
        """Normal traffic must be classified as normal."""
        result = self.engine.predict(self._normal_event())
        assert result["ml_level"] == "normal"
        assert result["ml_score"] < 0.5

    def test_predict_probabilities_sum_to_one(self):
        """Class probabilities must sum to approximately 1.0."""
        result = self.engine.predict(self._normal_event())
        probs  = result["probabilities"]
        total  = probs["normal"] + probs["suspicious"] + probs["malicious"]
        assert abs(total - 1.0) < 0.01

    def test_predict_feature_values_count(self):
        """feature_values dict must contain exactly 18 entries."""
        result = self.engine.predict(self._normal_event())
        assert len(result["feature_values"]) == 18

    def test_batch_predict_matches_individual(self):
        """Batch prediction must return the same count as input events."""
        events  = [self._brute_force_event(), self._normal_event(), self._brute_force_event()]
        results = self.engine.predict_batch(events)
        assert len(results) == len(events)
        for r in results:
            assert "ml_level" in r
            assert "ml_score" in r

    def test_drift_detection_properties(self):
        """drift_detected and recent_threat_rate must be accessible."""
        assert isinstance(self.engine.drift_detected, bool)
        assert isinstance(self.engine.recent_threat_rate, float)
        assert 0.0 <= self.engine.recent_threat_rate <= 1.0

    def test_compute_drift_score_empty(self):
        """compute_drift_score() on fresh engine returns 0.0."""
        fresh = AdvancedMLEngine.__new__(AdvancedMLEngine)
        from collections import deque
        fresh._recent_levels        = deque(maxlen=1000)
        fresh._drift_detected       = False
        fresh._high_threat_streak   = 0
        assert fresh.compute_drift_score() == 0.0


# ═══════════════════════════════════════════════════════════════════════════
# TestRuleEngine
# ═══════════════════════════════════════════════════════════════════════════

class TestRuleEngine:
    """Tests for the deterministic rule engine."""

    def test_sql_injection_fires(self):
        """SQL injection payload must raise a non-zero rule score."""
        event = {
            "payload": "' OR '1'='1",
            "path":    "/login",
            "method":  "POST",
        }
        score, flags, reason = evaluate_rules(event)
        assert score > 0
        assert "sql_injection" in reason

    def test_brute_force_fires(self):
        """Multiple failed logins must trigger the brute_force rule."""
        event = {
            "event_type":   "login",
            "status":       "failed",
            "failed_logins": 10,
            "threat_flags": {"failed_login": True},
        }
        score, flags, reason = evaluate_rules(event)
        assert score > 0
        assert "brute_force" in reason

    def test_http_flood_fires(self):
        """Very high request rate must trigger the http_flood rule."""
        event = {"request_rate": 100.0}
        score, flags, reason = evaluate_rules(event)
        assert score > 0
        assert "flood" in reason.lower()

    def test_known_bad_ip_fires(self):
        """A known-bad IP must trigger the known_bad_ip rule."""
        event = {"ip": "195.154.92.47"}
        score, flags, reason = evaluate_rules(event)
        assert score >= 0.9
        assert "known_bad_ip" in reason

    def test_normal_traffic_score_zero(self):
        """Benign traffic from an internal IP must score zero."""
        # Use a fixed midday timestamp (12:00 UTC on a weekday) to avoid
        # off-hours (+0.20) and weekend rules that would inflate the score.
        import calendar
        # Monday 2024-01-15 12:00:00 UTC
        noon_monday = calendar.timegm((2024, 1, 15, 12, 0, 0, 0, 0, 0))
        event = {
            "ip":            "10.0.0.1",
            "event_type":    "request",
            "status":        "success",
            "request_rate":  0.5,
            "failed_logins": 0,
            "user_agent":    "Mozilla/5.0 (Windows NT 10.0)",
            "path":          "/index.html",
            "payload":       "",
            "threat_flags":  {},
            "timestamp":     noon_monday,
        }
        score, flags, reason = evaluate_rules(event)
        assert score == 0.0
        assert reason == "normal behavior"

    def test_score_capped_at_one(self):
        """Combined rule score must never exceed 1.0."""
        event = {
            "ip":             "195.154.92.47",
            "event_type":     "login",
            "status":         "failed",
            "failed_logins":  50,
            "request_rate":   500.0,
            "payload":        "' OR '1'='1; DROP TABLE users;--",
            "user_agent":     "sqlmap/1.7",
            "path":           "/admin",
            "threat_flags":   {
                "failed_login": True,
                "high_request_rate": True,
                "suspicious_ip_activity": True,
            },
        }
        score, _, _ = evaluate_rules(event)
        assert score <= 1.0

    def test_classify_sql_injection(self):
        """classify_attack_type must return sql_injection for SQLi payload."""
        event = {"payload": "' OR 1=1--", "path": "/login"}
        assert classify_attack_type(event) == "sql_injection"

    def test_classify_ddos(self):
        """classify_attack_type must return ddos for high request rate."""
        event = {"request_rate": 200.0}
        assert classify_attack_type(event) == "ddos"


# ═══════════════════════════════════════════════════════════════════════════
# TestThreatEngine
# ═══════════════════════════════════════════════════════════════════════════

class TestThreatEngine:
    """Tests for the ThreatEngine fusion layer."""

    def setup_method(self):
        self.engine = ThreatEngine()

    def test_fusion_weights(self):
        """
        Rule weight = 0.40, ML weight = 0.60.
        Verify with a synthetic event where we can bound both sub-scores.
        """
        # A known-bad IP with SQL injection gives rule_score >= 0.9.
        # With fusion: final >= 0.4 * 0.9 = 0.36; plus ML contribution.
        event = {
            "ip":      "195.154.92.47",
            "payload": "' OR '1'='1",
            "path":    "/login",
        }
        result = self.engine.analyze_event(event)
        assert "rule_score" in result
        assert "ml_score" in result
        # Final score must be between the two sub-scores (weighted average)
        rs = result["rule_score"]
        ms = result["ml_score"]
        expected_approx = 0.40 * rs + 0.60 * ms
        assert abs(result["threat_score"] - expected_approx) < 0.001

    def test_malicious_triggers_block(self):
        """A malicious verdict must include a block_ip response action."""
        event = {
            "ip":            "195.154.92.47",
            "event_type":    "login",
            "status":        "failed",
            "failed_logins": 25,
            "request_rate":  60.0,
            "user_agent":    "sqlmap/1.7",
            "threat_flags":  {
                "failed_login": True,
                "high_request_rate": True,
                "suspicious_ip_activity": True,
            },
        }
        result = self.engine.analyze_event(event)
        if result["threat_level"] == "malicious":
            action_types = [a["type"] for a in result.get("response_actions", [])]
            assert "block_ip" in action_types

    def test_normal_no_response_action(self):
        """Normal traffic must have no response actions."""
        event = {
            "ip":           "10.0.0.5",
            "event_type":   "request",
            "status":       "success",
            "request_rate": 0.5,
            "failed_logins": 0,
            "user_agent":   "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "threat_flags": {},
        }
        result = self.engine.analyze_event(event)
        if result["threat_level"] == "normal":
            assert result.get("response_actions", []) == []

    def test_analyze_threat_alias_works(self):
        """analyze_threat() must return the same structure as analyze_event()."""
        event = {"ip": "10.0.0.1", "event_type": "request", "status": "success"}
        result_event  = self.engine.analyze_event(event.copy())
        result_threat = self.engine.analyze_threat(event.copy())
        for key in ("threat_level", "threat_score", "rule_score", "ml_score"):
            assert key in result_event
            assert key in result_threat


# ═══════════════════════════════════════════════════════════════════════════
# TestDatabaseManager  (via repository layer)
# ═══════════════════════════════════════════════════════════════════════════

class TestDatabaseManager:
    """Integration tests for DatabaseManager and its repository delegates."""

    def setup_method(self):
        self.db = DatabaseManager(db_path=":memory:")

    def test_health_check_healthy(self):
        health = self.db.health_check()
        assert health["status"] == "healthy"
        assert health["connection"] == "ok"

    def test_store_and_retrieve_threat(self):
        """store_threat_analysis then get_threats returns the record."""
        threat_data = {
            "ip_address":   "192.168.1.100",
            "threat_level": "malicious",
            "threat_score": 0.95,
            "confidence":   0.88,
            "threat_type":  "brute_force",
            "description":  "Multiple failed login attempts",
            "blocked":      True,
            "source":       "honeypot",
        }
        ok = self.db.store_threat_analysis(threat_data)
        assert ok is True

        threats = self.db.get_threats(limit=10)
        assert len(threats) >= 1
        threat = threats[0]
        assert threat["ip_address"]   == "192.168.1.100"
        assert threat["threat_level"] == "malicious"
        assert threat["blocked"]      is True

    def test_threat_statistics(self):
        """get_threat_statistics returns correct aggregates."""
        for ip, level, blocked in [
            ("1.1.1.1", "malicious",  True),
            ("2.2.2.2", "suspicious", False),
            ("3.3.3.3", "normal",     False),
        ]:
            self.db.store_threat_analysis({
                "ip_address": ip, "threat_level": level,
                "threat_score": 0.5, "blocked": blocked,
            })

        stats = self.db.get_threat_statistics()
        assert stats["total_threats"] >= 3
        assert "malicious"  in stats["threat_levels"]
        assert "suspicious" in stats["threat_levels"]
        assert "normal"     in stats["threat_levels"]
        assert stats["blocked_threats"] >= 1

    def test_store_and_retrieve_log(self):
        """store_log_entry then get_logs returns the entry."""
        ok = self.db.store_log_entry("WARNING", "test", "unit test log", {"key": "val"})
        assert ok is True
        logs = self.db.get_logs(limit=10)
        assert any(log["message"] == "unit test log" for log in logs)

    def test_create_and_verify_user(self):
        """create_user and verify_user_password work end-to-end."""
        ok = self.db.create_user("tester@example.com", "secret123", "Analyst")
        assert ok is True
        assert self.db.verify_user_password("tester@example.com", "secret123") is True
        assert self.db.verify_user_password("tester@example.com", "wrongpass") is False

    def test_block_and_unblock_ip(self):
        """block_ip_in_db and unblock_ip_in_db work correctly."""
        self.db.block_ip_in_db("10.0.0.99", hard_block=True, reason="test block")
        active = self.db.load_active_blocked_ips()
        assert "10.0.0.99" in active

        ok = self.db.unblock_ip_in_db("10.0.0.99")
        assert ok is True
        active_after = self.db.load_active_blocked_ips()
        assert "10.0.0.99" not in active_after


# ═══════════════════════════════════════════════════════════════════════════
# Performance Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestPerformance:
    """Light performance benchmarks — ensure no catastrophic regressions."""

    def setup_method(self):
        self.ml_engine = AdvancedMLEngine()
        self.db        = DatabaseManager(db_path=":memory:")

    def test_ml_prediction_performance(self):
        """100 predictions must complete in under 120 s total (calibrated ensemble on CPU)."""
        event = {
            "ip":           "10.0.0.1",
            "threat_flags": {"failed_login": False, "high_request_rate": False},
            "user_agent":   "Mozilla/5.0",
            "timestamp":    int(datetime.now().timestamp()),
        }
        start = time.time()
        for _ in range(100):
            self.ml_engine.predict(event)
        elapsed = time.time() - start
        assert elapsed < 120.0, f"100 predictions took {elapsed:.2f}s -- too slow"

    def test_database_insert_performance(self):
        """100 DB inserts must complete in under 5 s total."""
        start = time.time()
        for i in range(100):
            self.db.store_threat_analysis({
                "ip_address":   f"10.0.0.{i % 254 + 1}",
                "threat_level": "normal",
                "threat_score": 0.1,
            })
        elapsed = time.time() - start
        assert elapsed < 5.0, f"100 DB inserts took {elapsed:.2f}s — too slow"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
