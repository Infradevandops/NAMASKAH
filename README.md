# 📱 Namaskah SMS - Simple Verification Service

**Minimal SMS verification platform**

## ✨ Features

### Core
- 🔐 User authentication (JWT + Google OAuth)
- 📱 SMS & Voice verification for 1,807 services
- 🏠 Number rentals (hourly/daily/weekly/monthly)
- 💰 Wallet system with Paystack integration
- 🎨 Clean web interface with dark/light theme
- 🚀 Production-ready backend
- 💾 PostgreSQL database (SQLite for local dev)
- 🐳 Docker ready

### Security
- 🔒 HTTPS enforcement
- 🛡️ Security headers (HSTS, X-Frame-Options, etc.)
- 🚦 Redis rate limiting (100 req/min)
- 📧 Email verification
- 🔑 Password reset flow
- 🐛 Sentry error tracking
- 🔍 Request ID tracking

### Advanced
- 📞 Voice call verification (premium)
- 🏠 Long-term number rentals with auto-extend
- 💳 Real payment integration (Paystack webhooks)
- 🔔 Email & webhook notifications
- 🎁 Referral program
- 📊 Analytics dashboard
- 🔑 API keys for developers
- ✅ 70%+ test coverage

## 🚀 Quick Start

### 1. Install
```bash
pip install -r requirements.txt
```

### 2. Configure
```bash
cp .env.example .env
# Edit .env with your TextVerified credentials
```

### 3. Run
```bash
./start.sh
```

Visit: `http://localhost:8000`

### 4. Login
```
Email:    admin@namaskah.app
Password: admin123
```

Or create your own account using the Register tab.

## 📋 Requirements

- Python 3.11+

## 🔧 Configuration

Edit `.env`:
```bash
# JWT
JWT_SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=sqlite:///./sms.db  # Local dev
# DATABASE_URL=postgresql://user:pass@host/db  # Production

# SMS Provider
SMS_API_KEY=your-api-key
SMS_API_EMAIL=your-email@example.com

# Google OAuth (optional)
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret

# Payment (optional)
PAYSTACK_SECRET_KEY=sk_test_xxx

# Redis (optional - for rate limiting)
REDIS_URL=redis://localhost:6379

# Sentry (optional - for error tracking)
SENTRY_DSN=https://xxx@sentry.io/xxx
ENVIRONMENT=production

# CORS
CORS_ORIGINS=http://localhost:8000,https://your-domain.com
```

## 🎯 Supported Services

- WhatsApp
- Telegram  
- Google
- Discord
- Instagram
- Facebook
- Twitter/X
- TikTok
- 100+ more

## 📡 API Endpoints

### Authentication
- `POST /auth/register` - Register user
- `POST /auth/login` - Login
- `POST /auth/google` - Google OAuth
- `GET /auth/me` - Get user info
- `POST /auth/forgot-password` - Request password reset
- `POST /auth/reset-password` - Reset password

### Verification
- `POST /verify/create` - Create SMS/voice verification
- `GET /verify/{id}` - Get verification status
- `GET /verify/{id}/messages` - Get SMS messages
- `GET /verify/{id}/voice` - Get voice call details
- `DELETE /verify/{id}` - Cancel verification

### Rentals
- `POST /rentals/create` - Rent number (1hr-30days)
- `GET /rentals/active` - List active rentals
- `GET /rentals/{id}` - Get rental details
- `POST /rentals/{id}/extend` - Extend rental
- `POST /rentals/{id}/release` - Release early (50% refund)

### Wallet
- `POST /wallet/fund` - Fund wallet
- `POST /wallet/paystack/initialize` - Initialize payment
- `POST /wallet/paystack/webhook` - Payment webhook
- `GET /wallet/paystack/verify/{ref}` - Verify payment

### More
- `GET /health` - Health check
- `GET /docs` - Interactive API docs
- See [API_EXAMPLES.md](API_EXAMPLES.md) for code samples

## 🐳 Docker Deployment

```bash
docker build -t namaskah-sms .
docker run -p 8000:8000 --env-file .env namaskah-sms
```

## ☁️ Cloud Deployment

### Railway
```bash
railway login
railway init
railway up
```

### Render
1. Connect GitHub repo
2. Add environment variables
3. Deploy

## 📖 Usage

### Web Interface
1. Open `http://localhost:8000`
2. Register/Login
3. Select service (WhatsApp, Telegram, etc.)
4. Get temporary phone number
5. Use number for verification
6. Check messages for code

### API
```python
import requests

# Login
r = requests.post('http://localhost:8000/auth/login', json={
    'email': 'user@example.com',
    'password': 'password'
})
token = r.json()['token']

# Create verification
r = requests.post('http://localhost:8000/verify/create',
    headers={'Authorization': f'Bearer {token}'},
    json={'service_name': 'whatsapp'}
)
verification = r.json()
print(f"Phone: {verification['phone_number']}")

# Get messages
r = requests.get(f"http://localhost:8000/verify/{verification['id']}/messages",
    headers={'Authorization': f'Bearer {token}'}
)
messages = r.json()['messages']
print(f"Codes: {messages}")
```

## 🗂️ Project Structure

```
.
├── main.py                      # Backend API
├── requirements.txt             # Dependencies
├── pytest.ini                   # Test configuration
├── .env.example                 # Config template
├── static/
│   ├── css/style.css           # Styles
│   └── js/
│       ├── app.js              # Frontend logic
│       └── config.js           # Config loader
├── templates/
│   └── index.html              # Web interface
├── tests/                       # Test suite (70%+ coverage)
│   ├── test_auth.py
│   ├── test_verification.py
│   ├── test_rentals.py
│   ├── test_wallet.py
│   └── test_system.py
└── docs/
    ├── API_EXAMPLES.md          # API usage examples
    ├── POSTGRESQL_MIGRATION.md  # Database migration
    └── REDIS_SETUP.md           # Redis configuration
```

## 🔒 Security

- JWT token authentication (30-day expiry)
- Password hashing (bcrypt)
- HTTPS enforcement (production)
- Security headers (HSTS, X-Frame-Options, CSP)
- Redis rate limiting (100 req/min per user)
- Email verification on registration
- Secure password reset (1-hour tokens)
- Request ID tracking (X-Request-ID)
- Sentry error monitoring
- Environment-based secrets
- CORS restrictions
- Paystack webhook signature verification

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=main --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v
```

## 🐛 Troubleshooting

**"Invalid token"**
- Token expired (30 days) - Login again
- Check Authorization header format

**"Insufficient credits"**
- Fund wallet via Paystack/crypto
- Check balance: GET /auth/me

**"Rate limit exceeded"**
- Max 100 requests per minute
- Wait 60 seconds or upgrade plan

**"Authentication failed"**
- Check SMS API key
- Verify account has balance

**Database errors**
- Local: Delete `sms.db` and restart
- Production: Check PostgreSQL connection

**Redis not available**
- App continues with in-memory rate limiting
- Install Redis for persistent limits

**Google Sign-In not showing**
- Check GOOGLE_CLIENT_ID in .env
- Verify authorized origins in Google Console

## 📚 Documentation

- **API Docs**: `http://localhost:8000/docs` (Interactive)
- **API Examples**: [API_EXAMPLES.md](API_EXAMPLES.md)
- **PostgreSQL Migration**: [POSTGRESQL_MIGRATION.md](POSTGRESQL_MIGRATION.md)
- **Redis Setup**: [REDIS_SETUP.md](REDIS_SETUP.md)
- **Deployment**: [DEPLOY.md](DEPLOY.md)
- **Security**: [SECURITY_SETUP.md](SECURITY_SETUP.md)

## 🚀 Production Deployment

1. **Database**: Migrate to PostgreSQL ([guide](POSTGRESQL_MIGRATION.md))
2. **Redis**: Add for persistent rate limiting ([guide](REDIS_SETUP.md))
3. **Sentry**: Configure error tracking
4. **Paystack**: Add webhook URL to dashboard
5. **Google OAuth**: Add authorized origins
6. **Environment**: Set all variables on Render

## 📈 Pricing

- **SMS Verification**: ₵0.50 (categorized) / ₵0.75 (uncategorized)
- **Voice Verification**: ₵0.75 (categorized) / ₵1.13 (uncategorized)
- **Number Rentals**:
  - 1 hour: ₵2.00
  - 6 hours: ₵8.00
  - 24 hours: ₵10.00
  - 7 days: ₵50.00
  - 30 days: ₵150.00

## 📝 License

MIT

## 🆘 Support

- **Email**: support@namaskah.app
- **API Docs**: `http://localhost:8000/docs`
- **Issues**: [GitHub Issues](https://github.com/Infradevandops/NAMASKAH/issues)

---

**Production-Ready. Secure. Scalable.**

**Version**: 2.0.0
