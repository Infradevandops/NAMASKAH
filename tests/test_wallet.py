"""Wallet and transaction tests"""
import pytest

def test_fund_wallet(client, auth_headers):
    """Test wallet funding"""
    response = client.post("/wallet/fund",
        headers=auth_headers,
        json={"amount": 10.0, "payment_method": "paystack"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert data["amount"] == 10.0
    assert data["new_balance"] == 15.0  # 5 initial + 10

def test_fund_wallet_minimum(client, auth_headers):
    """Test minimum funding amount"""
    response = client.post("/wallet/fund",
        headers=auth_headers,
        json={"amount": 3.0, "payment_method": "paystack"}
    )
    assert response.status_code == 400
    assert "Minimum" in response.json()["detail"]

def test_transaction_history(client, auth_headers):
    """Test getting transaction history"""
    response = client.get("/transactions/history", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "transactions" in data
    assert isinstance(data["transactions"], list)

def test_paystack_initialize(client, auth_headers):
    """Test Paystack payment initialization"""
    response = client.post("/wallet/paystack/initialize",
        headers=auth_headers,
        json={"amount": 10.0, "payment_method": "paystack"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "authorization_url" in data
    assert "reference" in data

def test_crypto_address(client, auth_headers):
    """Test crypto payment address generation"""
    response = client.post("/wallet/crypto/address",
        headers=auth_headers,
        json={"amount": 20.0, "payment_method": "bitcoin"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "address" in data
    assert "qr_code" in data
    assert data["currency"] == "BITCOIN"
