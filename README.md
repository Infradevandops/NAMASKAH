# 🚀 SMSPROJ - Enterprise Communication Platform

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Security](https://img.shields.io/badge/security-hardened-brightgreen.svg)](#security)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Production-ready SMS verification and communication platform** with enterprise security, AI-powered features, and comprehensive API coverage.

---

## ⚡ Quick Start

```bash
# Clone and setup
git clone <repository-url> && cd smsproj
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Start development server
uvicorn main:app --reload

# Access platform
open http://localhost:8000
```

**🎯 Ready in 30 seconds** - All services work in mock mode by default.

---

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   FastAPI       │    │   Services      │
│   Bootstrap 5   │◄──►│   + WebSocket   │◄──►│   SMS/AI/Auth   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                       ┌─────────────────┐
                       │   Database      │
                       │   PostgreSQL    │
                       └─────────────────┘
```

### Core Components
- **FastAPI Backend**: High-performance async API
- **JWT Authentication**: Secure token-based auth
- **WebSocket**: Real-time communication
- **Mock Services**: Zero-cost development
- **Docker Ready**: Production deployment

---

## 🔐 Security Features

### ✅ **Security Hardened**
- **XSS Protection**: Input sanitization & output encoding
- **CSRF Protection**: Token-based request validation  
- **JWT Security**: Secure token handling with expiration
- **Rate Limiting**: API abuse prevention
- **Input Validation**: Phone numbers, emails, content
- **Security Headers**: CORS, CSP, HSTS ready

### 🛡️ **Production Security**
```python
# Automatic input sanitization
from security import security_utils
safe_content = security_utils.sanitize_html(user_input)

# CSRF protection for state-changing operations
from security import csrf_protection
token = csrf_protection.generate_token(session_id)
```

---

## 🚀 Features

### 📱 **SMS & Verification**
- **TextVerified Integration**: 100+ services (WhatsApp, Google, etc.)
- **Multi-Provider SMS**: Twilio, Vonage, mock for development
- **Auto Code Extraction**: Smart verification code detection
- **International Support**: Global phone number handling

### 🤖 **AI-Powered**
- **Groq AI Integration**: Message analysis & suggestions
- **Intent Detection**: Automatic message categorization
- **Response Suggestions**: Context-aware reply generation
- **Sentiment Analysis**: Message mood detection

### 💬 **Real-Time Communication**
- **WebSocket Chat**: Instant messaging
- **Typing Indicators**: Live user activity
- **Message Status**: Delivered/read receipts
- **Conversation Management**: Organized chat history

### 📊 **Enterprise Ready**
- **User Management**: Role-based access control
- **Analytics Dashboard**: Usage metrics & insights
- **API Documentation**: Interactive OpenAPI docs
- **Health Monitoring**: System status endpoints

---

## 🛠️ Installation & Setup

### 📋 **Prerequisites**
- Python 3.11+
- Docker (optional)
- Git

### ⚡ **Development Setup**

```bash
# 1. Clone repository
git clone <repository-url>
cd smsproj

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment (optional)
cp .env.example .env
# Edit .env with your API keys

# 5. Start development server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 🐳 **Docker Deployment**

```bash
# Development
docker-compose up -d

# Production
docker-compose -f docker-compose.yml up -d

# With custom environment
docker-compose --env-file .env.production up -d
```

### ☁️ **Cloud Deployment**

#### **Railway** (Recommended)
```bash
# One-click deploy
railway login
railway link
railway up
```

#### **Render**
- Uses included `render.yaml`
- Automatic deployments from Git
- Built-in PostgreSQL & Redis

#### **Heroku**
```bash
heroku create your-app-name
heroku addons:create heroku-postgresql:mini
heroku addons:create heroku-redis:mini
git push heroku main
```

---

## 📚 API Documentation

### 🏥 **System Endpoints**
```http
GET  /health              # System health check
GET  /docs                # Interactive API documentation  
GET  /api/info            # Platform information
```

### 🔐 **Authentication**
```http
POST /api/auth/register   # User registration
POST /api/auth/login      # User login
POST /api/auth/refresh    # Token refresh
GET  /api/auth/me         # Current user info
```

### 📱 **SMS & Communication**
```http
POST /api/sms/send                    # Send SMS
GET  /api/conversations               # Get conversations
POST /api/conversations/{id}/messages # Send message
GET  /api/conversations/{id}/messages # Get messages
```

### 🔍 **Verification Services**
```http
POST /api/verification/create         # Create verification
GET  /api/verification/{id}/number    # Get temp number
GET  /api/verification/{id}/messages  # Get SMS codes
GET  /api/verification/{id}/status    # Check status
DELETE /api/verification/{id}         # Cancel verification
```

### 🤖 **AI Features**
```http
POST /api/ai/suggest-response         # Get AI suggestions
POST /api/ai/analyze-intent          # Analyze message
GET  /api/ai/help/{service}          # Contextual help
```

### 📞 **Phone Management**
```http
GET  /api/numbers/available/{country} # Available numbers
POST /api/numbers/purchase            # Purchase number
GET  /api/numbers/owned               # User's numbers
```

**📖 Full Documentation**: Visit `/docs` when server is running

---

## 💡 Usage Examples

### 🔥 **Quick Demo**
```bash
# Test all features
python demo_platform.py

# Health check
curl http://localhost:8000/health

# Send SMS
curl -X POST "http://localhost:8000/api/sms/send" \
  -H "Content-Type: application/json" \
  -d '{"to_number": "+1234567890", "message": "Hello World!"}'
```

### 📱 **Service Verification**
```python
import httpx

# Create WhatsApp verification
response = await httpx.post("http://localhost:8000/api/verification/create", 
    json={"service_name": "whatsapp", "capability": "sms"}
)
verification_id = response.json()["verification_id"]

# Get temporary number
number_response = await httpx.get(
    f"http://localhost:8000/api/verification/{verification_id}/number"
)
temp_number = number_response.json()["phone_number"]
print(f"Use this number: {temp_number}")

# Check for codes
codes_response = await httpx.get(
    f"http://localhost:8000/api/verification/{verification_id}/messages"
)
codes = codes_response.json()["messages"]
```

### 🤖 **AI Integration**
```python
# Analyze message intent
response = await httpx.post("http://localhost:8000/api/ai/analyze-intent",
    params={"message": "I need help with verification"}
)
analysis = response.json()
print(f"Intent: {analysis['intent']}, Sentiment: {analysis['sentiment']}")

# Get response suggestions
response = await httpx.post("http://localhost:8000/api/ai/suggest-response",
    json={
        "conversation_history": [
            {"role": "user", "content": "Hi, I need help"},
            {"role": "assistant", "content": "How can I help you?"}
        ]
    }
)
suggestion = response.json()["suggestion"]
```

---

## 🔧 Configuration

### 🌍 **Environment Variables**

```bash
# Application
APP_NAME=SMSPROJ
PORT=8000
DEBUG=false

# Security
JWT_SECRET_KEY=your-super-secret-key-here
JWT_EXPIRE_MINUTES=30
CORS_ORIGINS=https://yourdomain.com

# Services (Optional - uses mocks if not provided)
TEXTVERIFIED_API_KEY=your_textverified_key
TEXTVERIFIED_EMAIL=your_email@domain.com
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE_NUMBER=+1234567890
GROQ_API_KEY=your_groq_key

# Database (Optional - uses SQLite if not provided)
DATABASE_URL=postgresql://user:pass@localhost/db
REDIS_URL=redis://localhost:6379

# Development
USE_MOCK_TWILIO=true
LOG_LEVEL=INFO
```

### 🎛️ **Feature Toggles**
```python
# Mock mode for development (no charges)
USE_MOCK_TWILIO=true

# Enable AI features
GROQ_API_KEY=your_key_here

# Enable real SMS
TWILIO_ACCOUNT_SID=your_sid_here
```

---

## 🧪 Testing

### 🔬 **Run Tests**
```bash
# All tests
pytest

# With coverage
pytest --cov=. --cov-report=html

# Specific tests
pytest tests/test_main.py
pytest tests/test_auth.py

# Frontend tests
npm test  # If you have Node.js setup
```

### 🎯 **Test Coverage**
- **Backend**: 85%+ coverage
- **API Endpoints**: 100% coverage
- **Security**: Comprehensive security tests
- **Integration**: End-to-end testing

---

## 📈 Performance & Monitoring

### ⚡ **Performance Features**
- **Async/Await**: Non-blocking operations
- **Connection Pooling**: Database optimization
- **Caching**: Redis for session storage
- **Rate Limiting**: API protection
- **Lazy Loading**: Efficient resource usage

### 📊 **Monitoring**
```bash
# Health check
curl http://localhost:8000/health

# Metrics endpoint
curl http://localhost:8000/metrics

# System info
curl http://localhost:8000/api/info
```

### 🚨 **Alerts & Logging**
- **Structured Logging**: JSON format
- **Error Tracking**: Comprehensive error handling
- **Performance Metrics**: Response time tracking
- **Security Events**: Authentication & authorization logs

---

## 🔒 Security Best Practices

### ✅ **Implemented Security**
- [x] Input sanitization (XSS prevention)
- [x] CSRF protection for state-changing operations
- [x] JWT token security with expiration
- [x] Rate limiting on all endpoints
- [x] SQL injection prevention (SQLAlchemy ORM)
- [x] Secure password hashing (bcrypt)
- [x] HTTPS ready (security headers)
- [x] Environment variable security

### 🛡️ **Production Security Checklist**
```bash
# 1. Update all secrets
JWT_SECRET_KEY=$(openssl rand -base64 32)

# 2. Enable HTTPS
FORCE_HTTPS=true

# 3. Set secure CORS
CORS_ORIGINS=https://yourdomain.com

# 4. Enable rate limiting
RATE_LIMIT_ENABLED=true

# 5. Use strong database passwords
DATABASE_URL=postgresql://user:$(openssl rand -base64 16)@host/db
```

---

## 🚀 Deployment Guide

### 🌐 **Production Deployment**

#### **1. Environment Setup**
```bash
# Create production environment file
cp .env.example .env.production

# Update with production values
JWT_SECRET_KEY=$(openssl rand -base64 32)
DATABASE_URL=postgresql://user:pass@prod-db:5432/smsproj
REDIS_URL=redis://prod-redis:6379
DEBUG=false
```

#### **2. Docker Production**
```bash
# Build production image
docker build -t smsproj:latest .

# Run with production compose
docker-compose -f docker-compose.yml up -d

# Scale services
docker-compose up -d --scale app=3
```

#### **3. Database Migration**
```bash
# Run migrations
docker-compose exec app alembic upgrade head

# Create admin user
docker-compose exec app python -c "
from auth.security import create_admin_user
create_admin_user('admin@company.com', 'secure_password')
"
```

### 📊 **Scaling**
- **Horizontal**: Multiple app instances behind load balancer
- **Database**: PostgreSQL with read replicas
- **Cache**: Redis cluster for high availability
- **CDN**: Static assets via CloudFront/CloudFlare

---

## 🤝 Contributing

### 🔧 **Development Workflow**
```bash
# 1. Fork and clone
git clone https://github.com/yourusername/smsproj.git

# 2. Create feature branch
git checkout -b feature/amazing-feature

# 3. Make changes and test
pytest
black .
flake8 .

# 4. Commit and push
git commit -m "Add amazing feature"
git push origin feature/amazing-feature

# 5. Create Pull Request
```

### 📝 **Code Standards**
- **Python**: Black formatting, flake8 linting
- **Security**: All inputs sanitized, CSRF protected
- **Testing**: 85%+ coverage required
- **Documentation**: Docstrings for all functions

---

## 📄 License & Support

### 📜 **License**
MIT License - see [LICENSE](LICENSE) file

### 🆘 **Support**
- **Documentation**: `/docs` endpoint when running
- **Issues**: [GitHub Issues](https://github.com/yourusername/smsproj/issues)
- **Security**: security@yourdomain.com
- **Commercial**: enterprise@yourdomain.com

### 🌟 **Enterprise Features**
- Priority support
- Custom integrations
- Advanced analytics
- SLA guarantees
- Dedicated infrastructure

---

## 🎯 Roadmap

### ✅ **Current (v1.1)**
- SMS verification with 100+ services
- AI-powered conversation assistance
- Real-time WebSocket communication
- Enterprise security features
- Docker deployment ready

### 🔄 **Next (v1.2)**
- Voice calling capabilities
- Mobile app (React Native)
- Advanced analytics dashboard
- Multi-tenant architecture
- Kubernetes deployment

### 🚀 **Future (v2.0)**
- Video calling
- Team collaboration features
- Advanced AI features
- Global CDN deployment
- Enterprise SSO integration

---

**🏆 Production-ready SMS platform with enterprise security and AI features**

*Built with ❤️ for developers who need reliable communication infrastructure*