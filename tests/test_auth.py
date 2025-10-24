"""Authentication endpoint tests"""

import pytest


def test_register_success(client):
    """Test user registration"""
    response = client.post(
        "/auth/register",
        json={"email": "newuser@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert data["credits"] == 5.0
    assert "referral_code" in data


def test_register_duplicate_email(client, test_user):
    """Test registration with existing email"""
    response = client.post(
        "/auth/register", json={"email": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_login_success(client, test_user):
    """Test user login"""
    response = client.post(
        "/auth/login", json={"email": "test@example.com", "password": "testpass123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert "credits" in data


def test_login_invalid_credentials(client):
    """Test login with wrong password"""
    response = client.post(
        "/auth/login", json={"email": "test@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401


def test_get_current_user(client, auth_headers):
    """Test getting current user info"""
    response = client.get("/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "credits" in data


def test_get_current_user_no_token(client):
    """Test accessing protected endpoint without token"""
    response = client.get("/auth/me")
    assert response.status_code == 403
