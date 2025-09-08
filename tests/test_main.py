"""
Tests for main FastAPI application endpoints.
"""
import pytest
from fastapi.testclient import TestClient


def test_health_endpoint(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app_name"] == "CumApp"
    assert data["version"] == "1.0.0"
    assert "services" in data


def test_app_info_endpoint(client):
    """Test the application info endpoint."""
    response = client.get("/api/info")
    assert response.status_code == 200
    
    data = response.json()
    assert data["app_name"] == "CumApp"
    assert data["version"] == "1.0.0"
    assert "features" in data
    assert "endpoints" in data


def test_home_endpoint(client):
    """Test the home page endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    # Should return HTML content
    assert "text/html" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_sms_send_endpoint_missing_twilio(client, sample_sms_request):
    """Test SMS send endpoint when Twilio is not configured."""
    response = client.post("/api/sms/send", json=sample_sms_request)
    # Should return 503 if Twilio is not configured
    assert response.status_code in [200, 503]


def test_openapi_docs(client):
    """Test that OpenAPI documentation is accessible."""
    response = client.get("/docs")
    assert response.status_code == 200
    
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    data = response.json()
    assert data["info"]["title"] == "CumApp - Communication Platform"