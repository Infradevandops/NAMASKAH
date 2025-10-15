# 📡 Namaskah SMS - API Examples

Complete API usage examples with curl, Python, and JavaScript.

---

## 🔐 Authentication

### Register New User

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepass123"
  }'
```

**Response:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user_id": "user_1234567890",
  "credits": 5.0,
  "referral_code": "ABC123",
  "email_verified": false
}
```

### Login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepass123"
  }'
```

### Get Current User

```bash
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 📱 SMS Verification

### Create Verification

```bash
curl -X POST http://localhost:8000/verify/create \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "whatsapp",
    "capability": "sms"
  }'
```

**Response:**
```json
{
  "id": "12345",
  "service_name": "whatsapp",
  "phone_number": "+1234567890",
  "status": "pending",
  "cost": 0.50,
  "remaining_credits": 4.50
}
```

### Get SMS Messages

```bash
curl http://localhost:8000/verify/12345/messages \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "verification_id": "12345",
  "messages": [
    "Your WhatsApp code is 123-456",
    "Use 123456 to verify your WhatsApp"
  ]
}
```

### Cancel Verification

```bash
curl -X DELETE http://localhost:8000/verify/12345 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 💰 Wallet Management

### Fund Wallet (Paystack)

```bash
curl -X POST http://localhost:8000/wallet/paystack/initialize \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 10.00,
    "payment_method": "paystack"
  }'
```

### Fund Wallet (Crypto)

```bash
curl -X POST http://localhost:8000/wallet/crypto/address \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 20.00,
    "payment_method": "bitcoin"
  }'
```

**Response:**
```json
{
  "address": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
  "amount": 20.0,
  "currency": "BITCOIN",
  "payment_id": "crypto_user_1234567890",
  "qr_code": "https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=...",
  "explorer_url": "https://blockchair.com/bitcoin/address/...",
  "instructions": "Send exactly $20.0 USD worth of BITCOIN to the address above"
}
```

### Transaction History

```bash
curl http://localhost:8000/transactions/history \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🔑 API Keys

### Create API Key

```bash
curl -X POST http://localhost:8000/api-keys/create \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production API Key"
  }'
```

**Response:**
```json
{
  "key": "nsk_AbCdEfGhIjKlMnOpQrStUvWxYz123456",
  "name": "Production API Key",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### List API Keys

```bash
curl http://localhost:8000/api-keys/list \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🪝 Webhooks

### Create Webhook

```bash
curl -X POST http://localhost:8000/webhooks/create \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-server.com/webhook"
  }'
```

### Webhook Payload (Received)

When SMS arrives, your webhook receives:

```json
{
  "verification_id": "12345",
  "messages": [
    "Your verification code is 123456"
  ],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## 📊 Analytics

### Get Dashboard Analytics

```bash
curl http://localhost:8000/analytics/dashboard \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "total_verifications": 42,
  "total_spent": 21.0,
  "success_rate": 95.2,
  "popular_services": [
    {"service": "whatsapp", "count": 15},
    {"service": "telegram", "count": 10}
  ],
  "recent_verifications": 8,
  "daily_usage": [
    {"date": "2024-01-15", "count": 5},
    {"date": "2024-01-14", "count": 3}
  ]
}
```

---

## 🎁 Referrals

### Get Referral Stats

```bash
curl http://localhost:8000/referrals/stats \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "referral_code": "ABC123",
  "total_referrals": 5,
  "total_earnings": 5.0,
  "referral_link": "http://localhost:8000/app?ref=ABC123",
  "referred_users": [
    {
      "email": "friend@example.com",
      "joined_at": "2024-01-10T08:00:00Z",
      "reward": 1.0
    }
  ]
}
```

---

## 🐍 Python SDK Example

```python
import requests

class NamaskahClient:
    def __init__(self, token):
        self.base_url = "http://localhost:8000"
        self.token = token
        self.headers = {"Authorization": f"Bearer {token}"}
    
    def create_verification(self, service_name):
        r = requests.post(
            f"{self.base_url}/verify/create",
            headers=self.headers,
            json={"service_name": service_name}
        )
        return r.json()
    
    def get_messages(self, verification_id):
        r = requests.get(
            f"{self.base_url}/verify/{verification_id}/messages",
            headers=self.headers
        )
        return r.json()["messages"]
    
    def get_balance(self):
        r = requests.get(f"{self.base_url}/auth/me", headers=self.headers)
        return r.json()["credits"]

# Usage
client = NamaskahClient("YOUR_TOKEN")

# Create verification
verification = client.create_verification("whatsapp")
print(f"Phone: {verification['phone_number']}")

# Wait for SMS (poll every 5 seconds)
import time
for _ in range(12):  # Try for 1 minute
    messages = client.get_messages(verification['id'])
    if messages:
        print(f"Code received: {messages[0]}")
        break
    time.sleep(5)

# Check balance
balance = client.get_balance()
print(f"Remaining: ₵{balance}")
```

---

## 🌐 JavaScript/Node.js Example

```javascript
const axios = require('axios');

class NamaskahClient {
  constructor(token) {
    this.baseURL = 'http://localhost:8000';
    this.token = token;
    this.headers = { Authorization: `Bearer ${token}` };
  }

  async createVerification(serviceName) {
    const { data } = await axios.post(
      `${this.baseURL}/verify/create`,
      { service_name: serviceName },
      { headers: this.headers }
    );
    return data;
  }

  async getMessages(verificationId) {
    const { data } = await axios.get(
      `${this.baseURL}/verify/${verificationId}/messages`,
      { headers: this.headers }
    );
    return data.messages;
  }

  async getBalance() {
    const { data } = await axios.get(
      `${this.baseURL}/auth/me`,
      { headers: this.headers }
    );
    return data.credits;
  }
}

// Usage
(async () => {
  const client = new NamaskahClient('YOUR_TOKEN');

  // Create verification
  const verification = await client.createVerification('telegram');
  console.log(`Phone: ${verification.phone_number}`);

  // Poll for messages
  for (let i = 0; i < 12; i++) {
    const messages = await client.getMessages(verification.id);
    if (messages.length > 0) {
      console.log(`Code: ${messages[0]}`);
      break;
    }
    await new Promise(resolve => setTimeout(resolve, 5000));
  }

  // Check balance
  const balance = await client.getBalance();
  console.log(`Balance: ₵${balance}`);
})();
```

---

## 🔴 Error Responses

### 401 Unauthorized
```json
{
  "detail": "Invalid token"
}
```

### 402 Payment Required
```json
{
  "detail": "Insufficient credits. Need ₵0.50, have ₵0.25"
}
```

### 404 Not Found
```json
{
  "detail": "Verification not found"
}
```

### 429 Rate Limit
```json
{
  "detail": "Rate limit exceeded. Max 100 requests per minute."
}
```

---

## 📚 Additional Resources

- **Interactive Docs**: http://localhost:8000/docs
- **OpenAPI Spec**: http://localhost:8000/openapi.json
- **Health Check**: http://localhost:8000/health
- **Services List**: http://localhost:8000/services/list

---

**Need Help?** support@namaskah.app
