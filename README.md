# 🚀 CumApp - Enterprise Communication Platform

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Security](https://img.shields.io/badge/security-hardened-brightgreen.svg)](#security)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Production-ready SMS verification and communication platform** with enterprise security, AI-powered features, and comprehensive API coverage.

---

## ⚡ Quick Start

```bash
# Clone and setup
git clone <repository-url> && cd cumapp
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Start development server
uvicorn main:app --reload

# Access platform
open http://localhost:8000
```

**🎯 Ready in 30 seconds** - All services work in mock mode by default.

---

## 🌳 **Branch Structure**

This repository contains **6 development phases** showing the complete evolution of CumApp:

### **📋 Available Branches:**

1. **`phase-1-mvp`** - Basic SMS functionality
2. **`phase-2-core-features`** - Complete API & services  
3. **`phase-3-ui-enhancement`** - Professional interfaces
4. **`phase-4-security-hardening`** - Production security
5. **`phase-5-analytics-monitoring`** - Analytics & monitoring
6. **`phase-6-production-ready`** - Complete platform ⭐

**🎯 For production deployment, use `phase-6-production-ready` branch**

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

## 🎯 **User Interfaces**

### **Main Communication Hub** - `/hub`
Complete SMS and verification interface where users can:
- Send SMS to any phone number
- Get temporary numbers for verification
- Verify accounts on 100+ services
- Chat with AI assistant
- Real-time messaging

### **Analytics Dashboard** - `/analytics`
Real-time platform monitoring:
- Usage statistics and metrics
- Activity feed and tracking
- Performance monitoring
- Visual charts and graphs

### **API Documentation** - `/docs`
Interactive API testing:
- Complete endpoint documentation
- Test all features directly
- Authentication examples
- Response schemas

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
cd cumapp

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
```

### ☁️ **Cloud Deployment**

#### **Render** (Recommended)
- Uses included `render.yaml`
- Automatic deployments from Git
- Built-in PostgreSQL & Redis

#### **Railway**
```bash
railway login && railway up
```

#### **Heroku**
```bash
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

**📖 Full Documentation**: Visit `/docs` when server is running

---

## 🔧 Configuration

### 🌍 **Environment Variables**

```bash
# Application
APP_NAME=CumApp
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
```

---

## 🔒 Security Features

### ✅ **Implemented Security**
- [x] Input sanitization (XSS prevention)
- [x] CSRF protection for state-changing operations
- [x] JWT token security with expiration
- [x] Rate limiting on all endpoints
- [x] SQL injection prevention (SQLAlchemy ORM)
- [x] Secure password hashing (bcrypt)
- [x] HTTPS ready (security headers)
- [x] Environment variable security

---

## 🚀 Deployment Guide

### 🌐 **Production Deployment**

#### **1. Environment Setup**
```bash
# Create production environment file
cp .env.example .env.production

# Update with production values
JWT_SECRET_KEY=$(openssl rand -base64 32)
DATABASE_URL=postgresql://user:pass@prod-db:5432/cumapp
REDIS_URL=redis://prod-redis:6379
DEBUG=false
```

#### **2. Docker Production**
```bash
# Build production image
docker build -t cumapp:latest .

# Run with production compose
docker-compose -f docker-compose.yml up -d
```

---

## 🤝 Contributing

### 🔧 **Development Workflow**
```bash
# 1. Fork and clone
git clone https://github.com/yourusername/cumapp.git

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

---

## 📄 License & Support

### 📜 **License**
MIT License - see [LICENSE](LICENSE) file

### 🆘 **Support**
- **Documentation**: `/docs` endpoint when running
- **Issues**: [GitHub Issues](https://github.com/yourusername/cumapp/issues)
- **Security**: security@yourdomain.com
- **Commercial**: enterprise@yourdomain.com

---

## 🎯 Roadmap

### ✅ **Current (v1.0)**
- SMS verification with 100+ services
- AI-powered conversation assistance
- Real-time WebSocket communication
- Enterprise security features
- Docker deployment ready

### 🔄 **Next (v1.1)**
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