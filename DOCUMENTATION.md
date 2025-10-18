# Namaskah SMS - Complete Documentation

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Deployment Guide](#deployment-guide)
3. [Feature Documentation](#feature-documentation)
4. [Testing Guide](#testing-guide)
5. [Mobile Implementation](#mobile-implementation)
6. [Admin Features](#admin-features)

---

## Architecture Overview

### System Architecture

**Backend Stack**
- FastAPI framework with async support
- SQLAlchemy ORM with SQLite database
- JWT authentication with Google OAuth
- Paystack payment integration
- TextVerified SMS API integration

**Frontend Stack**
- Modular JavaScript architecture
- CSS3 with custom properties (theming)
- Progressive Web App (PWA) capabilities
- Responsive mobile-first design

**Security Features**
- HTTPS enforcement
- Rate limiting (100 req/min)
- Password hashing (bcrypt)
- JWT token authentication
- CORS protection
- Request ID tracking

### Database Schema

**Users Table**
- id, email, password_hash, credits, free_verifications
- is_verified, is_admin, referral_code, referred_by
- created_at, updated_at

**Verifications Table**
- id, user_id, service, phone_number, status
- cost, capability, verification_id, target_id
- created_at, expires_at

**Transactions Table**
- id, user_id, amount, type, status
- reference, payment_method, created_at

**Rentals Table**
- id, user_id, phone_number, service, mode
- duration_hours, cost, status, expires_at

**API Keys Table**
- id, user_id, key_hash, name, last_used_at

**Webhooks Table**
- id, user_id, url, secret, is_active

---

## Deployment Guide

### Prerequisites
- Python 3.9+
- Domain with SSL certificate
- SMTP server for emails
- Payment gateway accounts (Paystack)
- SMS provider API key (TextVerified)

### Environment Setup

1. **Clone and Setup**
```bash
git clone <repository-url>
cd namaskah-app
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. **Configure Environment**
```bash
cp .env.example .env
# Edit .env with production values
```

3. **Initialize Database**
```bash
python reset_db.py
python create_admin.py
```

4. **Run Application**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Production Deployment

**Using Render**
1. Connect GitHub repository
2. Set environment variables in dashboard
3. Use `render.yaml` configuration
4. Deploy automatically on push

**Using Railway**
1. Connect GitHub repository
2. Configure `railway.json`
3. Set environment variables
4. Deploy with automatic SSL

**Using Docker**
```bash
docker build -t namaskah-app .
docker run -d -p 8000:8000 --env-file .env namaskah-app
```

### Post-Deployment Checklist
- [ ] Verify SSL certificate
- [ ] Test payment integration
- [ ] Verify email sending
- [ ] Check SMS API connectivity
- [ ] Test admin login
- [ ] Monitor error logs
- [ ] Set up backup schedule
- [ ] Configure monitoring alerts

---

## Feature Documentation

### SMS Verification Flow

1. **User selects service** from 1,807+ options
2. **System requests number** from TextVerified API
3. **User receives phone number** instantly
4. **User enters number** on target service
5. **SMS arrives** within 60-120 seconds
6. **System retrieves SMS** and displays to user
7. **Auto-refund** if SMS not received

### Voice Verification Flow

1. User selects voice capability
2. System requests voice-enabled number
3. User initiates call on target service
4. System retrieves call transcription
5. User receives verification code

### Number Rental System

**Rental Types**
- Service-specific: Dedicated to one service
- General use: Accepts from any service

**Rental Modes**
- Always Active: 24/7 availability
- Manual: Activate before use (30% discount)

**Rental Process**
1. User selects service and duration
2. Payment method required for auto-billing
3. Number assigned immediately
4. Auto-renewal before expiration
5. Early release with 50% refund

### Payment System

**Supported Methods**
- Paystack (Bank transfer, Card, USSD)
- Bitcoin (BTC)
- Ethereum (ETH)
- Solana (SOL)
- Tether (USDT)

**Payment Flow**
1. User initiates funding
2. System generates payment reference
3. User completes payment
4. Webhook confirms payment
5. Credits added to wallet
6. Email confirmation sent

### Referral Program

**Mechanics**
- Each user gets unique referral code
- Referrer earns 1 free verification when referee funds wallet (min $5)
- Referee also gets 1 free verification on signup
- Unlimited referrals allowed

---

## Testing Guide

### Running Tests

**Full Test Suite**
```bash
pytest
```

**With Coverage**
```bash
pytest --cov=. --cov-report=html
```

**Specific Tests**
```bash
pytest tests/test_auth.py
pytest tests/test_verification.py
pytest tests/test_wallet.py
```

### Test Categories

**Authentication Tests**
- User registration
- Login with email/password
- Google OAuth flow
- Email verification
- Password reset

**Verification Tests**
- Create verification
- Check status
- Retrieve messages
- Cancel and refund
- Service filtering

**Wallet Tests**
- Fund wallet
- Payment verification
- Transaction history
- Balance updates

**Rental Tests**
- Create rental
- Extend duration
- Early release
- Auto-renewal

### Manual Testing Checklist

**User Flow**
- [ ] Register new account
- [ ] Verify email
- [ ] Fund wallet
- [ ] Create verification
- [ ] Receive SMS
- [ ] Check transaction history
- [ ] Test referral link

**Admin Flow**
- [ ] Login to admin panel
- [ ] View statistics
- [ ] Manage users
- [ ] Track payments
- [ ] Respond to support tickets

---

## Mobile Implementation

### Responsive Design

**Breakpoints**
- Mobile: < 480px (1 column)
- Tablet: 480px - 768px (2 columns)
- Desktop: > 768px (3-4 columns)

**Touch Optimization**
- Minimum button size: 44px x 44px
- Touch-friendly spacing
- Swipe gestures support
- Pull-to-refresh

**Mobile Features**
- Bottom navigation bar
- Hamburger menu drawer
- Full-screen modals
- PWA installation prompt
- Offline support

### PWA Capabilities

**Features**
- Install to home screen
- Offline functionality
- Push notifications
- Background sync
- App-like experience

**Implementation**
- Service Worker: `/static/sw.js`
- Manifest: `/static/manifest.json`
- Icons: `/static/icons/`

---

## Admin Features

### Dashboard Statistics

**Metrics Displayed**
- Total users
- Total revenue (N and USD)
- Total verifications
- Completed verifications
- Failed/cancelled verifications
- Pending verifications
- Success rate percentage
- Active rentals

**Filtering**
- Time periods: 7, 14, 30, 60, 90 days, all time
- Service popularity rankings
- User balance categories

### User Management

**Capabilities**
- View all users with pagination
- Search by email
- Filter by balance (High/Medium/Low/Zero)
- Sort by date or balance
- Add credits to user wallet
- View user verification history

### Payment Tracking

**Features**
- Complete payment history
- Status badges (Success/Pending/Failed)
- Amount display (N and NGN)
- Webhook status tracking
- Error message display
- Search by email or reference

### Support System

**Ticket Management**
- View all support tickets
- Filter by category
- Respond to tickets
- Track resolution status
- Email notifications

---

## API Integration

### Authentication

All API requests require JWT token in header:
```
Authorization: Bearer <token>
```

### Example Requests

**Create Verification**
```bash
curl -X POST https://api.namaskah.app/verify/create \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"service": "whatsapp", "capability": "sms"}'
```

**Check Status**
```bash
curl -X GET https://api.namaskah.app/verify/{id} \
  -H "Authorization: Bearer <token>"
```

**Fund Wallet**
```bash
curl -X POST https://api.namaskah.app/wallet/fund \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"amount": 10.00, "method": "paystack"}'
```

### Webhooks

**SMS Notification Webhook**
```json
{
  "event": "sms.received",
  "verification_id": "123",
  "phone_number": "+1234567890",
  "message": "Your code is 123456",
  "timestamp": "2025-01-18T12:00:00Z"
}
```

**Payment Webhook**
```json
{
  "event": "payment.success",
  "reference": "ref_123",
  "amount": 10.00,
  "user_id": "user_123",
  "timestamp": "2025-01-18T12:00:00Z"
}
```

---

## Troubleshooting

### Common Issues

**SMS Not Received**
- Check service timer (some services take longer)
- Verify sufficient balance
- Check TextVerified API status
- Auto-refund triggers after timeout

**Payment Not Credited**
- Check webhook delivery
- Verify payment reference
- Check transaction status in admin panel
- Manual credit available via admin

**Email Not Sending**
- Verify SMTP credentials
- Check spam folder
- Verify email server connectivity
- Check error logs

**API Rate Limiting**
- Default: 100 requests/minute
- Upgrade to Enterprise for higher limits
- Implement exponential backoff

### Logs and Monitoring

**Log Files**
- Application: `app.log`
- Server: `server.log`

**Monitoring Endpoints**
- Health check: `/health`
- Metrics: `/metrics`
- Status: `/status`

---

## Security Best Practices

### For Developers

1. Never commit `.env` file
2. Rotate API keys regularly
3. Use HTTPS in production
4. Implement rate limiting
5. Validate all user inputs
6. Use prepared statements for SQL
7. Keep dependencies updated

### For Users

1. Use strong passwords
2. Enable email verification
3. Secure API keys
4. Use webhook secrets
5. Monitor transaction history
6. Report suspicious activity

---

## Performance Optimization

### Backend
- Database indexing on frequently queried fields
- Connection pooling
- Async request handling
- Response caching where appropriate

### Frontend
- Lazy loading for images
- Code splitting
- Service worker caching
- Minified assets

### Database
- Regular vacuum operations
- Index optimization
- Query optimization
- Backup schedule

---

## Maintenance

### Regular Tasks

**Daily**
- Monitor error logs
- Check payment webhooks
- Verify SMS API connectivity

**Weekly**
- Review user feedback
- Update service list
- Check system performance

**Monthly**
- Database backup
- Security audit
- Dependency updates
- Performance review

### Backup Strategy

**Database Backups**
- Automated daily backups
- Retention: 30 days
- Off-site storage
- Test restore monthly

**Configuration Backups**
- Environment variables
- SSL certificates
- API credentials

---

## Support and Contact

**Technical Support**
- Email: support@namaskah.app
- Response time: 24 hours
- In-app support tickets

**Business Inquiries**
- Enterprise solutions
- Partnership opportunities
- Custom integrations

**Security Issues**
- Email: security@namaskah.app
- Responsible disclosure policy

---

**Last Updated**: 2025-01-18
**Version**: 2.1.0
**Status**: Production Ready
