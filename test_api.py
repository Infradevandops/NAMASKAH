"""Basic API tests for critical endpoints"""
import pytest
from fastapi.testclient import TestClient
from main import app
import os

# Set test environment
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

client = TestClient(app)

def test_health_check():
    """Test health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_register_user():
    """Test user registration"""
    response = client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "testpass123"
    })
    assert response.status_code == 200
    assert "token" in response.json()

def test_register_duplicate_email():
    """Test duplicate email registration"""
    # First registration
    client.post("/auth/register", json={
        "email": "duplicate@example.com",
        "password": "testpass123"
    })
    
    # Duplicate registration
    response = client.post("/auth/register", json={
        "email": "duplicate@example.com",
        "password": "testpass123"
    })
    assert response.status_code == 400

def test_login():
    """Test user login"""
    # Register first
    client.post("/auth/register", json={
        "email": "login@example.com",
        "password": "testpass123"
    })
    
    # Login
    response = client.post("/auth/login", json={
        "email": "login@example.com",
        "password": "testpass123"
    })
    assert response.status_code == 200
    assert "token" in response.json()

def test_login_invalid_credentials():
    """Test login with wrong password"""
    response = client.post("/auth/login", json={
        "email": "login@example.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401

def test_get_services_list():
    """Test services list endpoint"""
    response = client.get("/services/list")
    assert response.status_code == 200
    assert "categories" in response.json()

def test_get_service_status():
    """Test service status endpoint"""
    response = client.get("/services/status")
    assert response.status_code == 200
    assert "overall_status" in response.json()

def test_unauthorized_access():
    """Test accessing protected endpoint without token"""
    response = client.get("/auth/me")
    assert response.status_code == 403

def test_get_user_profile():
    """Test getting user profile with valid token"""
    # Register and get token
    reg_response = client.post("/auth/register", json={
        "email": "profile@example.com",
        "password": "testpass123"
    })
    token = reg_response.json()["token"]
    
    # Get profile
    response = client.get("/auth/me", headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200
    assert response.json()["email"] == "profile@example.com"

def test_create_verification_without_email_verification():
    """Test that unverified users cannot create verifications"""
    # Register
    reg_response = client.post("/auth/register", json={
        "email": "unverified@example.com",
        "password": "testpass123"
    })
    token = reg_response.json()["token"]
    
    # Try to create verification
    response = client.post("/verify/create", 
        headers={"Authorization": f"Bearer {token}"},
        json={"service_name": "whatsapp", "capability": "sms"}
    )
    assert response.status_code == 403
    assert "verify your email" in response.json()["detail"].lower()

def test_admin_stats_unauthorized():
    """Test admin endpoint without admin privileges"""
    # Register normal user
    reg_response = client.post("/auth/register", json={
        "email": "normaluser@example.com",
        "password": "testpass123"
    })
    token = reg_response.json()["token"]
    
    # Try to access admin stats
    response = client.get("/admin/stats", headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 403

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
