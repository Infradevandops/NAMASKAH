# 🚀 **SMSPROJ - Advanced Communication Platform**

**SMSPROJ** is a modern, full-featured communication platform built with FastAPI that combines SMS messaging, phone verification services, and AI-powered conversation assistance. Perfect for businesses, developers, and individuals who need reliable communication tools.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## ✨ **Key Features**

### 🔐 **Phone Verification Services**
- **TextVerified Integration**: Get temporary numbers for 100+ services (WhatsApp, Google, Telegram, etc.)
- **Automated Code Retrieval**: Automatic SMS code extraction and display
- **Service Management**: Track verification requests and success rates
- **Multi-Service Support**: Support for all major platforms and services

### 💬 **Real-Time Communication**
- **SMS Messaging**: Send/receive SMS with external numbers
- **Real-Time Chat**: WebSocket-powered instant messaging
- **Conversation Management**: Organize chats with individuals and groups
- **Message History**: Persistent conversation storage and search

### 📱 **Phone Number Management**
- **Multi-Provider Support**: Twilio, Vonage, and mock providers for development
- **Smart Routing**: Cost optimization and delivery rate optimization
- **Number Purchasing**: Buy and manage phone numbers by country
- **Usage Analytics**: Track SMS volume, costs, and performance

### 🤖 **AI-Powered Features**
- **Message Analysis**: Intent detection and sentiment analysis using Groq AI
- **Response Suggestions**: AI-generated reply recommendations
- **Conversation Assistance**: Context-aware messaging help
- **Smart Templates**: Service-specific verification message templates

### 🏢 **Enterprise Ready**
- **User Management**: Multi-user support with role-based access
- **API Access**: RESTful API with authentication and rate limiting
- **Subscription Tiers**: Flexible pricing with usage limits
- **Analytics Dashboard**: Comprehensive usage and performance metrics

---

## 🛠 **Technology Stack**

- **Backend**: FastAPI (Python 3.9+)
- **Database**: SQLAlchemy + PostgreSQL (with SQLite for development)
- **Real-Time**: WebSockets + Redis
- **Authentication**: JWT tokens with bcrypt password hashing
- **SMS Providers**: Twilio, Vonage, Mock (for development)
- **AI**: Groq API for conversation assistance
- **Frontend**: Bootstrap 5 + Vanilla JavaScript
- **Deployment**: Docker + Docker Compose
- **Testing**: pytest with comprehensive test coverage

---

## 🚀 **Quick Start**

### 📋 **Prerequisites**

- **Python 3.9+** installed
- **Git** for version control
- **Optional**: TextVerified account for real verification services
- **Optional**: Groq API key for AI features

### ⚡ **Installation**

1. **Clone the Repository**
```bash
git clone https://github.com/yourusername/smsproj.git
cd smsproj
```

2. **Set Up Virtual Environment**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure Environment**
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your API keys (optional for demo)
# TEXTVERIFIED_API_KEY=your_key_here
# GROQ_API_KEY=your_groq_key_here
```

5. **Run the Application**
```bash
# Development mode with auto-reload
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Or use the setup script
python setup_project.py
```

6. **Access the Platform**
- **Dashboard**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Chat Interface**: http://localhost:8000/chat
- **Health Check**: http://localhost:8000/health

---

## � ***API Documentation**

### 🏥 **System Endpoints**
- `GET /health` - System health check
- `GET /api/info` - Platform information
- `GET /docs` - Interactive API documentation

### 📱 **SMS & Communication**
- `POST /api/sms/send` - Send SMS messages
- `GET /api/mock/sms/history` - Get SMS history (development)
- `POST /api/mock/sms/simulate-incoming` - Simulate incoming SMS
- `GET /api/mock/statistics` - Platform usage statistics

### � **VeSrification Services**
- `POST /api/verification/create` - Create TextVerified verification
- `GET /api/verification/{id}/number` - Get verification phone number
- `GET /api/verification/{id}/messages` - Retrieve SMS codes
- `GET /api/verification/{id}/status` - Check verification status
- `DELETE /api/verification/{id}` - Cancel verification

### 🤖 **AI Features**
- `POST /api/ai/suggest-response` - Get AI response suggestions
- `POST /api/ai/analyze-intent` - Analyze message intent and sentiment
- `GET /api/ai/help/{service}` - Get contextual help for services

### 📞 **Phone Number Management**
- `GET /api/numbers/available/{country}` - List available numbers by country
- `POST /api/numbers/purchase` - Purchase phone number
- `GET /api/numbers/owned` - Get user's owned numbers

### � **SReal-Time Communication**
- `WebSocket /ws/{user_id}` - Real-time messaging and notifications

> **📖 Full API Documentation**: Visit `/docs` when the server is running for interactive API documentation with request/response examples.

---

## � **Ussage Examples**

### �  **Quick Demo**

```bash
# Run the comprehensive demo
python demo_platform.py

# Test SMS functionality
curl -X POST "http://localhost:8000/api/sms/send" \
  -H "Content-Type: application/json" \
  -d '{"to_number": "+1234567890", "message": "Hello from SMSPROJ!"}'

# Check platform health
curl "http://localhost:8000/health"
```

### 📱 **Service Verification**

```python
import httpx

# Create verification for WhatsApp
response = await httpx.post("http://localhost:8000/api/verification/create", 
    json={"service_name": "whatsapp", "capability": "sms"}
)
verification_id = response.json()["verification_id"]

# Get the temporary number
number_response = await httpx.get(f"http://localhost:8000/api/verification/{verification_id}/number")
temp_number = number_response.json()["phone_number"]

print(f"Use this number for WhatsApp verification: {temp_number}")

# Check for received SMS codes
messages_response = await httpx.get(f"http://localhost:8000/api/verification/{verification_id}/messages")
codes = messages_response.json()["messages"]
print(f"Verification codes: {codes}")
```

### 💬 **SMS Communication**

```python
# Send SMS to external number
response = await httpx.post("http://localhost:8000/api/sms/send",
    json={
        "to_number": "+1234567890",
        "message": "Hello! This is a test message from SMSPROJ.",
        "from_number": "+1555000001"  # Your platform number
    }
)

if response.status_code == 200:
    result = response.json()
    print(f"SMS sent! Message ID: {result['message_sid']}")
```

### 🤖 **AI Message Analysis**

```python
# Analyze message intent and sentiment
response = await httpx.post("http://localhost:8000/api/ai/analyze-intent",
    params={"message": "I need help urgently with my verification!"}
)

analysis = response.json()
print(f"Intent: {analysis['intent']}")
print(f"Sentiment: {analysis['sentiment']}")
print(f"Urgency: {analysis['urgency']}")
```

### 📞 **Phone Number Management**

```python
# Get available numbers by country
response = await httpx.get("http://localhost:8000/api/numbers/available/US")
numbers = response.json()["available_numbers"]

for number in numbers[:3]:  # Show first 3
    print(f"Available: {number['phone_number']} - {number['monthly_cost']}/month")

# Purchase a number (mock implementation)
purchase_response = await httpx.post("http://localhost:8000/api/numbers/purchase",
    json={
        "phone_number": "+1555000001",
        "country_code": "US",
        "provider": "twilio"
    }
)
```

---

## � **DDeployment**

### **Development Mode**

```bash
# Quick start with setup script
python setup_project.py

# Manual start
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### **Docker Deployment**

```bash
# Build and run with Docker Compose
docker-compose up -d

# Check logs
docker-compose logs -f app

# Stop services
docker-compose down
```

### **Production Deployment**

```bash
# Use production compose file
docker-compose -f docker-compose.yml up -d

# With database migrations
docker-compose exec app alembic upgrade head
```

### **Cloud Deployment Options**

- **Railway**: One-click deployment with automatic scaling
- **Heroku**: Easy deployment with add-ons for PostgreSQL and Redis
- **DigitalOcean App Platform**: Managed containers with databases
- **AWS ECS/Fargate**: Full control with auto-scaling
- **Google Cloud Run**: Serverless container deployment

---

## 🎯 **Key Features in Detail**

### 🔄 **Development Mode**

The platform includes a comprehensive **mock mode** for development:

- **Mock SMS Service**: Realistic SMS simulation with delays and failure rates
- **No External Dependencies**: Develop without real API keys
- **Complete Feature Testing**: All functionality works in mock mode
- **Cost-Free Development**: No charges during development and testing

### 🤖 **AI-Powered Intelligence**

- **Message Analysis**: Intent detection, sentiment analysis, urgency assessment
- **Response Suggestions**: Context-aware reply recommendations
- **Conversation Assistance**: Smart templates and automated responses
- **Multi-Language Support**: AI features work across different languages

### 📊 **Analytics & Insights**

- **Real-Time Statistics**: Live usage metrics and performance data
- **Cost Tracking**: Detailed breakdown of SMS and verification costs
- **Success Rates**: Verification success rates by service and country
- **Usage Patterns**: Identify peak times and optimize resources

### 🔒 **Security & Privacy**

- **JWT Authentication**: Secure token-based authentication
- **API Rate Limiting**: Prevent abuse with configurable rate limits
- **Data Encryption**: Sensitive data encrypted at rest and in transit
- **Privacy First**: Optional local AI processing for sensitive conversations

---

## �  **Development**

### 🧪 **Testing**

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_main.py

# Run demo to test all features
python demo_platform.py
```

### 📁 **Project Structure**

```
smsproj/
├── api/                    # API route handlers
├── models/                 # Database models and schemas
├── services/               # Business logic and external integrations
├── templates/              # HTML templates
├── tests/                  # Test files
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── docker-compose.yml      # Docker configuration
└── README.md              # This file
```

### 🔧 **Configuration**

Key environment variables:

```env
# Development mode (uses mock services)
USE_MOCK_TWILIO=true

# API Keys (optional for demo)
TEXTVERIFIED_API_KEY=your_key_here
GROQ_API_KEY=your_groq_key_here

# Database (optional, uses SQLite by default)
DATABASE_URL=postgresql://user:pass@localhost/db

# Security
JWT_SECRET_KEY=your_secret_key_here
```

### 🐛 **Troubleshooting**

**Common Issues:**

1. **Port 8000 already in use**
   ```bash
   # Use different port
   uvicorn main:app --port 8001
   ```

2. **Missing dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **API keys not working**
   - Check `.env` file configuration
   - Verify API key validity
   - Use mock mode for development: `USE_MOCK_TWILIO=true`

---

## �️ **Roadmeap**

### **✅ Current Features (v1.0)**
- SMS messaging with mock and real providers
- TextVerified integration for phone verification
- AI-powered message analysis and suggestions
- Real-time WebSocket communication
- Interactive web dashboard
- Comprehensive API with documentation
- Docker deployment ready

### **🔄 In Development (v1.1)**
- User authentication and management
- Persistent conversation storage
- Enhanced chat interface
- Phone number purchasing workflow
- Advanced verification management

### **🚀 Planned Features (v2.0)**
- Voice calling capabilities
- Group chat and collaboration
- Advanced analytics dashboard
- Mobile app (React Native)
- Enterprise features and API

---

## 🤝 **Contributing**

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🆘 **Support**

- **Documentation**: Visit `/docs` when running the server
- **Issues**: [GitHub Issues](https://github.com/yourusername/smsproj/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/smsproj/discussions)
- **Demo**: Run `python demo_platform.py` for a comprehensive demo

---

## ⭐ **Show Your Support**

If you find this project helpful, please consider:
- ⭐ Starring the repository
- 🐛 Reporting bugs and issues
- 💡 Suggesting new features
- 🤝 Contributing code or documentation

---

**Built with ❤️ for the developer community**