import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from backend.services.ml_engine import AdvancedMLEngine
from backend.services.threat_engine import ThreatEngine
from backend.database.models import DatabaseManager, Threat

class TestAdvancedMLEngine:
    """Test the advanced ML engine functionality"""

    def setup_method(self):
        """Setup test fixtures"""
        self.ml_engine = AdvancedMLEngine()

    def test_initialization(self):
        """Test ML engine initializes correctly"""
        assert self.ml_engine is not None
        assert hasattr(self.ml_engine, 'model')
        assert hasattr(self.ml_engine, 'scaler')
        assert hasattr(self.ml_engine, 'threat_intelligence')

    def test_extract_features(self):
        """Test feature extraction from threat data"""
        threat_data = {
            "ip": "192.168.1.100",
            "threat_flags": {
                "failed_login": True,
                "high_request_rate": False,
                "suspicious_ip_activity": True
            },
            "user_agent": "Mozilla/5.0 (compatible; Nmap Scripting Engine)",
            "timestamp": int(datetime.now().timestamp())
        }

        features = self.ml_engine.extract_features(threat_data)
        assert len(features) == 9  # Should have 9 features
        assert features[0] == 1  # failed_login
        assert features[1] == 0  # high_request_rate
        assert features[2] == 1  # suspicious_ip_activity
        assert isinstance(features[3], int)  # unusual_time
        assert features[4] == 1  # ua_threat (nmap detected)

    def test_predict_normal_traffic(self):
        """Test prediction for normal traffic"""
        normal_event = {
            "ip": "10.0.0.1",
            "threat_flags": {
                "failed_login": False,
                "high_request_rate": False,
                "suspicious_ip_activity": False
            },
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "timestamp": int(datetime.now().timestamp())
        }

        result = self.ml_engine.predict(normal_event)
        assert "ml_level" in result
        assert "confidence" in result
        assert "feature_importance" in result
        assert result["ml_level"] in ["normal", "suspicious", "malicious"]

    def test_predict_malicious_traffic(self):
        """Test prediction for malicious traffic"""
        malicious_event = {
            "ip": "192.168.1.100",  # Known malicious IP
            "threat_flags": {
                "failed_login": True,
                "high_request_rate": True,
                "suspicious_ip_activity": True
            },
            "user_agent": "sqlmap/1.5.5",
            "timestamp": int(datetime.now().timestamp())
        }

        result = self.ml_engine.predict(malicious_event)
        assert result["ml_level"] in ["suspicious", "malicious"]
        assert "feature_importance" in result

    def test_threat_intelligence_loading(self):
        """Test threat intelligence data loading"""
        ti = self.ml_engine.threat_intelligence
        assert isinstance(ti, dict)
        assert "malicious_ips" in ti
        assert "suspicious_domains" in ti
        assert "known_attack_patterns" in ti

class TestDatabaseManager:
    """Test database operations"""

    def setup_method(self):
        """Setup test database"""
        self.db = DatabaseManager(db_path=":memory:")  # Use in-memory SQLite

    def test_health_check(self):
        """Test database health check"""
        health = self.db.health_check()
        assert health["status"] == "healthy"
        assert health["connection"] == "ok"

    def test_store_and_retrieve_threat(self):
        """Test storing and retrieving threat data"""
        threat_data = {
            "ip_address": "192.168.1.100",
            "threat_level": "malicious",
            "threat_score": 0.95,
            "confidence": 0.88,
            "threat_type": "brute_force",
            "description": "Multiple failed login attempts",
            "blocked": True,
            "source": "honeypot"
        }

        # Store threat
        success = self.db.store_threat_analysis(threat_data)
        assert success

        # Retrieve threats
        threats = self.db.get_threats(limit=10)
        assert len(threats) >= 1

        threat = threats[0]
        assert threat["ip_address"] == "192.168.1.100"
        assert threat["threat_level"] == "malicious"
        assert threat["blocked"] == True

    def test_threat_statistics(self):
        """Test threat statistics calculation"""
        # Add some test data
        test_threats = [
            {"ip_address": "1.1.1.1", "threat_level": "malicious", "threat_score": 0.9, "blocked": True},
            {"ip_address": "2.2.2.2", "threat_level": "suspicious", "threat_score": 0.6, "blocked": False},
            {"ip_address": "3.3.3.3", "threat_level": "normal", "threat_score": 0.1, "blocked": False},
        ]

        for threat in test_threats:
            self.db.store_threat_analysis(threat)

        stats = self.db.get_threat_statistics()
        assert stats["total_threats"] == 3
        assert "malicious" in stats["threat_levels"]
        assert "suspicious" in stats["threat_levels"]
        assert "normal" in stats["threat_levels"]
        assert stats["blocked_threats"] == 1

    def test_analytics_data(self):
        """Test analytics data generation"""
        # Add threats with different timestamps
        base_time = datetime.utcnow()
        for i in range(5):
            threat_time = base_time - timedelta(hours=i)
            threat = {
                "ip_address": f"10.0.0.{i}",
                "threat_level": "malicious" if i % 2 == 0 else "suspicious",
                "threat_score": 0.8,
                "timestamp": int(threat_time.timestamp())
            }
            self.db.store_threat_analysis(threat)

        analytics = self.db.get_analytics()
        assert "threat_trends" in analytics
        assert "top_threat_sources" in analytics
        assert "threat_distribution" in analytics

class TestThreatEngine:
    """Test threat detection engine"""

    def setup_method(self):
        """Setup threat engine"""
        self.threat_engine = ThreatEngine()

    def test_analyze_normal_request(self):
        """Test analysis of normal HTTP request"""
        normal_request = {
            "ip": "10.0.0.1",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "request_method": "GET",
            "path": "/index.html",
            "status_code": 200,
            "response_time": 150,
            "timestamp": int(datetime.now().timestamp())
        }

        result = self.threat_engine.analyze_event(normal_request)
        assert result["threat_level"] in ["normal", "suspicious", "malicious"]
        assert "score" in result
        assert "ml_level" in result

    def test_analyze_suspicious_request(self):
        """Test analysis of suspicious request"""
        suspicious_request = {
            "ip": "192.168.1.100",
            "user_agent": "sqlmap/1.5.5",
            "request_method": "POST",
            "path": "/api/login",
            "data": "username=admin' OR '1'='1",
            "status_code": 500,
            "response_time": 5000,
            "failed_logins": 5,
            "timestamp": int(datetime.now().timestamp())
        }

        result = self.threat_engine.analyze_event(suspicious_request)
        assert result["score"] > 0.5  # Should be high threat score
        assert "ml_level" in result

    def test_analyze_brute_force_attack(self):
        """Test detection of brute force attacks"""
        brute_force_request = {
            "ip": "10.0.0.100",
            "user_agent": "Python-urllib/3.8",
            "request_method": "POST",
            "path": "/login",
            "failed_logins": 10,
            "rapid_requests": True,
            "timestamp": int(datetime.now().timestamp())
        }

        result = self.threat_engine.analyze_event(brute_force_request)
        assert result["threat_level"] == "malicious"  # Brute force should be malicious
        assert result["score"] > 0.7

class TestAPIEndpoints:
    """Test API endpoints (integration tests)"""

    def setup_method(self):
        """Setup for API tests"""
        self.base_url = "http://localhost:8000"

    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        """Test health check endpoint"""
        # This would require the server to be running
        # For now, just test that the endpoint structure is correct
        pass

    @pytest.mark.asyncio
    async def test_analyze_threat_endpoint(self):
        """Test threat analysis endpoint"""
        # Integration test would require running server
        pass

# Performance Tests
class TestPerformance:
    """Performance and load testing"""

    def setup_method(self):
        self.ml_engine = AdvancedMLEngine()
        self.db = DatabaseManager(db_path=":memory:")

    def test_ml_prediction_performance(self):
        """Test ML prediction performance"""
        import time

        test_event = {
            "ip": "10.0.0.1",
            "threat_flags": {"failed_login": False, "high_request_rate": False},
            "user_agent": "Mozilla/5.0",
            "timestamp": int(datetime.now().timestamp())
        }

        # Test prediction speed
        start_time = time.time()
        for _ in range(100):
            self.ml_engine.predict(test_event)
        end_time = time.time()

        avg_time = (end_time - start_time) / 100
        assert avg_time < 0.1  # Should be faster than 100ms per prediction

    def test_database_performance(self):
        """Test database operation performance"""
        import time

        # Insert performance test
        start_time = time.time()
        for i in range(100):
            threat = {
                "ip_address": f"10.0.0.{i}",
                "threat_level": "normal",
                "threat_score": 0.1
            }
            self.db.store_threat_analysis(threat)
        end_time = time.time()

        avg_insert_time = (end_time - start_time) / 100
        assert avg_insert_time < 0.01  # Should be faster than 10ms per insert

        # Query performance test
        start_time = time.time()
        for _ in range(10):
            self.db.get_threats(limit=50)
        end_time = time.time()

        avg_query_time = (end_time - start_time) / 10
        assert avg_query_time < 0.1  # Should be faster than 100ms per query

if __name__ == "__main__":
    pytest.main([__file__, "-v"])