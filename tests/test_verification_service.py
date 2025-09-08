#!/usr/bin/env python3
"""
Unit tests for Enhanced Verification Service
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.user_models import Base, User, VerificationRequest, SubscriptionPlan
from services.verification_service import VerificationService, CodeExtractionService
from textverified_client import TextVerifiedClient

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
def mock_textverified_client():
    """Create mock TextVerified client"""
    client = Mock(spec=TextVerifiedClient)
    client.create_verification = AsyncMock(return_value="tv_123456")
    client.get_verification_number = AsyncMock(return_value="+1234567890")
    client.get_sms_messages = AsyncMock(return_value=[])
    client.cancel_verification = AsyncMock(return_value=True)
    return client

@pytest.fixture
def verification_service(db_session, mock_textverified_client):
    """Create verification service with mocked dependencies"""
    return VerificationService(db_session, mock_textverified_client)

class TestCodeExtractionService:
    """Test code extraction functionality"""
    
    def test_extract_basic_verification_codes(self):
        """Test extraction of basic verification codes"""
        test_cases = [
            ("Your verification code is 123456", ["123456"]),
            ("Code: 789012", ["789012"]),
            ("PIN 4567", ["4567"]),
            ("OTP: 987654", ["987654"]),
            ("345678 is your verification code", ["345678"]),
            ("Use code 111222 to verify", ["111222"]),
        ]
        
        for message, expected in test_cases:
            codes = CodeExtractionService.extract_verification_codes(message)
            assert codes == expected, f"Failed for message: {message}"
    
    def test_extract_service_specific_codes(self):
        """Test extraction of service-specific codes"""
        test_cases = [
            ("WhatsApp code: 123456", "whatsapp", ["123456"]),
            ("Your Google verification code is 789012", "google", ["789012"]),
            ("Telegram code 54321", "telegram", ["54321"]),
            ("Discord: 987654", "discord", ["987654"]),
        ]
        
        for message, service, expected in test_cases:
            codes = CodeExtractionService.extract_verification_codes(message, service)
            assert codes == expected, f"Failed for service {service}, message: {message}"
    
    def test_filter_invalid_codes(self):
        """Test filtering of invalid codes"""
        invalid_messages = [
            "Call us at 2023 for help",  # Year
            "Your order #12345678901 is ready",  # Too long
            "Code 123",  # Too short
            "No codes here",  # No codes
        ]
        
        for message in invalid_messages:
            codes = CodeExtractionService.extract_verification_codes(message)
            assert len(codes) == 0, f"Should not extract codes from: {message}"
    
    def test_identify_service_patterns(self):
        """Test service pattern identification"""
        message = "WhatsApp code: 123456. Use this to verify your account."
        result = CodeExtractionService.identify_service_patterns(message, "whatsapp")
        
        assert result['service_detected'] == True
        assert result['confidence'] > 0.5
        assert "123456" in result['extracted_codes']
        assert len(result['patterns_matched']) > 0

class TestVerificationService:
    """Test verification service functionality"""
    
    @pytest.mark.asyncio
    async def test_create_verification_success(self, verification_service, test_user, mock_textverified_client):
        """Test successful verification creation"""
        result = await verification_service.create_verification(
            user_id=test_user.id,
            service_name="whatsapp",
            capability="sms"
        )
        
        assert result.user_id == test_user.id
        assert result.service_name == "whatsapp"
        assert result.textverified_id == "tv_123456"
        assert result.status == "pending"
        
        mock_textverified_client.create_verification.assert_called_once_with(
            service_name="whatsapp",
            capability="sms"
        )
    
    @pytest.mark.asyncio
    async def test_create_verification_invalid_user(self, verification_service):
        """Test verification creation with invalid user"""
        with pytest.raises(ValueError, match="User .* not found"):
            await verification_service.create_verification(
                user_id="invalid-user",
                service_name="whatsapp"
            )
    
    @pytest.mark.asyncio
    async def test_create_verification_no_client(self, db_session, test_user):
        """Test verification creation without TextVerified client"""
        service = VerificationService(db_session, None)
        
        with pytest.raises(ValueError, match="TextVerified client not configured"):
            await service.create_verification(
                user_id=test_user.id,
                service_name="whatsapp"
            )
    
    @pytest.mark.asyncio
    async def test_get_verification_number(self, verification_service, test_user, mock_textverified_client):
        """Test getting verification phone number"""
        # Create verification first
        verification = await verification_service.create_verification(
            user_id=test_user.id,
            service_name="whatsapp"
        )
        
        # Get phone number
        phone_number = await verification_service.get_verification_number(
            user_id=test_user.id,
            verification_id=verification.id
        )
        
        assert phone_number == "+1234567890"
        mock_textverified_client.get_verification_number.assert_called_once_with("tv_123456")
    
    @pytest.mark.asyncio
    async def test_check_verification_messages_with_codes(self, verification_service, test_user, mock_textverified_client):
        """Test checking messages and extracting codes"""
        # Create verification
        verification = await verification_service.create_verification(
            user_id=test_user.id,
            service_name="whatsapp"
        )
        
        # Mock messages with verification code
        mock_textverified_client.get_sms_messages.return_value = [
            "Your WhatsApp verification code is 123456"
        ]
        
        messages = await verification_service.check_verification_messages(
            user_id=test_user.id,
            verification_id=verification.id
        )
        
        assert len(messages) == 1
        assert "123456" in messages[0]
        
        # Verify verification was completed
        verification_service.db.refresh(verification)
        assert verification.status == "completed"
        assert verification.verification_code == "123456"
        assert verification.completed_at is not None
    
    @pytest.mark.asyncio
    async def test_get_verification_history(self, verification_service, test_user):
        """Test getting verification history"""
        # Create multiple verifications
        await verification_service.create_verification(test_user.id, "whatsapp")
        await verification_service.create_verification(test_user.id, "google")
        await verification_service.create_verification(test_user.id, "telegram")
        
        # Get history
        history = await verification_service.get_verification_history(test_user.id)
        
        assert len(history) == 3
        services = [v.service_name for v in history]
        assert "whatsapp" in services
        assert "google" in services
        assert "telegram" in services
    
    @pytest.mark.asyncio
    async def test_get_verification_history_with_filters(self, verification_service, test_user):
        """Test getting verification history with filters"""
        # Create verifications
        v1 = await verification_service.create_verification(test_user.id, "whatsapp")
        v2 = await verification_service.create_verification(test_user.id, "google")
        
        # Update one to completed status
        v1.status = "completed"
        verification_service.db.commit()
        
        # Filter by status
        completed_history = await verification_service.get_verification_history(
            test_user.id,
            filters={'status': 'completed'}
        )
        
        assert len(completed_history) == 1
        assert completed_history[0].service_name == "whatsapp"
        
        # Filter by service name
        whatsapp_history = await verification_service.get_verification_history(
            test_user.id,
            filters={'service_name': 'whatsapp'}
        )
        
        assert len(whatsapp_history) == 1
        assert whatsapp_history[0].service_name == "whatsapp"
    
    @pytest.mark.asyncio
    async def test_search_verifications(self, verification_service, test_user):
        """Test searching verifications"""
        # Create verifications with different services
        v1 = await verification_service.create_verification(test_user.id, "whatsapp")
        v2 = await verification_service.create_verification(test_user.id, "google")
        
        # Add phone numbers
        v1.phone_number = "+1234567890"
        v2.phone_number = "+0987654321"
        verification_service.db.commit()
        
        # Search by service name
        results = await verification_service.search_verifications(test_user.id, "whatsapp")
        assert len(results) == 1
        assert results[0].service_name == "whatsapp"
        
        # Search by phone number
        results = await verification_service.search_verifications(test_user.id, "1234567890")
        assert len(results) == 1
        assert results[0].phone_number == "+1234567890"
    
    @pytest.mark.asyncio
    async def test_cancel_verification(self, verification_service, test_user, mock_textverified_client):
        """Test cancelling verification"""
        # Create verification
        verification = await verification_service.create_verification(
            user_id=test_user.id,
            service_name="whatsapp"
        )
        
        # Cancel verification
        result = await verification_service.cancel_verification(
            user_id=test_user.id,
            verification_id=verification.id
        )
        
        assert result == True
        mock_textverified_client.cancel_verification.assert_called_once_with("tv_123456")
        
        # Verify status updated
        verification_service.db.refresh(verification)
        assert verification.status == "cancelled"
    
    @pytest.mark.asyncio
    async def test_cancel_completed_verification(self, verification_service, test_user):
        """Test cancelling already completed verification"""
        # Create and complete verification
        verification = await verification_service.create_verification(
            user_id=test_user.id,
            service_name="whatsapp"
        )
        verification.status = "completed"
        verification_service.db.commit()
        
        # Try to cancel
        with pytest.raises(ValueError, match="Cannot cancel verification"):
            await verification_service.cancel_verification(
                user_id=test_user.id,
                verification_id=verification.id
            )
    
    @pytest.mark.asyncio
    async def test_get_verification_statistics(self, verification_service, test_user):
        """Test getting verification statistics"""
        # Create verifications with different statuses
        v1 = await verification_service.create_verification(test_user.id, "whatsapp")
        v2 = await verification_service.create_verification(test_user.id, "google")
        v3 = await verification_service.create_verification(test_user.id, "telegram")
        
        # Update statuses
        v1.status = "completed"
        v2.status = "completed"
        v3.status = "failed"
        verification_service.db.commit()
        
        # Get statistics
        stats = await verification_service.get_verification_statistics(test_user.id)
        
        assert stats['total_verifications'] == 3
        assert stats['completed_verifications'] == 2
        assert stats['success_rate'] == 66.67
        assert stats['status_breakdown']['completed'] == 2
        assert stats['status_breakdown']['failed'] == 1
        assert stats['service_usage']['whatsapp'] == 1
        assert stats['service_usage']['google'] == 1
        assert stats['service_usage']['telegram'] == 1
    
    @pytest.mark.asyncio
    async def test_export_verification_data_json(self, verification_service, test_user):
        """Test exporting verification data in JSON format"""
        # Create verifications
        v1 = await verification_service.create_verification(test_user.id, "whatsapp")
        v2 = await verification_service.create_verification(test_user.id, "google")
        
        # Export data
        export_result = await verification_service.export_verification_data(
            user_id=test_user.id,
            format_type="json"
        )
        
        assert export_result['format'] == 'json'
        assert export_result['user_id'] == test_user.id
        assert export_result['record_count'] == 2
        assert len(export_result['data']) == 2
        
        # Check data structure
        record = export_result['data'][0]
        assert 'id' in record
        assert 'service_name' in record
        assert 'status' in record
        assert 'created_at' in record
    
    @pytest.mark.asyncio
    async def test_export_verification_data_csv(self, verification_service, test_user):
        """Test exporting verification data in CSV format"""
        # Create verification
        await verification_service.create_verification(test_user.id, "whatsapp")
        
        # Export data
        export_result = await verification_service.export_verification_data(
            user_id=test_user.id,
            format_type="csv"
        )
        
        assert export_result['format'] == 'csv'
        assert 'csv_content' in export_result
        assert 'id,service_name' in export_result['csv_content']  # CSV headers
    
    @pytest.mark.asyncio
    async def test_verification_limits_free_user(self, verification_service, test_user):
        """Test verification limits for free users"""
        # Set user to free plan
        test_user.subscription_plan = SubscriptionPlan.FREE
        verification_service.db.commit()
        
        # Create 5 verifications (free limit)
        for i in range(5):
            await verification_service.create_verification(test_user.id, f"service{i}")
        
        # Try to create 6th verification (should fail)
        with pytest.raises(ValueError, match="Daily verification limit"):
            await verification_service.create_verification(test_user.id, "service6")
    
    @pytest.mark.asyncio
    async def test_get_user_verification_not_found(self, verification_service, test_user):
        """Test getting verification that doesn't exist or doesn't belong to user"""
        with pytest.raises(ValueError, match="Verification .* not found"):
            await verification_service._get_user_verification(test_user.id, "invalid-id")
    
    @pytest.mark.asyncio
    async def test_get_user_verification_wrong_user(self, verification_service, test_user, db_session):
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
        db_session.commit()
        
        # Create verification for other user
        verification = await verification_service.create_verification(other_user.id, "whatsapp")
        
        # Try to access with test_user
        with pytest.raises(ValueError, match="Verification .* not found"):
            await verification_service._get_user_verification(test_user.id, verification.id)

class TestVerificationServiceIntegration:
    """Integration tests for verification service"""
    
    @pytest.mark.asyncio
    async def test_complete_verification_workflow(self, verification_service, test_user, mock_textverified_client):
        """Test complete verification workflow from creation to completion"""
        # Step 1: Create verification
        verification = await verification_service.create_verification(
            user_id=test_user.id,
            service_name="whatsapp",
            capability="sms"
        )
        
        assert verification.status == "pending"
        
        # Step 2: Get phone number
        phone_number = await verification_service.get_verification_number(
            user_id=test_user.id,
            verification_id=verification.id
        )
        
        assert phone_number == "+1234567890"
        
        # Step 3: Check for messages (simulate receiving verification code)
        mock_textverified_client.get_sms_messages.return_value = [
            "Your WhatsApp verification code is 123456. Don't share this code."
        ]
        
        messages = await verification_service.check_verification_messages(
            user_id=test_user.id,
            verification_id=verification.id
        )
        
        assert len(messages) == 1
        
        # Step 4: Verify completion
        verification_service.db.refresh(verification)
        assert verification.status == "completed"
        assert verification.verification_code == "123456"
        assert verification.completed_at is not None
        
        # Step 5: Check history
        history = await verification_service.get_verification_history(test_user.id)
        assert len(history) == 1
        assert history[0].status == "completed"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])