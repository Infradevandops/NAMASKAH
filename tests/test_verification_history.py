#!/usr/bin/env python3
"""
Tests for Verification History and Export Features
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
def sample_verifications(db_session, test_user):
    """Create sample verification data for testing"""
    verifications = []
    
    # Create verifications with different statuses and services
    verification_data = [
        {
            "service_name": "whatsapp",
            "status": "completed",
            "verification_code": "123456",
            "phone_number": "+1234567890",
            "created_at": datetime.utcnow() - timedelta(days=1),
            "completed_at": datetime.utcnow() - timedelta(days=1, hours=1)
        },
        {
            "service_name": "google",
            "status": "completed",
            "verification_code": "789012",
            "phone_number": "+1234567891",
            "created_at": datetime.utcnow() - timedelta(days=2),
            "completed_at": datetime.utcnow() - timedelta(days=2, hours=1)
        },
        {
            "service_name": "telegram",
            "status": "pending",
            "phone_number": "+1234567892",
            "created_at": datetime.utcnow() - timedelta(hours=2)
        },
        {
            "service_name": "discord",
            "status": "failed",
            "phone_number": "+1234567893",
            "created_at": datetime.utcnow() - timedelta(days=3)
        },
        {
            "service_name": "facebook",
            "status": "cancelled",
            "phone_number": "+1234567894",
            "created_at": datetime.utcnow() - timedelta(days=5)
        }
    ]
    
    for i, data in enumerate(verification_data):
        verification = VerificationRequest(
            user_id=test_user.id,
            textverified_id=f"tv_{i}",
            expires_at=datetime.utcnow() + timedelta(minutes=30),
            **data
        )
        verifications.append(verification)
        db_session.add(verification)
    
    db_session.commit()
    return verifications

class TestVerificationHistoryAPI:
    """Test verification history API functionality"""
    
    def test_get_verification_statistics(self, client, auth_headers, sample_verifications):
        """Test getting verification statistics"""
        response = client.get(
            "/api/verifications/stats/summary?period_days=30",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_verifications"] == 5
        assert data["completed_verifications"] == 2
        assert data["success_rate"] == 40.0  # 2/5 * 100
        assert data["period_days"] == 30
        
        # Check status breakdown
        assert data["status_breakdown"]["completed"] == 2
        assert data["status_breakdown"]["pending"] == 1
        assert data["status_breakdown"]["failed"] == 1
        assert data["status_breakdown"]["cancelled"] == 1
        
        # Check service usage
        assert data["service_usage"]["whatsapp"] == 1
        assert data["service_usage"]["google"] == 1
        assert data["service_usage"]["telegram"] == 1
        assert data["service_usage"]["discord"] == 1
        assert data["service_usage"]["facebook"] == 1
    
    def test_get_verification_statistics_different_periods(self, client, auth_headers, sample_verifications):
        """Test statistics with different time periods"""
        # Test 7-day period
        response = client.get(
            "/api/verifications/stats/summary?period_days=7",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["period_days"] == 7
        
        # Test 1-day period (should include only recent verifications)
        response = client.get(
            "/api/verifications/stats/summary?period_days=1",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["period_days"] == 1
        # Should have fewer verifications than 30-day period
        assert data["total_verifications"] <= 5
    
    def test_export_verification_data_json(self, client, auth_headers, sample_verifications):
        """Test exporting verification data in JSON format"""
        response = client.get(
            "/api/verifications/export/data?format_type=json",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["format"] == "json"
        assert data["record_count"] == 5
        assert len(data["data"]) == 5
        
        # Check data structure
        record = data["data"][0]
        required_fields = [
            "id", "service_name", "phone_number", "status", 
            "verification_code", "created_at", "completed_at", "expires_at"
        ]
        for field in required_fields:
            assert field in record
        
        # Verify data content
        services = [r["service_name"] for r in data["data"]]
        assert "whatsapp" in services
        assert "google" in services
        assert "telegram" in services
    
    def test_export_verification_data_csv(self, client, auth_headers, sample_verifications):
        """Test exporting verification data in CSV format"""
        response = client.get(
            "/api/verifications/export/data?format_type=csv",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        
        csv_content = response.content.decode()
        
        # Check CSV headers
        assert "id,service_name,phone_number,status,verification_code" in csv_content
        
        # Check CSV data
        lines = csv_content.strip().split('\n')
        assert len(lines) == 6  # Header + 5 data rows
        
        # Verify some data is present
        assert "whatsapp" in csv_content
        assert "completed" in csv_content
        assert "+1234567890" in csv_content
    
    def test_export_with_filters(self, client, auth_headers, sample_verifications):
        """Test exporting data with filters applied"""
        # Export only completed verifications
        response = client.get(
            "/api/verifications/export/data?format_type=json&status=completed",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["record_count"] == 2
        assert len(data["data"]) == 2
        
        # All records should be completed
        for record in data["data"]:
            assert record["status"] == "completed"
        
        # Export only WhatsApp verifications
        response = client.get(
            "/api/verifications/export/data?format_type=json&service_name=whatsapp",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["record_count"] == 1
        assert data["data"][0]["service_name"] == "whatsapp"
    
    def test_export_with_date_filters(self, client, auth_headers, sample_verifications):
        """Test exporting data with date range filters"""
        # Get verifications from last 2 days
        date_from = (datetime.utcnow() - timedelta(days=2)).strftime("%Y-%m-%d")
        
        response = client.get(
            f"/api/verifications/export/data?format_type=json&date_from={date_from}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have fewer records than total
        assert data["record_count"] <= 5
        assert data["record_count"] >= 1
        
        # Verify dates are within range
        for record in data["data"]:
            created_date = datetime.fromisoformat(record["created_at"].replace('Z', '+00:00'))
            assert created_date >= datetime.fromisoformat(date_from + "T00:00:00+00:00")
    
    def test_export_invalid_format(self, client, auth_headers):
        """Test export with invalid format"""
        response = client.get(
            "/api/verifications/export/data?format_type=xml",
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_export_unauthorized(self, client, sample_verifications):
        """Test export without authentication"""
        response = client.get("/api/verifications/export/data?format_type=json")
        
        assert response.status_code == 403  # No authorization header

class TestVerificationHistoryFiltering:
    """Test verification history filtering and search"""
    
    def test_filter_by_service(self, client, auth_headers, sample_verifications):
        """Test filtering verifications by service name"""
        response = client.get(
            "/api/verifications?service_name=whatsapp",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_count"] == 1
        assert len(data["verifications"]) == 1
        assert data["verifications"][0]["service_name"] == "whatsapp"
    
    def test_filter_by_status(self, client, auth_headers, sample_verifications):
        """Test filtering verifications by status"""
        response = client.get(
            "/api/verifications?status=completed",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_count"] == 2
        assert len(data["verifications"]) == 2
        
        for verification in data["verifications"]:
            assert verification["status"] == "completed"
    
    def test_filter_by_date_range(self, client, auth_headers, sample_verifications):
        """Test filtering verifications by date range"""
        # Filter to last 2 days
        date_from = (datetime.utcnow() - timedelta(days=2)).isoformat()
        
        response = client.get(
            f"/api/verifications?date_from={date_from}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have fewer than total verifications
        assert data["total_count"] <= 5
        assert data["total_count"] >= 1
        
        # Verify all returned verifications are within date range
        for verification in data["verifications"]:
            created_date = datetime.fromisoformat(verification["created_at"].replace('Z', ''))
            filter_date = datetime.fromisoformat(date_from.replace('Z', ''))
            assert created_date >= filter_date
    
    def test_search_verifications(self, client, auth_headers, sample_verifications):
        """Test searching verifications"""
        # Search by service name
        response = client.get(
            "/api/verifications?search=whatsapp",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_count"] >= 1
        # Should find WhatsApp verification
        services = [v["service_name"] for v in data["verifications"]]
        assert "whatsapp" in services
        
        # Search by phone number
        response = client.get(
            "/api/verifications?search=1234567890",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_count"] >= 1
        # Should find verification with that phone number
        phones = [v["phone_number"] for v in data["verifications"] if v["phone_number"]]
        assert any("1234567890" in phone for phone in phones)
    
    def test_combined_filters(self, client, auth_headers, sample_verifications):
        """Test combining multiple filters"""
        response = client.get(
            "/api/verifications?status=completed&service_name=whatsapp",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should find only completed WhatsApp verifications
        for verification in data["verifications"]:
            assert verification["status"] == "completed"
            assert verification["service_name"] == "whatsapp"
    
    def test_pagination_with_filters(self, client, auth_headers, sample_verifications):
        """Test pagination works with filters"""
        response = client.get(
            "/api/verifications?page=1&page_size=2",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert len(data["verifications"]) <= 2
        assert data["total_count"] == 5

class TestVerificationHistoryAnalytics:
    """Test verification analytics and success rate tracking"""
    
    def test_success_rate_calculation(self, client, auth_headers, sample_verifications):
        """Test success rate calculation accuracy"""
        response = client.get(
            "/api/verifications/stats/summary",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # With sample data: 2 completed out of 5 total = 40%
        expected_rate = (2 / 5) * 100
        assert data["success_rate"] == expected_rate
        
        # Verify the calculation components
        assert data["total_verifications"] == 5
        assert data["completed_verifications"] == 2
    
    def test_service_usage_analytics(self, client, auth_headers, sample_verifications):
        """Test service usage analytics"""
        response = client.get(
            "/api/verifications/stats/summary",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        service_usage = data["service_usage"]
        
        # Each service should have exactly 1 verification
        expected_services = ["whatsapp", "google", "telegram", "discord", "facebook"]
        for service in expected_services:
            assert service in service_usage
            assert service_usage[service] == 1
    
    def test_status_breakdown_analytics(self, client, auth_headers, sample_verifications):
        """Test status breakdown analytics"""
        response = client.get(
            "/api/verifications/stats/summary",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        status_breakdown = data["status_breakdown"]
        
        # Verify expected status counts
        expected_statuses = {
            "completed": 2,
            "pending": 1,
            "failed": 1,
            "cancelled": 1
        }
        
        for status, count in expected_statuses.items():
            assert status in status_breakdown
            assert status_breakdown[status] == count
    
    def test_empty_statistics(self, client, auth_headers, test_user, db_session):
        """Test statistics when no verifications exist"""
        # Clear all verifications
        db_session.query(VerificationRequest).filter(
            VerificationRequest.user_id == test_user.id
        ).delete()
        db_session.commit()
        
        response = client.get(
            "/api/verifications/stats/summary",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_verifications"] == 0
        assert data["completed_verifications"] == 0
        assert data["success_rate"] == 0
        assert data["status_breakdown"] == {}
        assert data["service_usage"] == {}

class TestVerificationHistoryPerformance:
    """Test performance aspects of verification history"""
    
    def test_large_dataset_pagination(self, client, auth_headers, test_user, db_session):
        """Test pagination with large dataset"""
        # Create many verifications
        verifications = []
        for i in range(100):
            verification = VerificationRequest(
                user_id=test_user.id,
                textverified_id=f"tv_{i}",
                service_name="whatsapp",
                status="completed" if i % 2 == 0 else "pending",
                expires_at=datetime.utcnow() + timedelta(minutes=30),
                created_at=datetime.utcnow() - timedelta(hours=i)
            )
            verifications.append(verification)
        
        db_session.add_all(verifications)
        db_session.commit()
        
        # Test first page
        response = client.get(
            "/api/verifications?page=1&page_size=20",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_count"] == 100
        assert len(data["verifications"]) == 20
        assert data["page"] == 1
        assert data["page_size"] == 20
        
        # Test middle page
        response = client.get(
            "/api/verifications?page=3&page_size=20",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["verifications"]) == 20
        assert data["page"] == 3
    
    def test_export_large_dataset(self, client, auth_headers, test_user, db_session):
        """Test exporting large dataset"""
        # Create many verifications
        verifications = []
        for i in range(50):
            verification = VerificationRequest(
                user_id=test_user.id,
                textverified_id=f"tv_{i}",
                service_name=f"service{i % 5}",
                status="completed",
                verification_code=f"{100000 + i}",
                phone_number=f"+123456{i:04d}",
                expires_at=datetime.utcnow() + timedelta(minutes=30),
                created_at=datetime.utcnow() - timedelta(hours=i)
            )
            verifications.append(verification)
        
        db_session.add_all(verifications)
        db_session.commit()
        
        # Test JSON export
        response = client.get(
            "/api/verifications/export/data?format_type=json",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["record_count"] == 50
        assert len(data["data"]) == 50
        
        # Test CSV export
        response = client.get(
            "/api/verifications/export/data?format_type=csv",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        csv_content = response.content.decode()
        lines = csv_content.strip().split('\n')
        assert len(lines) == 51  # Header + 50 data rows

if __name__ == "__main__":
    pytest.main([__file__, "-v"])