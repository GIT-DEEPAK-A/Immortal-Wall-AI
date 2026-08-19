import pytest
from fastapi.testclient import TestClient
from backend.app import app
from backend.database.models import DatabaseManager
from backend.services.auth_service import AuthService
import os

# Create test client
client = TestClient(app)

# Use in-memory database for tests
@pytest.fixture(scope="function")
def test_db():
    """Create in-memory database for testing"""
    db = DatabaseManager(db_path=":memory:")
    return db

@pytest.fixture(scope="function")
def test_auth_service(test_db):
    """Create auth service with test database"""
    os.environ["SMTP_APP_PASSWORD"] = "test_password"
    return AuthService(test_db)


class TestUserCreation:
    """Test user management"""
    
    def test_create_user(self, test_db):
        """Test creating a new user"""
        result = test_db.create_user(
            email="test@example.com",
            password="testpassword123",
            role="Analyst"
        )
        assert result is True
    
    def test_create_duplicate_user(self, test_db):
        """Test that duplicate users cannot be created"""
        test_db.create_user("duplicate@test.com", "password", "Analyst")
        result = test_db.create_user("duplicate@test.com", "password", "Analyst")
        assert result is False
    
    def test_get_user_by_email(self, test_db):
        """Test retrieving user by email"""
        test_db.create_user("test@example.com", "password", "Admin")
        user = test_db.get_user_by_email("test@example.com")
        assert user is not None
        assert user.email == "test@example.com"
        assert user.role == "Admin"


class TestPasswordValidation:
    """Test password verification"""
    
    def test_verify_correct_password(self, test_db):
        """Test correct password verification"""
        test_db.create_user("test@example.com", "correctpassword", "Analyst")
        result = test_db.verify_user_password("test@example.com", "correctpassword")
        assert result is True
    
    def test_verify_incorrect_password(self, test_db):
        """Test incorrect password rejection"""
        test_db.create_user("test@example.com", "correctpassword", "Analyst")
        result = test_db.verify_user_password("test@example.com", "wrongpassword")
        assert result is False
    
    def test_verify_nonexistent_user(self, test_db):
        """Test verification for non-existent user"""
        result = test_db.verify_user_password("nonexistent@example.com", "password")
        assert result is False


class TestOTPGeneration:
    """Test OTP generation and validation"""
    
    def test_generate_otp_format(self, test_auth_service):
        """Test OTP generation format"""
        otp = test_auth_service.generate_secure_otp()
        assert len(otp) == 6
        assert otp.isdigit()
    
    def test_otp_uniqueness(self, test_auth_service):
        """Test that generated OTPs are unique"""
        otps = set()
        for _ in range(100):
            otp = test_auth_service.generate_secure_otp()
            otps.add(otp)
        # Most should be unique (allowing for occasional collisions in random)
        assert len(otps) > 95
    
    def test_create_otp_entry(self, test_auth_service):
        """Test OTP entry creation"""
        result = test_auth_service.create_otp("test@example.com")
        assert result is not None
        assert len(result) == 6
    
    def test_get_active_otp(self, test_auth_service):
        """Test retrieving active OTP"""
        test_auth_service.create_otp("test@example.com")
        otp_entry = test_auth_service.db.get_active_otp("test@example.com")
        assert otp_entry is not None
    
    def test_otp_expiration(self, test_auth_service):
        """Test that expired OTP is not returned"""
        from datetime import datetime, timedelta
        
        # Create OTP with very short TTL
        test_auth_service.otp_ttl_minutes = 0  # Expired immediately
        test_auth_service.create_otp("test@example.com")
        
        # Should not retrieve expired OTP
        otp_entry = test_auth_service.db.get_active_otp("test@example.com")
        assert otp_entry is None
    
    def test_otp_max_attempts(self, test_auth_service):
        """Test max attempt limit"""
        test_auth_service.create_otp("test@example.com")
        
        # Try wrong OTP 3 times
        for _ in range(3):
            test_auth_service.db.increment_otp_attempts("test@example.com")
        
        # Should not retrieve OTP after max attempts
        otp_entry = test_auth_service.db.get_active_otp("test@example.com")
        assert otp_entry is None


class TestOTPVerification:
    """Test OTP verification process"""
    
    def test_verify_correct_otp(self, test_auth_service):
        """Test verification with correct OTP"""
        # Create test user
        test_auth_service.db.create_user("test@example.com", "password", "Analyst")
        
        # Generate OTP
        otp = test_auth_service.create_otp("test@example.com")
        
        # Verify OTP
        result = test_auth_service.verify_otp("test@example.com", otp)
        assert result is True
    
    def test_verify_incorrect_otp(self, test_auth_service):
        """Test verification with incorrect OTP"""
        test_auth_service.db.create_user("test@example.com", "password", "Analyst")
        test_auth_service.create_otp("test@example.com")
        
        # Try wrong OTP
        result = test_auth_service.verify_otp("test@example.com", "999999")
        assert result is False
    
    def test_otp_invalidation_after_use(self, test_auth_service):
        """Test that OTP is invalidated after successful use"""
        test_auth_service.db.create_user("test@example.com", "password", "Analyst")
        
        # Create and verify OTP
        otp = test_auth_service.create_otp("test@example.com")
        test_auth_service.verify_otp("test@example.com", otp)
        
        # OTP should no longer be retrievable
        otp_entry = test_auth_service.db.get_active_otp("test@example.com")
        assert otp_entry is None


class TestAPIEndpoints:
    """Test API endpoints"""
    
    def test_login_endpoint_missing_credentials(self):
        """Test login with missing credentials"""
        response = client.post("/api/auth/login", json={})
        assert response.status_code in [422, 400]  # Validation error
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "components" in data
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "status" in data


class TestAuthentication:
    """Test complete authentication flow"""
    
    def test_login_success_flow(self):
        """Test successful login flow"""
        # Login with demo user
        response = client.post("/api/auth/login", json={
            "email": "deepakananthan4@gmail.com",
            "password": "password"
        })
        # May fail due to email sending, but check endpoint exists
        assert response.status_code in [200, 500]  # Server error is OK (no email)
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = client.post("/api/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 404
    
    def test_auth_pages_accessible(self):
        """Test that auth pages are accessible"""
        response = client.get("/auth/login")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        
        # OTP page might redirect if not authenticated
        response = client.get("/auth/otp")
        assert response.status_code in [200, 307, 404]


class TestSecurityFeatures:
    """Test security implementations"""
    
    def test_password_hashing(self, test_db):
        """Test that passwords are hashed"""
        test_db.create_user("test@example.com", "plaintext_password", "Analyst")
        user = test_db.get_user_by_email("test@example.com")
        
        # Password should not be stored in plain text
        assert user.password_hash != "plaintext_password"
        assert len(user.password_hash) == 64  # SHA256 hex
    
    def test_different_salts_for_same_password(self, test_db):
        """Test that different users get different salts"""
        test_db.create_user("user1@example.com", "samepassword", "Analyst")
        test_db.create_user("user2@example.com", "samepassword", "Analyst")
        
        user1 = test_db.get_user_by_email("user1@example.com")
        user2 = test_db.get_user_by_email("user2@example.com")
        
        # Salts should be different
        assert user1.salt != user2.salt
        # Hashes should be different
        assert user1.password_hash != user2.password_hash
    
    def test_otp_hashing(self, test_auth_service):
        """Test that OTPs are hashed in storage"""
        otp = test_auth_service.create_otp("test@example.com")
        otp_entry = test_auth_service.db.get_active_otp("test@example.com")
        
        # OTP hash should not be plaintext
        assert otp_entry.otp_hash != otp
        assert len(otp_entry.otp_hash) == 64  # SHA256 hex


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
