"""Verification endpoint tests"""
import pytest
from unittest.mock import patch, MagicMock

@patch('main.tv_client')
def test_create_verification_sms(mock_tv, client, auth_headers):
    """Test creating SMS verification"""
    mock_tv.create_verification.return_value = "12345"
    mock_tv.get_verification.return_value = {"number": "+1234567890"}
    
    response = client.post("/verify/create", 
        headers=auth_headers,
        json={"service_name": "whatsapp", "capability": "sms"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["phone_number"] == "+1234567890"
    assert data["capability"] == "sms"
    assert data["cost"] == 0.5

@patch('main.tv_client')
def test_create_verification_voice(mock_tv, client, auth_headers):
    """Test creating voice verification with premium pricing"""
    mock_tv.create_verification.return_value = "12345"
    mock_tv.get_verification.return_value = {"number": "+1234567890"}
    
    response = client.post("/verify/create",
        headers=auth_headers,
        json={"service_name": "whatsapp", "capability": "voice"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["capability"] == "voice"
    assert data["cost"] == 0.75  # 50% premium

def test_create_verification_insufficient_credits(client, auth_headers):
    """Test verification with insufficient credits"""
    # Drain credits first
    for _ in range(10):
        try:
            client.post("/verify/create",
                headers=auth_headers,
                json={"service_name": "test", "capability": "sms"}
            )
        except:
            pass
    
    response = client.post("/verify/create",
        headers=auth_headers,
        json={"service_name": "whatsapp", "capability": "sms"}
    )
    assert response.status_code == 402
    assert "Insufficient credits" in response.json()["detail"]

def test_get_verification_history(client, auth_headers):
    """Test getting verification history"""
    response = client.get("/verifications/history", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "verifications" in data
    assert isinstance(data["verifications"], list)
