"""System endpoint tests"""
import pytest

def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "2.0.0"
    assert "timestamp" in data

def test_services_list(client):
    """Test services list endpoint"""
    response = client.get("/services/list")
    assert response.status_code == 200
    data = response.json()
    assert "categories" in data or "uncategorized" in data

def test_root_endpoint(client):
    """Test root endpoint returns HTML"""
    response = client.get("/")
    assert response.status_code == 200

def test_app_endpoint(client):
    """Test app endpoint returns HTML"""
    response = client.get("/app")
    assert response.status_code == 200

def test_analytics_dashboard(client, auth_headers):
    """Test analytics endpoint"""
    response = client.get("/analytics/dashboard", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_verifications" in data
    assert "total_spent" in data
    assert "success_rate" in data
