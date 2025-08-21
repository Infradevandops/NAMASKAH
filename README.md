# 📘 **SMSPROJ - Comprehensive Communication Platform**

**SMSPROJ** is a powerful FastAPI-based communication platform that combines TextVerified and Twilio APIs to provide comprehensive SMS services including service verification, international messaging, and AI-powered communication assistance.

---

## 🔸 **Platform Overview**

### 🚀 **Core Capabilities**

1. **Service Verification Hub**
   * Use TextVerified API to get temporary numbers for service verification
   * Support for WhatsApp, Google, Telegram, and 100+ other services
   * Automated SMS code retrieval and display

2. **International SMS & Voice Communication**
   * Send/receive SMS and make/receive voice calls globally using Twilio
   * Smart routing with country-code optimization for both SMS and calls
   * Choose between personal number or purchase local numbers for better rates
   * Full voice features: call recording, forwarding, conference calls

3. **Dedicated Number Management**
   * Purchase numbers by subscription or one-time payment
   * Country-specific numbers for optimal delivery rates
   * Long-term communication capabilities (1+ months)

4. **AI-Powered Messaging**
   * Embedded language model for conversation assistance
   * Response suggestions and contextual help
   * Privacy-focused local processing

5. **Flexible Usage Models**
   * One-time verification: Temporary numbers via TextVerified
   * Long-term communication: Dedicated numbers via Twilio
   * Cost optimization: Smart routing based on destination

### 🛠 **Technology Stack**

* **Backend**: FastAPI (Python 3.11+)
* **APIs**: Twilio (SMS/Voice) + TextVerified (Verification)
* **Database**: SQLAlchemy with PostgreSQL
* **Caching**: Redis for token management
* **AI**: Local transformer models (privacy-focused)
* **Authentication**: JWT tokens
* **Deployment**: Docker + Docker Compose

---

## 🔸 **Quick Start**

### 📋 **Prerequisites**

1. **Python 3.11+** installed
2. **TextVerified Account**: Get API key from [TextVerified](https://www.textverified.com)
3. **Twilio Account**: Get credentials from [Twilio Console](https://console.twilio.com)
4. **Redis** (for caching) - optional but recommended

### ⚙️ **Environment Setup**

1. **Clone and Install Dependencies**
```bash
git clone <repository-url>
cd SMSPROJ
pip install -r requirements.txt
```

2. **Environment Variables**
Create a `.env` file:
```env
# TextVerified API
TEXTVERIFIED_API_KEY=your_textverified_api_key
TEXTVERIFIED_EMAIL=your_email@example.com

# Twilio API
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number

# Database
DATABASE_URL=postgresql://user:password@localhost/communication_db

# Redis (optional)
REDIS_URL=redis://localhost:6379

# JWT Secret
JWT_SECRET_KEY=your_jwt_secret_key

# AI Model (optional)
AI_MODEL_PATH=./models/local_model
```

3. **Run the Application**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 🔸 **API Endpoints**

### 🔐 **Authentication**
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `POST /api/auth/refresh` - Refresh JWT token

### 📱 **Verification Services**
- `POST /api/verification/create` - Create service verification
- `GET /api/verification/{id}/number` - Get verification number
- `GET /api/verification/{id}/messages` - Get received SMS codes
- `DELETE /api/verification/{id}` - Cancel verification

### 💬 **SMS & Voice Communication**
- `POST /api/sms/send` - Send SMS with routing options
- `POST /api/sms/receive` - Webhook for incoming SMS
- `POST /api/voice/call` - Make outbound voice call
- `POST /api/voice/receive` - Webhook for incoming calls
- `POST /api/voice/record` - Start/stop call recording
- `POST /api/voice/forward` - Forward calls to another number
- `POST /api/voice/conference` - Create conference call
- `GET /api/conversations/{user_id}` - Get SMS and call history
- `GET /api/sms/suggestions` - Get AI response suggestions

### 📞 **Number Management**
- `GET /api/numbers/available/{country_code}` - List available numbers
- `POST /api/numbers/purchase` - Purchase dedicated number
- `GET /api/numbers/user/{user_id}` - Get user's numbers
- `DELETE /api/numbers/{number_id}` - Release number

### 💳 **Subscriptions**
- `GET /api/subscriptions/plans` - List subscription plans
- `POST /api/subscriptions/subscribe` - Create subscription
- `GET /api/subscriptions/user/{user_id}` - Get user subscriptions

---

## 🔸 **Usage Examples**

### 📱 **Service Verification**

```python
import httpx

# Create verification for WhatsApp
response = await httpx.post("http://localhost:8000/api/verification/create", 
    json={"service_name": "whatsapp", "capability": "sms"},
    headers={"Authorization": "Bearer your_jwt_token"}
)
verification_id = response.json()["verification_id"]

# Get the temporary number
number_response = await httpx.get(f"http://localhost:8000/api/verification/{verification_id}/number")
temp_number = number_response.json()["number"]

print(f"Use this number for WhatsApp verification: {temp_number}")

# Poll for received SMS codes
messages_response = await httpx.get(f"http://localhost:8000/api/verification/{verification_id}/messages")
codes = messages_response.json()["messages"]
print(f"Verification codes: {codes}")
```

### 💬 **International SMS with Smart Routing**

```python
# Send SMS with routing optimization
response = await httpx.post("http://localhost:8000/api/sms/send",
    json={
        "to_number": "+44123456789",  # UK number
        "message": "Hello from the platform!",
        "routing_options": {
            "optimize_cost": True,
            "suggest_local_number": True
        }
    },
    headers={"Authorization": "Bearer your_jwt_token"}
)

routing_info = response.json()
print(f"Suggested routing: {routing_info['suggested_routing']}")
print(f"Cost comparison: {routing_info['cost_comparison']}")
```

### 📞 **Voice Calling with Smart Routing**

```python
# Make an international call with cost optimization
response = await httpx.post("http://localhost:8000/api/voice/call",
    json={
        "to_number": "+44123456789",  # UK number
        "from_number": "auto",  # Let system choose optimal number
        "routing_options": {
            "optimize_cost": True,
            "record_call": True,
            "max_duration": 1800  # 30 minutes
        }
    },
    headers={"Authorization": "Bearer your_jwt_token"}
)

call_info = response.json()
print(f"Call SID: {call_info['call_sid']}")
print(f"Using number: {call_info['from_number']}")
print(f"Estimated cost: ${call_info['estimated_cost']}")
```

### 📞 **Number Management**

```python
# Purchase a UK number for better rates
response = await httpx.post("http://localhost:8000/api/numbers/purchase",
    json={
        "country_code": "GB",
        "subscription_type": "monthly",
        "duration_months": 3
    },
    headers={"Authorization": "Bearer your_jwt_token"}
)

new_number = response.json()["phone_number"]
print(f"Purchased UK number: {new_number}")
```

---

## 🔸 **Docker Deployment**

### 🐳 **Docker Compose Setup**

```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/communication_db
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    volumes:
      - ./models:/app/models

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: communication_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

### 🚀 **Deploy**

```bash
# Build and start services
docker-compose up -d

# Run database migrations
docker-compose exec app alembic upgrade head

# Check logs
docker-compose logs -f app
```

---

## 🔸 **Features in Detail**

### 🎯 **Smart Routing Engine**

The platform automatically suggests the most cost-effective routing for international SMS:

1. **Cost Analysis**: Compares rates between your primary number and local numbers
2. **Country Matching**: Suggests numbers with closest country codes to destination
3. **Delivery Optimization**: Prioritizes local numbers for better delivery rates
4. **Real-time Pricing**: Shows cost comparisons before sending

### 🤖 **AI Assistant Integration**

- **Local Processing**: All AI features run locally for privacy
- **Context Awareness**: Understands conversation history
- **Response Suggestions**: Provides smart reply options
- **Intent Analysis**: Helps categorize and route messages

### 📊 **Analytics & Monitoring**

- **Usage Tracking**: Monitor SMS volume and costs
- **Performance Metrics**: Track delivery rates and response times
- **Cost Optimization**: Identify savings opportunities
- **Health Monitoring**: Real-time system status

---

## 🔸 **Development**

### 🧪 **Testing**

```bash
# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run with coverage
pytest --cov=app tests/
```

### 📝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### 🐛 **Troubleshooting**

**Common Issues:**

1. **TextVerified Authentication Failed**
   - Check API key and email in environment variables
   - Verify account balance

2. **Twilio SMS Delivery Issues**
   - Verify phone number format
   - Check Twilio account balance and permissions

3. **Database Connection Issues**
   - Ensure PostgreSQL is running
   - Check DATABASE_URL format

---

## 📄 **License**

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🤝 **Support**

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review the API examples

---

## 🚀 **Development Roadmap**

### **Phase 1: Core Platform (Current Release)**
- ✅ Basic SMS verification with TextVerified
- ✅ SMS communication with Twilio
- ✅ Docker containerization
- ✅ CI/CD pipeline with CircleCI
- ✅ Production deployment ready

### **Phase 2: Advanced Features (Future Releases)**
We can add the advanced features (AI, smart routing, voice calls) in subsequent releases after we have the core platform deployed and running:

- 🔄 **Smart International Routing**: Cost optimization and local number suggestions
- 🤖 **AI-Powered Messaging**: Local LLM integration for conversation assistance
- 📞 **Voice Calling**: Full voice capabilities with recording and forwarding
- 💳 **Advanced Subscriptions**: Flexible billing and number management
- 📊 **Analytics Dashboard**: Usage tracking and cost optimization insights

---

**Crafted with ❤️ You Will ❤️ It**