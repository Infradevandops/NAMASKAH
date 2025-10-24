"""Rental endpoint tests"""

from unittest.mock import patch

import pytest


@patch("main.tv_client")
def test_create_rental(mock_tv, client, auth_headers):
    """Test creating number rental"""
    mock_tv.create_verification.return_value = "rental_123"
    mock_tv.get_verification.return_value = {"number": "+1234567890"}

    response = client.post(
        "/rentals/create",
        headers=auth_headers,
        json={"service_name": "whatsapp", "duration_hours": 24, "auto_extend": False},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["phone_number"] == "+1234567890"
    assert data["duration_hours"] == 24
    assert data["cost"] == 10.0
    assert data["status"] == "active"


def test_rental_pricing(client, auth_headers):
    """Test rental pricing tiers"""
    mock_tv = patch("main.tv_client")
    mock_tv.create_verification.return_value = "test"
    mock_tv.get_verification.return_value = {"number": "+1234567890"}

    # 1 hour = ₵2
    # 6 hours = ₵8
    # 24 hours = ₵10
    # 168 hours (7 days) = ₵50
    # 720 hours (30 days) = ₵150

    pricing_tests = [(1, 2.0), (6, 8.0), (24, 10.0), (168, 50.0), (720, 150.0)]

    for hours, expected_cost in pricing_tests:
        from main import calculate_rental_cost

        assert calculate_rental_cost(hours) == expected_cost


def test_list_active_rentals(client, auth_headers):
    """Test listing active rentals"""
    response = client.get("/rentals/active", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "rentals" in data
    assert isinstance(data["rentals"], list)


@patch("main.tv_client")
def test_extend_rental(mock_tv, client, auth_headers):
    """Test extending rental duration"""
    mock_tv.create_verification.return_value = "rental_123"
    mock_tv.get_verification.return_value = {"number": "+1234567890"}

    # Create rental first
    create_response = client.post(
        "/rentals/create",
        headers=auth_headers,
        json={"service_name": "whatsapp", "duration_hours": 1, "auto_extend": False},
    )
    rental_id = create_response.json()["id"]

    # Extend it
    response = client.post(
        f"/rentals/{rental_id}/extend",
        headers=auth_headers,
        json={"additional_hours": 1},
    )
    assert response.status_code == 200
    data = response.json()
    assert "new_expires_at" in data
    assert data["cost"] == 2.0


@patch("main.tv_client")
def test_release_rental(mock_tv, client, auth_headers):
    """Test early release with refund"""
    mock_tv.create_verification.return_value = "rental_123"
    mock_tv.get_verification.return_value = {"number": "+1234567890"}

    # Create rental
    create_response = client.post(
        "/rentals/create",
        headers=auth_headers,
        json={"service_name": "whatsapp", "duration_hours": 24, "auto_extend": False},
    )
    rental_id = create_response.json()["id"]

    # Release immediately
    response = client.post(f"/rentals/{rental_id}/release", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "released"
    assert data["refund"] >= 0
