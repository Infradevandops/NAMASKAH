# Namaskah SMS Verification Platform

Enterprise-grade SMS verification service providing instant temporary phone numbers for 1,807+ online platforms with guaranteed delivery and automatic refunds.

## Core Features

### SMS Verification Service
- Instant temporary phone numbers for receiving SMS verification codes
- Support for 1,807+ services including WhatsApp, Telegram, Instagram, Facebook, Discord
- 60-120 second average delivery time
- 95%+ success rate with automatic refunds
- Service-specific timers for optimal delivery

### Voice Verification
- Voice call verification with transcription and audio recording
- Support for services requiring phone call confirmation
- Premium pricing: SMS price + N0.25

### Number Rentals
- Long-term phone number rentals (7-365 days)
- Two rental types: Service-specific or General use
- Two modes: Always Active (24/7) or Manual (30% discount)
- Auto-billing with payment method on file

### Payment System
- Multi-currency support: Paystack (NGN), Bitcoin, Ethereum, Solana, USDT
- Tiered pricing: Pay-as-You-Go, Developer (20% off), Enterprise (35% off)
- Automatic refund system for failed verifications
- Real-time payment tracking and webhook notifications

### User Management
- JWT-based authentication with Google OAuth integration
- Email verification system
- Referral program (1 free verification per referral)
- API key management for developers
- Webhook integration for SMS notifications

### Admin Dashboard
- Real-time platform statistics and analytics
- User management with balance filtering
- Payment tracking with status monitoring
- Verification success/failure reports
- Support ticket management

## Technical Stack

### Backend
- **Framework**: FastAPI (Python 3.9+)
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: JWT tokens, Google OAuth 2.0
- **Payment**: Paystack API, Cryptocurrency integrations
- **SMS Provider**: TextVerified API

### Frontend
- **Architecture**: Vanilla JavaScript (modular)
- **Styling**: CSS3 with CSS Variables for theming
- **PWA**: Service Worker, Web App Manifest
- **Mobile**: Responsive design, touch-optimized UI

### Security
- HTTPS enforcement
- Rate limiting (100 requests/minute)
- End-to-end encryption
- Secure password hashing (bcrypt)
- Request ID tracking
- CORS protection

## Project Structure

```
Namaskah. app/
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── static/
│   ├── css/               # Stylesheets (style.css, mobile.css)
│   ├── js/                # Modular JavaScript files
│   ├── icons/             # PWA icons
│   ├── manifest.json      # PWA manifest
│   └── sw.js              # Service worker
├── templates/             # HTML templates
│   ├── index.html         # Main application
│   ├── landing.html       # Landing page
│   ├── admin.html         # Admin dashboard
│   └── ...
├── tests/                 # Test suite
├── docs/                  # Documentation
└── scripts/               # Deployment scripts
```

## Installation

### Prerequisites
- Python 3.9 or higher
- pip package manager
- SQLite3

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/namaskah-app.git
cd namaskah-app
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Initialize database:
```bash
python reset_db.py
python create_admin.py
```

6. Run the application:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Access the application at `http://localhost:8000`

## Configuration

### Environment Variables

```env
# Application
SECRET_KEY=your-secret-key-here
ENVIRONMENT=development

# Database
DATABASE_URL=sqlite:///./namaskah.db

# SMS Provider
TEXTVERIFIED_API_KEY=your-textverified-api-key

# Payment
PAYSTACK_SECRET_KEY=your-paystack-secret-key
PAYSTACK_PUBLIC_KEY=your-paystack-public-key

# OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

## API Documentation

### Authentication Endpoints

```
POST /auth/register        # Create new account
POST /auth/login           # User login
POST /auth/google          # Google OAuth login
GET  /auth/me              # Get user profile
POST /auth/verify-email    # Verify email address
POST /auth/forgot-password # Request password reset
```

### Verification Endpoints

```
POST   /verify/create           # Create verification
GET    /verify/{id}             # Check verification status
GET    /verify/{id}/messages    # Retrieve SMS messages
DELETE /verify/{id}             # Cancel verification (refund)
```

### Rental Endpoints

```
POST /rentals/create        # Rent phone number
GET  /rentals/active        # List active rentals
POST /rentals/{id}/extend   # Extend rental duration
POST /rentals/{id}/release  # Release rental (50% refund)
```

### Wallet Endpoints

```
POST /wallet/fund                    # Initialize funding
POST /wallet/paystack/initialize     # Paystack payment
GET  /wallet/paystack/verify/{ref}   # Verify payment
GET  /wallet/transactions            # Transaction history
```

### Admin Endpoints

```
GET  /admin/stats           # Platform statistics
GET  /admin/users           # User management
GET  /admin/payments        # Payment tracking
POST /admin/credit/{user}   # Add credits to user
```

Full API documentation available at `/docs` (Swagger UI) and `/redoc` (ReDoc).

## Deployment

### Production Deployment

1. Set environment to production:
```bash
export ENVIRONMENT=production
```

2. Configure production database and secrets

3. Deploy using provided script:
```bash
chmod +x deploy.sh
./deploy.sh
```

### Docker Deployment

```bash
docker build -t namaskah-app .
docker run -p 8000:8000 --env-file .env namaskah-app
```

### Platform-Specific

- **Render**: Use `render.yaml` configuration
- **Railway**: Use `railway.json` configuration
- **Heroku**: Use `Procfile` (create if needed)

## Testing

Run the test suite:

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_auth.py
```

## Admin Access

Default admin credentials:
```
Email: admin@namaskah.app
Password: Namaskah@Admin2024
```

Change these credentials immediately after first login.

## Pricing Structure

### Currency
- Symbol: N (Namaskah Coin)
- Exchange Rate: 1N = $2 USD

### Verification Pricing
- Popular Services: N1 ($2.00)
- General Purpose: N1.25 ($2.50)
- Voice Verification: +N0.25 additional

### Pricing Tiers
- Pay-as-You-Go: Standard pricing
- Developer: 20% discount (min. N25 funded)
- Enterprise: 35% discount (min. N100 funded)

### Rental Pricing
Service-specific rentals start at N5 ($10) for 7 days.
General use rentals start at N6 ($12) for 7 days.
Manual mode offers 30% discount.

## Support

### Documentation
- API Documentation: `/docs`
- User Guides: `/docs/guides/`
- Testing Guide: `/docs/testing/`

### Contact
- Email: support@namaskah.app
- In-app support tickets
- Response time: Within 24 hours

## License

MIT License - See LICENSE file for details

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## Security

Report security vulnerabilities to: security@namaskah.app

## Changelog

### Version 2.1.0 (2025-01-18)
- Admin panel enhancements with verification reports
- Mobile responsive design improvements
- Professional UI theme updates
- Documentation consolidation
- Performance optimizations

---

**Namaskah SMS** - Enterprise SMS Verification Platform
Version 2.1.0 | Production Ready
