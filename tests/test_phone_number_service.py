#!/usr/bin/env python3
"""
Unit tests for Phone Number Service
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session

from services.phone_number_service import PhoneNumberService
from models.user_models import User, PhoneNumber

class TestPhoneNumberService:
    """Test phone number service functionality"""
    
    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_user(self):
        return User(
            id="test_user_1",
            email="test@example.com",
            username="testuser",
            subscription_plan="BASIC",
            is_active=True
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
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
    
    @pytest.fixture
    def phone_service(self, mock_db):
        return PhoneNumberService(mock_db)
    
    @pytest.mark.asyncio
    async def test_search_available_numbers_us(self, phone_service):
        """Test searching for available US numbers"""
        numbers, count = await phone_service.search_available_numbers("US", "555", ["sms"], 5)
        
        assert count == 5
        assert len(numbers) == 5
        
        for number in numbers:
            assert number["country_code"] == "US"
            assert number["area_code"] == "555"
            assert number["phone_number"].startswith("+1555")
            assert "sms" in number["capabilities"]
            assert isinstance(number["monthly_cost"], Decimal)
    
    @pytest.mark.asyncio
    async def test_search_available_numbers_gb(self, phone_service):
        """Test searching for available GB numbers"""
        numbers, count = await phone_service.search_available_numbers("GB", None, ["sms"], 3)
        
        assert count == 3
        assert len(numbers) == 3
        
        for number in numbers:
            assert number["country_code"] == "GB"
            assert number["phone_number"].startswith("+44700")
            assert number["region"] == "United Kingdom"
    
    @pytest.mark.asyncio
    async def test_purchase_phone_number_success(self, phone_service, mock_user):
        """Test successful phone number purchase"""
        phone_service.db.query.return_value.filter.return_value.first.side_effect = [
            mock_user,  # User exists
            None        # Number not already owned
        ]
        phone_service.db.query.return_value.filter.return_value.count.return_value = 0  # No existing numbers
        
        result = await phone_service.purchase_phone_number("test_user_1", "+15551234567")
        
        assert result["success"] is True
        assert "transaction_id" in result
        assert result["message"] == "Phone number purchased successfully"
        phone_service.db.add.assert_called_once()
        phone_service.db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_purchase_phone_number_user_not_found(self, phone_service):
        """Test phone number purchase with non-existent user"""
        phone_service.db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(ValueError, match="User not found"):
            await phone_service.purchase_phone_number("nonexistent_user", "+15551234567")
    
    @pytest.mark.asyncio
    async def test_purchase_phone_number_already_owned(self, phone_service, mock_user, mock_phone_number):
        """Test phone number purchase when number is already owned"""
        mock_phone_number.status = "active"
        phone_service.db.query.return_value.filter.return_value.first.side_effect = [
            mock_user,           # User exists
            mock_phone_number    # Number already owned
        ]
        
        with pytest.raises(ValueError, match="Phone number is already owned"):
            await phone_service.purchase_phone_number("test_user_1", "+15551234567")
    
    @pytest.mark.asyncio
    async def test_purchase_phone_number_limit_exceeded(self, phone_service, mock_user):
        """Test phone number purchase when user limit is exceeded"""
        phone_service.db.query.return_value.filter.return_value.first.side_effect = [
            mock_user,  # User exists
            None        # Number not owned
        ]
        phone_service.db.query.return_value.filter.return_value.count.return_value = 3  # At limit for BASIC plan
        
        with pytest.raises(ValueError, match="Maximum number limit reached"):
            await phone_service.purchase_phone_number("test_user_1", "+15551234567")
    
    @pytest.mark.asyncio
    async def test_get_owned_numbers(self, phone_service, mock_phone_number):
        """Test getting owned phone numbers"""
        phone_service.db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_phone_number]
        phone_service.db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.count.return_value = 1
        
        numbers, count = await phone_service.get_owned_numbers("test_user_1")
        
        assert count == 1
        assert len(numbers) == 1
        assert numbers[0].phone_number == "+15551234567"
    
    @pytest.mark.asyncio
    async def test_renew_phone_number_success(self, phone_service, mock_phone_number):
        """Test successful phone number renewal"""
        phone_service.db.query.return_value.filter.return_value.first.return_value = mock_phone_number
        
        result = await phone_service.renew_phone_number("test_user_1", "phone_1", 2)
        
        assert result["success"] is True
        assert "transaction_id" in result
        assert result["message"] == "Phone number renewed for 2 month(s)"
        assert result["total_cost"] == Decimal("3.00")  # 1.50 * 2 months
        phone_service.db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_renew_phone_number_not_found(self, phone_service):
        """Test phone number renewal when number not found"""
        phone_service.db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(ValueError, match="Phone number not found or not owned by user"):
            await phone_service.renew_phone_number("test_user_1", "nonexistent_phone")
    
    @pytest.mark.asyncio
    async def test_renew_phone_number_cancelled(self, phone_service, mock_phone_number):
        """Test phone number renewal when number is cancelled"""
        mock_phone_number.status = "cancelled"
        phone_service.db.query.return_value.filter.return_value.first.return_value = mock_phone_number
        
        with pytest.raises(ValueError, match="Phone number cannot be renewed"):
            await phone_service.renew_phone_number("test_user_1", "phone_1")
    
    @pytest.mark.asyncio
    async def test_cancel_phone_number_success(self, phone_service, mock_phone_number):
        """Test successful phone number cancellation"""
        phone_service.db.query.return_value.filter.return_value.first.return_value = mock_phone_number
        
        result = await phone_service.cancel_phone_number("test_user_1", "phone_1")
        
        assert result["success"] is True
        assert result["message"] == "Phone number subscription cancelled"
        assert mock_phone_number.status == "cancelled"
        assert mock_phone_number.auto_renew is False
        phone_service.db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cancel_phone_number_already_cancelled(self, phone_service, mock_phone_number):
        """Test phone number cancellation when already cancelled"""
        mock_phone_number.status = "cancelled"
        phone_service.db.query.return_value.filter.return_value.first.return_value = mock_phone_number
        
        with pytest.raises(ValueError, match="Phone number is already cancelled"):
            await phone_service.cancel_phone_number("test_user_1", "phone_1")
    
    @pytest.mark.asyncio
    async def test_get_usage_statistics(self, phone_service, mock_phone_number):
        """Test getting usage statistics"""
        mock_phone_number.monthly_sms_sent = 100
        mock_phone_number.total_sms_received = 50
        mock_phone_number.monthly_voice_minutes = 30
        phone_service.db.query.return_value.filter.return_value.first.return_value = mock_phone_number
        
        stats = await phone_service.get_usage_statistics("test_user_1", "phone_1")
        
        assert stats["phone_number"] == "+15551234567"
        assert stats["usage"]["sms_sent"] == 100
        assert stats["usage"]["sms_received"] == 50
        assert stats["usage"]["voice_minutes"] == 30
        assert stats["costs"]["sms_cost"] == Decimal("1.00")  # 100 * 0.01
        assert stats["costs"]["monthly_fee"] == Decimal("1.50")
    
    @pytest.mark.asyncio
    async def test_track_usage_sms_sent(self, phone_service, mock_phone_number):
        """Test tracking SMS sent usage"""
        phone_service.db.query.return_value.filter.return_value.first.return_value = mock_phone_number
        
        result = await phone_service.track_usage("+15551234567", "sms_sent", 5)
        
        assert result is True
        assert mock_phone_number.total_sms_sent == 5
        assert mock_phone_number.monthly_sms_sent == 5
        phone_service.db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_track_usage_sms_received(self, phone_service, mock_phone_number):
        """Test tracking SMS received usage"""
        phone_service.db.query.return_value.filter.return_value.first.return_value = mock_phone_number
        
        result = await phone_service.track_usage("+15551234567", "sms_received", 3)
        
        assert result is True
        assert mock_phone_number.total_sms_received == 3
        phone_service.db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_track_usage_voice_minutes(self, phone_service, mock_phone_number):
        """Test tracking voice minutes usage"""
        phone_service.db.query.return_value.filter.return_value.first.return_value = mock_phone_number
        
        result = await phone_service.track_usage("+15551234567", "voice_minutes", 10)
        
        assert result is True
        assert mock_phone_number.total_voice_minutes == 10
        assert mock_phone_number.monthly_voice_minutes == 10
        phone_service.db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_track_usage_number_not_found(self, phone_service):
        """Test tracking usage for non-existent number"""
        phone_service.db.query.return_value.filter.return_value.first.return_value = None
        
        result = await phone_service.track_usage("+15551234567", "sms_sent", 1)
        
        assert result is False
    
    def test_generate_mock_numbers_us(self, phone_service):
        """Test generating mock US numbers"""
        numbers = phone_service._generate_mock_numbers("US", "555", 3)
        
        assert len(numbers) == 3
        for number in numbers:
            assert number.startswith("+1555")
    
    def test_generate_mock_numbers_gb(self, phone_service):
        """Test generating mock GB numbers"""
        numbers = phone_service._generate_mock_numbers("GB", None, 2)
        
        assert len(numbers) == 2
        for number in numbers:
            assert number.startswith("+44700")
    
    def test_extract_area_code(self, phone_service):
        """Test extracting area code from phone number"""
        area_code = phone_service._extract_area_code("+15551234567")
        assert area_code == "555"
        
        area_code = phone_service._extract_area_code("+447001234567")
        assert area_code is None  # Not US number
    
    def test_get_region_for_country(self, phone_service):
        """Test getting region for country code"""
        assert phone_service._get_region_for_country("US") == "United States"
        assert phone_service._get_region_for_country("GB") == "United Kingdom"
        assert phone_service._get_region_for_country("XX") == "Unknown"
    
    def test_get_max_numbers_for_plan(self, phone_service):
        """Test getting max numbers for subscription plan"""
        assert phone_service._get_max_numbers_for_plan("FREE") == 1
        assert phone_service._get_max_numbers_for_plan("BASIC") == 3
        assert phone_service._get_max_numbers_for_plan("PREMIUM") == 10
        assert phone_service._get_max_numbers_for_plan("ENTERPRISE") == 50
        assert phone_service._get_max_numbers_for_plan("UNKNOWN") == 1

class TestPhoneNumberServiceIntegration:
    """Integration tests for phone number service"""
    
    @pytest.mark.asyncio
    async def test_full_purchase_workflow(self):
        """Test complete phone number purchase workflow"""
        # This would be an integration test with real database
        # For now, just verify the workflow structure
        
        workflow_steps = [
            "search_available_numbers",
            "purchase_phone_number", 
            "get_owned_numbers",
            "track_usage",
            "get_usage_statistics",
            "renew_phone_number"
        ]
        
        service = PhoneNumberService(Mock())
        
        for step in workflow_steps:
            assert hasattr(service, step)
            assert callable(getattr(service, step))

if __name__ == "__main__":
    pytest.main([__file__, "-v"])