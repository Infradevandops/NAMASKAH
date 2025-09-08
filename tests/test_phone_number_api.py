#!/usr/bin/env python3
"""
Integration tests for Phone Number API endpoints
"""
import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient

from main import app
from models.user_models import User, PhoneNumber

class TestPhoneNumberAPI:
    """Test phone number API endpoints"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def mock_user(self):
        return User(
            id="test_user_1",
            email="test@example.com",
            username="testuser",
            subscription_plan="BASIC",
            is_active=True,
            is_verified=True
        )
    
    @pytest.fixture
    def mock_phone_number(self):
        return PhoneNumber(
            id="phone_1",
            phone_number="+15551234567",
            country_code="US",
            area_code="555",
            provider="mock",
            owner_id="test_user_1",
            monthly_cost="1.50",
            sms_cost_per_message="0.01",
            status="active",
            purchased_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=30),
            auto_renew=True,
            total_sms_sent=100,
            total_sms_received=50,
            monthly_sms_sent=25
        )
    
    def test_get_available_numbers_success(self, client, mock_user):
        """Test getting available numbers successfully"""
        with patch('services.auth_service.get_current_active_user', return_value=mock_user):
            with patch('services.phone_number_service.PhoneNumberService.search_available_numbers') as mock_search:
                mock_search.return_value = ([
                    {
                        "phone_number": "+15551234567",
                        "country_code": "US",
                        "area_code": "555",
                        "region": "United States",
                        "provider": "mock",
                        "monthly_cost": 1.50,
                        "sms_cost_per_message": 0.01,
                        "voice_cost_per_minute": 0.02,
                        "setup_fee": 0.00,
                        "capabilities": ["sms", "voice"]
                    }
                ], 1)
                
                response = client.get("/api/numbers/available/US?area_code=555&limit=1")
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["country_code"] == "US"
                assert len(data["numbers"]) == 1
                assert data["numbers"][0]["phone_number"] == "+15551234567"
    
    def test_get_available_numbers_unauthorized(self, client):
        """Test getting available numbers without authentication"""
        response = client.get("/api/numbers/available/US")
        assert response.status_code == 401
    
    def test_purchase_phone_number_success(self, client, mock_user, mock_phone_number):
        """Test purchasing phone number successfully"""
        with patch('services.auth_service.get_current_active_user', return_value=mock_user):
            with patch('services.phone_number_service.PhoneNumberService.purchase_phone_number') as mock_purchase:
                mock_purchase.return_value = {
                    "success": True,
                    "message": "Phone number purchased successfully",
                    "phone_number": mock_phone_number,
                    "transaction_id": "txn_123456"
                }
                
                purchase_data = {
                    "phone_number": "+15551234567",
                    "auto_renew": True
                }
                
                response = client.post("/api/numbers/purchase", json=purchase_data)
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["transaction_id"] == "txn_123456"
                assert data["phone_number"]["phone_number"] == "+15551234567"
    
    def test_purchase_phone_number_already_owned(self, client, mock_user):
        """Test purchasing phone number that's already owned"""
        with patch('services.auth_service.get_current_active_user', return_value=mock_user):
            with patch('services.phone_number_service.PhoneNumberService.purchase_phone_number') as mock_purchase:
                mock_purchase.side_effect = ValueError("Phone number is already owned")
                
                purchase_data = {
                    "phone_number": "+15551234567",
                    "auto_renew": True
                }
                
                response = client.post("/api/numbers/purchase", json=purchase_data)
                
                assert response.status_code == 400
                assert "already owned" in response.json()["detail"]
    
    def test_get_owned_numbers_success(self, client, mock_user, mock_phone_number):
        """Test getting owned numbers successfully"""
        with patch('services.auth_service.get_current_active_user', return_value=mock_user):
            with patch('services.phone_number_service.PhoneNumberService.get_owned_numbers') as mock_owned:
                mock_owned.return_value = ([mock_phone_number], 1)
                
                response = client.get("/api/numbers/owned")
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["total_count"] == 1
                assert data["active_count"] == 1
                assert len(data["numbers"]) == 1
                assert data["numbers"][0]["phone_number"] == "+15551234567"
    
    def test_get_owned_numbers_empty(self, client, mock_user):
        """Test getting owned numbers when user has none"""
        with patch('services.auth_service.get_current_active_user', return_value=mock_user):
            with patch('services.phone_number_service.PhoneNumberService.get_owned_numbers') as mock_owned:
                mock_owned.return_value = ([], 0)
                
                response = client.get("/api/numbers/owned")
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["total_count"] == 0
                assert data["active_count"] == 0
                assert len(data["numbers"]) == 0
    
    def test_renew_phone_number_success(self, client, mock_user, mock_phone_number):
        """Test renewing phone number successfully"""
        with patch('services.auth_service.get_current_active_user', return_value=mock_user):
            with patch('services.phone_number_service.PhoneNumberService.renew_phone_number') as mock_renew:
                new_expires = datetime.utcnow() + timedelta(days=60)
                mock_renew.return_value = {
                    "success": True,
                    "message": "Phone number renewed for 2 month(s)",
                    "phone_number": mock_phone_number,
                    "transaction_id": "rnw_123456",
                    "total_cost": 3.00,
                    "new_expires_at": new_expires
                }
                
                renewal_data = {
                    "renewal_months": 2,
                    "auto_renew": True
                }
                
                response = client.put("/api/numbers/phone_1/renew", json=renewal_data)
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["transaction_id"] == "rnw_123456"
                assert data["total_cost"] == "3.0"
    
    def test_renew_phone_number_not_found(self, client, mock_user):
        """Test renewing phone number that doesn't exist"""
        with patch('services.auth_service.get_current_active_user', return_value=mock_user):
            with patch('services.phone_number_service.PhoneNumberService.renew_phone_number') as mock_renew:
                mock_renew.side_effect = ValueError("Phone number not found or not owned by user")
                
                renewal_data = {
                    "renewal_months": 1
                }
                
                response = client.put("/api/numbers/nonexistent/renew", json=renewal_data)
                
                assert response.status_code == 400
                assert "not found" in response.json()["detail"]
    
    def test_cancel_phone_number_success(self, client, mock_user):
        """Test cancelling phone number successfully"""
        with patch('services.auth_service.get_current_active_user', return_value=mock_user):
            with patch('services.phone_number_service.PhoneNumberService.cancel_phone_number') as mock_cancel:
                mock_cancel.return_value = {
                    "success": True,
                    "message": "Phone number subscription cancelled"
                }
                
                response = client.delete("/api/numbers/phone_1")
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert "cancelled" in data["message"]
    
    def test_cancel_phone_number_already_cancelled(self, client, mock_user):
        """Test cancelling phone number that's already cancelled"""
        with patch('services.auth_service.get_current_active_user', return_value=mock_user):
            with patch('services.phone_number_service.PhoneNumberService.cancel_phone_number') as mock_cancel:
                mock_cancel.side_effect = ValueError("Phone number is already cancelled")
                
                response = client.delete("/api/numbers/phone_1")
                
                assert response.status_code == 400
                assert "already cancelled" in response.json()["detail"]
    
    def test_get_phone_number_usage_success(self, client, mock_user):
        """Test getting phone number usage statistics"""
        with patch('services.auth_service.get_current_active_user', return_value=mock_user):
            with patch('services.phone_number_service.PhoneNumberService.get_usage_statistics') as mock_stats:
                mock_stats.return_value = {
                    "phone_number_id": "phone_1",
                    "phone_number": "+15551234567",
                    "period_start": datetime.utcnow() - timedelta(days=30),
                    "period_end": datetime.utcnow(),
                    "usage": {
                        "sms_sent": 100,
                        "sms_received": 50,
                        "voice_minutes": 30
                    },
                    "costs": {
                        "sms_cost": 1.00,
                        "voice_cost": 0.60,
                        "monthly_fee": 1.50,
                        "total_cost": 3.10
                    },
                    "subscription": {
                        "status": "active",
                        "expires_at": datetime.utcnow() + timedelta(days=30),
                        "auto_renew": True
                    }
                }
                
                response = client.get("/api/numbers/phone_1/usage")
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["phone_number"] == "+15551234567"
                assert data["usage"]["sms_sent"] == 100
                assert data["costs"]["total_cost"] == "3.1"
    
    def test_get_phone_number_usage_with_date_range(self, client, mock_user):
        """Test getting phone number usage with custom date range"""
        with patch('services.auth_service.get_current_active_user', return_value=mock_user):
            with patch('services.phone_number_service.PhoneNumberService.get_usage_statistics') as mock_stats:
                mock_stats.return_value = {
                    "phone_number_id": "phone_1",
                    "phone_number": "+15551234567",
                    "period_start": datetime(2024, 1, 1),
                    "period_end": datetime(2024, 1, 31),
                    "usage": {"sms_sent": 50, "sms_received": 25, "voice_minutes": 15},
                    "costs": {"sms_cost": 0.50, "voice_cost": 0.30, "monthly_fee": 1.50, "total_cost": 2.30},
                    "subscription": {"status": "active", "expires_at": datetime.utcnow() + timedelta(days=30), "auto_renew": True}
                }
                
                response = client.get("/api/numbers/phone_1/usage?start_date=2024-01-01&end_date=2024-01-31")
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert "2024-01-01" in data["period_start"]
                assert "2024-01-31" in data["period_end"]
    
    def test_get_supported_countries_success(self, client, mock_user):
        """Test getting supported countries"""
        with patch('services.auth_service.get_current_active_user', return_value=mock_user):
            response = client.get("/api/numbers/countries")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["countries"]) > 0
            
            # Check US is included
            us_country = next((c for c in data["countries"] if c["code"] == "US"), None)
            assert us_country is not None
            assert us_country["name"] == "United States"
            assert "sms" in us_country["available_capabilities"]
    
    def test_phone_number_health_check(self, client):
        """Test phone number service health check"""
        response = client.get("/api/numbers/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "phone_numbers"
        assert "number_marketplace" in data["features"]

class TestPhoneNumberAPIValidation:
    """Test API input validation"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def mock_user(self):
        return User(
            id="test_user_1",
            email="test@example.com",
            username="testuser",
            is_active=True
        )
    
    def test_purchase_invalid_phone_number(self, client, mock_user):
        """Test purchasing with invalid phone number format"""
        with patch('services.auth_service.get_current_active_user', return_value=mock_user):
            purchase_data = {
                "phone_number": "invalid_number",
                "auto_renew": True
            }
            
            response = client.post("/api/numbers/purchase", json=purchase_data)
            # The validation would happen in the service layer
            assert response.status_code in [400, 422]
    
    def test_get_available_numbers_invalid_country(self, client, mock_user):
        """Test getting available numbers with invalid country code"""
        with patch('services.auth_service.get_current_active_user', return_value=mock_user):
            with patch('services.phone_number_service.PhoneNumberService.search_available_numbers') as mock_search:
                mock_search.side_effect = ValueError("Invalid country code")
                
                response = client.get("/api/numbers/available/INVALID")
                assert response.status_code == 500  # Service error
    
    def test_renew_invalid_months(self, client, mock_user):
        """Test renewing with invalid number of months"""
        with patch('services.auth_service.get_current_active_user', return_value=mock_user):
            renewal_data = {
                "renewal_months": 0  # Invalid: must be >= 1
            }
            
            response = client.put("/api/numbers/phone_1/renew", json=renewal_data)
            assert response.status_code == 422  # Validation error

class TestPhoneNumberAPIErrorHandling:
    """Test API error handling"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def mock_user(self):
        return User(id="test_user_1", email="test@example.com", username="testuser")
    
    def test_service_unavailable_error(self, client, mock_user):
        """Test handling service unavailable errors"""
        with patch('services.auth_service.get_current_active_user', return_value=mock_user):
            with patch('services.phone_number_service.PhoneNumberService.search_available_numbers') as mock_search:
                mock_search.side_effect = Exception("Service unavailable")
                
                response = client.get("/api/numbers/available/US")
                assert response.status_code == 500
                assert "Failed to get available numbers" in response.json()["detail"]
    
    def test_database_error_handling(self, client, mock_user):
        """Test handling database errors"""
        with patch('services.auth_service.get_current_active_user', return_value=mock_user):
            with patch('services.phone_number_service.PhoneNumberService.get_owned_numbers') as mock_owned:
                mock_owned.side_effect = Exception("Database connection failed")
                
                response = client.get("/api/numbers/owned")
                assert response.status_code == 500
                assert "Failed to get owned numbers" in response.json()["detail"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])