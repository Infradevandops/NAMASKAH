# Namaskah SMS Setup Guide

## 🚀 Quick Setup (5 minutes)

### 1. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit with your API keys
nano .env
```

### 2. Required API Keys

**TextVerified API:**
- Sign up at https://www.textverified.com
- Get API key from dashboard
- Add to `.env`: `TEXTVERIFIED_API_KEY=your-key`

**Paystack (for payments):**
- Sign up at https://paystack.com
- Get secret key from dashboard
- Add to `.env`: `PAYSTACK_SECRET_KEY=your-key`

### 3. Start Application
```bash
# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Create admin user
python3 create_admin.py

# Start server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Test Login
- Go to: http://localhost:8000/app
- Email: `admin@namaskah.app`
- Password: `Namaskah@Admin2024`

## ✅ Verification

Test SMS verification:
1. Login to dashboard
2. Select a service (e.g., "WhatsApp")
3. Click "Get Number"
4. Use the phone number for verification
5. Check "Get SMS" for verification code

## 🔧 Production Deployment

For production, update `.env`:
```bash
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=postgresql://user:pass@host:5432/db
BASE_URL=https://yourdomain.com
```

## 📞 Support

- Documentation: Check `/docs` endpoint
- Issues: Review Code Issues panel
- API: Interactive docs at `/docs`