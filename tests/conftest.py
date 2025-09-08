"""
Pytest configuration and fixtures for CumApp tests.
"""
import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock

# Set test environment variables
os.environ.update({
    "TEXTVERIFIED_API_KEY": "test_key",
    "TEXTVERIFIED_EMAIL": "test@example.com",
    "TWILIO_ACCOUNT_SID": "test_sid",
    "TWILIO_AUTH_TOKEN": "test_token",
    "TWILIO_PHONE_NUMBER": "+1234567890",
    "GROQ_API_KEY": "test_groq_key",
    "GROQ_MODEL": "llama3-8b-8192",
    "DATABASE_URL": "sqlite:///test.db",
    "REDIS_URL": "redis://localhost:6379/1",
    "JWT_SECRET_KEY": "test_jwt_secret"
})

from main import app

@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)

@pytest.fixture
def mock_twilio_client():
    """Mock Twilio client for testing."""
    mock_client = Mock()
    mock_message = Mock()
    mock_message.sid = "test_message_sid"
    mock_client.messages.create.return_value = mock_message
    return mock_client

@pytest.fixture
def mock_textverified_client():
    """Mock TextVerified client for testing."""
    mock_client = AsyncMock()
    mock_client.check_balance.return_value = 10.50
    mock_client.create_verification.return_value = "test_verification_id"
    mock_client.get_verification_number.return_value = "+1234567890"
    mock_client.get_sms_messages.return_value = ["123456"]
    mock_client.cancel_verification.return_value = True
    mock_client.get_service_list.return_value = [
        {"name": "whatsapp", "cost": 0.10},
        {"name": "telegram", "cost": 0.08}
    ]
    return mock_client

@pytest.fixture
def mock_groq_client():
    """Mock Groq AI client for testing."""
    mock_client = AsyncMock()
    mock_client.suggest_sms_response.return_value = "Thank you for your message!"
    mock_client.analyze_message_intent.return_value = {
        "intent": "question",
        "sentiment": "neutral",
        "urgency": "medium",
        "suggested_tone": "helpful",
        "confidence": 0.85
    }
    mock_client.help_with_service_setup.return_value = "Here's how to set up WhatsApp..."
    return mock_client

@pytest.fixture
def sample_verification_request():
    """Sample verification request data."""
    return {
        "service_name": "whatsapp",
        "capability": "sms"
    }

@pytest.fixture
def sample_sms_request():
    """Sample SMS request data."""
    return {
        "to_number": "+1234567890",
        "message": "Test message",
        "from_number": "+0987654321"
    }

@pytest.fixture
def sample_ai_request():
    """Sample AI request data."""
    return {
        "conversation_history": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"}
        ],
        "context": "Friendly conversation"
    }