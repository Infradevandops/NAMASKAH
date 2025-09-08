#!/usr/bin/env python3
"""
Integration tests for Verification Management API
"""
import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from models.user_models import Base, User, VerificationRequest, SubscriptionPlan
from database import get_db
from auth.jwt_handler import create_jwt_token

# Test database setup
@pytest.fixture
def db_session():
    """Create test database session"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()

@pytest.fixture
def test_user(db_session):
    """Create test user"""
    user = User(
        id="test-user-123",
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_password",
        subscription_plan=SubscriptionPlan.BASIC,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def auth_headers(test_user):
    """Create authentication headers with JWT token"""
    token = create_jwt_token({"user_id": test_user.id, "email": test_user.email})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def client(db_session):
    """Create test client with database override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()

@pytest.fixture
def mock_textverified_client():
    """Mock TextVerified client for testing"""
    with patch('api.verification_api.TextVerifiedClient') as mock_client_class:
        mock_client = Mock()
        mock_client.create_verification = AsyncMock(return_value="tv_123456")
        mock_client.get_verification_number = AsyncMock(return_value="+1234567890")
        mock_client.get_sms_messages = AsyncMock(return_value=[])
        mock_client.cancel_verification = AsyncMock(return_value=True)
        mock_client_class.return_value = mock_client
        yield mock_client

class TestVerificationAPI:
    """Test verification API endpoints"""
    
    def test_create_verification_success(self, client, auth_headers, test_user, mock_textverified_client):
        """Test successful verification creation"""
        request_data = {
            "service_name": "whatsapp",
            "capability": "sms"
        }
        
        response = client.post(
            "/api/verifications/create",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["service_name"] == "whatsapp"
        assert data["status"] == "pending"
        assert "id" in data
        assert "created_at" in data
        
        mock_textverified_client.create_verification.assert_called_once_with(
            service_name="whatsapp",
            capability="sms"
        )
    
    def test_create_verification_unauthorized(self, client):
        """Test verification creation without authentication"""
        request_data = {
            "service_name": "whatsapp",
            "capability": "sms"
        }
        
        response = client.post("/api/verifications/create", json=request_data)
        
        assert response.status_code == 403  # No authorization header
    
    def test_create_verification_invalid_token(self, client):
        """Test verification creation with invalid token"""
        request_data = {
            "service_name": "whatsapp",
            "capability": "sms"
        }
        
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.post(
            "/api/verifications/create",
            json=request_data,
            headers=headers
        )
        
        assert response.status_code == 401
    
    def test_get_verifications_empty(self, client, auth_headers, test_user):
        """Test getting verifications when none exist"""
        response = client.get("/api/verifications", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["verifications"] == []
        assert data["total_count"] == 0
        assert data["page"] == 1
        assert data["page_size"] == 20
    
    def test_get_verifications_with_data(self, client, auth_headers, test_user, db_session, mock_textverified_client):
        """Test getting verifications with existing data"""
        # Create test verifications
        verification1 = VerificationRequest(
            user_id=test_user.id,
            textverified_id="tv_123",
            service_name="whatsapp",
            status="pending",
            expires_at=datetime.utcnow() + timedelta(minutes=30)
        )
        verification2 = VerificationRequest(
            user_id=test_user.id,
            textverified_id="tv_456",
            service_name="google",
            status="completed",
            verification_code="123456",
            expires_at=datetime.utcnow() + timedelta(minutes=30)
        )
        
        db_session.add_all([verification1, verification2])
        db_session.commit()
        
        response = client.get("/api/verifications", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["verifications"]) == 2
        assert data["total_count"] == 2
        
        # Check verification data
        services = [v["service_name"] for v in data["verifications"]]
        assert "whatsapp" in services
        assert "google" in services
    
    def test_get_verifications_with_filters(self, client, auth_headers, test_user, db_session):
        """Test getting verifications with filters"""
        # Create test verifications
        verification1 = VerificationRequest(
            user_id=test_user.id,
            textverified_id="tv_123",
            service_name="whatsapp",
            status="pending",
            expires_at=datetime.utcnow() + timedelta(minutes=30)
        )
        verification2 = VerificationRequest(
            user_id=test_user.id,
            textverified_id="tv_456",
            service_name="google",
            status="completed",
            verification_code="123456",
            expires_at=datetime.utcnow() + timedelta(minutes=30)
        )
        
        db_session.add_all([verification1, verification2])
        db_session.commit()
        
        # Filter by service name
        response = client.get(
            "/api/verifications?service_name=whatsapp",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["verifications"]) == 1
        assert data["verifications"][0]["service_name"] == "whatsapp"
        
        # Filter by status
        response = client.get(
            "/api/verifications?status=completed",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["verifications"]) == 1
        assert data["verifications"][0]["status"] == "completed"
    
    def test_get_verifications_with_search(self, client, auth_headers, test_user, db_session):
        """Test getting verifications with search query"""
        # Create test verification
        verification = VerificationRequest(
            user_id=test_user.id,
            textverified_id="tv_123",
            service_name="whatsapp",
            phone_number="+1234567890",
            status="pending",
            expires_at=datetime.utcnow() + timedelta(minutes=30)
        )
        
        db_session.add(verification)
        db_session.commit()
        
        # Search by service name
        response = client.get(
            "/api/verifications?search=whatsapp",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["verifications"]) == 1
        assert data["verifications"][0]["service_name"] == "whatsapp"
        
        # Search by phone number
        response = client.get(
            "/api/verifications?search=1234567890",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["verifications"]) == 1
        assert data["verifications"][0]["phone_number"] == "+1234567890"
    
    def test_get_verifications_pagination(self, client, auth_headers, test_user, db_session):
        """Test verification pagination"""
        # Create multiple verifications
        verifications = []
        for i in range(25):
            verification = VerificationRequest(
                user_id=test_user.id,
                textverified_id=f"tv_{i}",
                service_name=f"service{i}",
                status="pending",
                expires_at=datetime.utcnow() + timedelta(minutes=30)
            )
            verifications.append(verification)
        
        db_session.add_all(verifications)
        db_session.commit()
        
        # Test first page
        response = client.get(
            "/api/verifications?page=1&page_size=10",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["verifications"]) == 10
        assert data["total_count"] == 25
        assert data["page"] == 1
        assert data["page_size"] == 10
        
        # Test second page
        response = client.get(
            "/api/verifications?page=2&page_size=10",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["verifications"]) == 10
        assert data["page"] == 2
    
    def test_get_verification_by_id(self, client, auth_headers, test_user, db_session):
        """Test getting specific verification by ID"""
        # Create test verification
        verification = VerificationRequest(
            user_id=test_user.id,
            textverified_id="tv_123",
            service_name="whatsapp",
            status="pending",
            expires_at=datetime.utcnow() + timedelta(minutes=30)
        )
        
        db_session.add(verification)
        db_session.commit()
        
        response = client.get(
            f"/api/verifications/{verification.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == verification.id
        assert data["service_name"] == "whatsapp"
        assert data["status"] == "pending"
    
    def test_get_verification_not_found(self, client, auth_headers, test_user):
        """Test getting non-existent verification"""
        response = client.get(
            "/api/verifications/invalid-id",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_get_verification_wrong_user(self, client, auth_headers, test_user, db_session):
        """Test getting verification that belongs to different user"""
        # Create another user
        other_user = User(
            id="other-user-123",
            email="other@example.com",
            username="otheruser",
            hashed_password="hashed_password",
            is_active=True
        )
        db_session.add(other_user)
        
        # Create verification for other user
        verification = VerificationRequest(
            user_id=other_user.id,
            textverified_id="tv_123",
            service_name="whatsapp",
            status="pending",
            expires_at=datetime.utcnow() + timedelta(minutes=30)
        )
        
        db_session.add(verification)
        db_session.commit()
        
        # Try to access with test_user token
        response = client.get(
            f"/api/verifications/{verification.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_get_verification_codes(self, client, auth_headers, test_user, db_session, mock_textverified_client):
        """Test getting verification codes"""
        # Create test verification
        verification = VerificationRequest(
            user_id=test_user.id,
            textverified_id="tv_123",
            service_name="whatsapp",
            status="pending",
            expires_at=datetime.utcnow() + timedelta(minutes=30)
        )
        
        db_session.add(verification)
        db_session.commit()
        
        # Mock SMS messages with verification code
        mock_textverified_client.get_sms_messages.return_value = [
            "Your WhatsApp verification code is 123456"
        ]
        
        response = client.get(
            f"/api/verifications/{verification.id}/codes",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["verification_id"] == verification.id
        assert len(data["messages"]) == 1
        assert "123456" in data["extracted_codes"]
        assert data["auto_completed"] == True  # Should be auto-completed
    
    def test_get_verification_phone(self, client, auth_headers, test_user, db_session, mock_textverified_client):
        """Test getting verification phone number"""
        # Create test verification
        verification = VerificationRequest(
            user_id=test_user.id,
            textverified_id="tv_123",
            service_name="whatsapp",
            status="pending",
            expires_at=datetime.utcnow() + timedelta(minutes=30)
        )
        
        db_session.add(verification)
        db_session.commit()
        
        response = client.get(
            f"/api/verifications/{verification.id}/phone",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["phone_number"] == "+1234567890"
        mock_textverified_client.get_verification_number.assert_called_once_with("tv_123")
    
    def test_delete_verification(self, client, auth_headers, test_user, db_session, mock_textverified_client):
        """Test cancelling/deleting verification"""
        # Create test verification
        verification = VerificationRequest(
            user_id=test_user.id,
            textverified_id="tv_123",
            service_name="whatsapp",
            status="pending",
            expires_at=datetime.utcnow() + timedelta(minutes=30)
        )
        
        db_session.add(verification)
        db_session.commit()
        
        response = client.delete(
            f"/api/verifications/{verification.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "cancelled successfully" in data["message"]
        mock_textverified_client.cancel_verification.assert_called_once_with("tv_123")
        
        # Verify status updated in database
        db_session.refresh(verification)
        assert verification.status == "cancelled"
    
    def test_delete_verification_not_found(self, client, auth_headers, test_user):
        """Test deleting non-existent verification"""
        response = client.delete(
            "/api/verifications/invalid-id",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_delete_completed_verification(self, client, auth_headers, test_user, db_session):
        """Test deleting already completed verification"""
        # Create completed verification
        verification = VerificationRequest(
            user_id=test_user.id,
            textverified_id="tv_123",
            service_name="whatsapp",
            status="completed",
            verification_code="123456",
            expires_at=datetime.utcnow() + timedelta(minutes=30)
        )
        
        db_session.add(verification)
        db_session.commit()
        
        response = client.delete(
            f"/api/verifications/{verification.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "Cannot cancel" in response.json()["detail"]
    
    def test_get_verification_statistics(self, client, auth_headers, test_user, db_session):
        """Test getting verification statistics"""
        # Create test verifications with different statuses
        verifications = [
            VerificationRequest(
                user_id=test_user.id,
                textverified_id="tv_1",
                service_name="whatsapp",
                status="completed",
                verification_code="123456",
                expires_at=datetime.utcnow() + timedelta(minutes=30)
            ),
            VerificationRequest(
                user_id=test_user.id,
                textverified_id="tv_2",
                service_name="google",
                status="completed",
                verification_code="789012",
                expires_at=datetime.utcnow() + timedelta(minutes=30)
            ),
            VerificationRequest(
                user_id=test_user.id,
                textverified_id="tv_3",
                service_name="telegram",
                status="failed",
                expires_at=datetime.utcnow() + timedelta(minutes=30)
            )
        ]
        
        db_session.add_all(verifications)
        db_session.commit()
        
        response = client.get(
            "/api/verifications/stats/summary?period_days=30",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_verifications"] == 3
        assert data["completed_verifications"] == 2
        assert data["success_rate"] == 66.67
        assert data["status_breakdown"]["completed"] == 2
        assert data["status_breakdown"]["failed"] == 1
        assert data["service_usage"]["whatsapp"] == 1
        assert data["service_usage"]["google"] == 1
        assert data["service_usage"]["telegram"] == 1
    
    def test_export_verification_data_json(self, client, auth_headers, test_user, db_session):
        """Test exporting verification data in JSON format"""
        # Create test verification
        verification = VerificationRequest(
            user_id=test_user.id,
            textverified_id="tv_123",
            service_name="whatsapp",
            status="completed",
            verification_code="123456",
            expires_at=datetime.utcnow() + timedelta(minutes=30)
        )
        
        db_session.add(verification)
        db_session.commit()
        
        response = client.get(
            "/api/verifications/export/data?format_type=json",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["format"] == "json"
        assert data["user_id"] == test_user.id
        assert data["record_count"] == 1
        assert len(data["data"]) == 1
        
        record = data["data"][0]
        assert record["service_name"] == "whatsapp"
        assert record["status"] == "completed"
        assert record["verification_code"] == "123456"
    
    def test_export_verification_data_csv(self, client, auth_headers, test_user, db_session):
        """Test exporting verification data in CSV format"""
        # Create test verification
        verification = VerificationRequest(
            user_id=test_user.id,
            textverified_id="tv_123",
            service_name="whatsapp",
            status="completed",
            verification_code="123456",
            expires_at=datetime.utcnow() + timedelta(minutes=30)
        )
        
        db_session.add(verification)
        db_session.commit()
        
        response = client.get(
            "/api/verifications/export/data?format_type=csv",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        
        csv_content = response.content.decode()
        assert "id,service_name" in csv_content  # CSV headers
        assert "whatsapp" in csv_content
        assert "completed" in csv_content
    
    def test_export_verification_data_with_filters(self, client, auth_headers, test_user, db_session):
        """Test exporting verification data with filters"""
        # Create test verifications
        verifications = [
            VerificationRequest(
                user_id=test_user.id,
                textverified_id="tv_1",
                service_name="whatsapp",
                status="completed",
                verification_code="123456",
                expires_at=datetime.utcnow() + timedelta(minutes=30)
            ),
            VerificationRequest(
                user_id=test_user.id,
                textverified_id="tv_2",
                service_name="google",
                status="pending",
                expires_at=datetime.utcnow() + timedelta(minutes=30)
            )
        ]
        
        db_session.add_all(verifications)
        db_session.commit()
        
        # Export only completed verifications
        response = client.get(
            "/api/verifications/export/data?format_type=json&status=completed",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["record_count"] == 1
        assert data["data"][0]["service_name"] == "whatsapp"
        assert data["data"][0]["status"] == "completed"

class TestVerificationAPIValidation:
    """Test API input validation"""
    
    def test_create_verification_missing_service_name(self, client, auth_headers):
        """Test verification creation with missing service name"""
        request_data = {
            "capability": "sms"
        }
        
        response = client.post(
            "/api/verifications/create",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_get_verifications_invalid_pagination(self, client, auth_headers):
        """Test getting verifications with invalid pagination parameters"""
        # Invalid page number
        response = client.get(
            "/api/verifications?page=0",
            headers=auth_headers
        )
        
        assert response.status_code == 422
        
        # Invalid page size
        response = client.get(
            "/api/verifications?page_size=0",
            headers=auth_headers
        )
        
        assert response.status_code == 422
        
        # Page size too large
        response = client.get(
            "/api/verifications?page_size=1000",
            headers=auth_headers
        )
        
        assert response.status_code == 422
    
    def test_export_invalid_format(self, client, auth_headers):
        """Test export with invalid format type"""
        response = client.get(
            "/api/verifications/export/data?format_type=xml",
            headers=auth_headers
        )
        
        assert response.status_code == 422
    
    def test_statistics_invalid_period(self, client, auth_headers):
        """Test statistics with invalid period"""
        # Period too small
        response = client.get(
            "/api/verifications/stats/summary?period_days=0",
            headers=auth_headers
        )
        
        assert response.status_code == 422
        
        # Period too large
        response = client.get(
            "/api/verifications/stats/summary?period_days=400",
            headers=auth_headers
        )
        
        assert response.status_code == 422

if __name__ == "__main__":
    pytest.main([__file__, "-v"])