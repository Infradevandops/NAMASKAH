# Namaskah SMS - Simplified Dashboard

A clean, focused SMS verification platform with working core functionality.

## What Works ✅

### Core Features
- **SMS Verification**: Create verifications for 1,800+ services
- **User Authentication**: Login/register with JWT tokens
- **Wallet System**: Paystack payment integration (NGN)
- **Admin Dashboard**: User management, stats, payment tracking
- **API Documentation**: Auto-generated Swagger docs at `/docs`

### Dashboard Features
- Real-time verification status
- Transaction history
- User settings
- Mobile-responsive design
- Admin panel with user management

## Quick Start

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Set Environment Variables**
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. **Initialize Database**
```bash
python -c "from main import Base, engine; Base.metadata.create_all(bind=engine)"
```

4. **Run Application**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

5. **Test Core Functionality**
```bash
python check_dashboard.py
```

## Admin Access

Default admin credentials:
- Email: `admin@namaskah.app`
- Password: `Namaskah@Admin2024`

Access admin dashboard at: `http://localhost:8000/admin`

## API Endpoints

### Core Endpoints
- `GET /health` - Health check
- `GET /docs` - API documentation
- `POST /auth/login` - User login
- `POST /auth/register` - User registration
- `POST /verify/create` - Create SMS verification
- `GET /verify/{id}` - Check verification status
- `GET /verify/{id}/messages` - Get SMS messages

### Admin Endpoints
- `GET /admin/stats` - Platform statistics
- `GET /admin/users` - User management
- `POST /admin/credits/add` - Add user credits

## Configuration

### Required Environment Variables
```env
SECRET_KEY=your-secret-key
TEXTVERIFIED_API_KEY=your-textverified-key
PAYSTACK_SECRET_KEY=your-paystack-key
```

### Optional Variables
```env
GOOGLE_CLIENT_ID=your-google-oauth-id
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

## File Structure

```
Namaskah. app/
├── main.py                 # FastAPI application
├── requirements.txt        # Dependencies
├── static/
│   ├── css/
│   │   ├── style.css      # Main styles
│   │   └── mobile.css     # Mobile styles
│   └── js/
│       ├── auth.js        # Authentication
│       ├── verification.js # SMS verification
│       ├── wallet.js      # Payment handling
│       ├── services.js    # Service selection
│       └── main.js        # Dashboard core
├── templates/
│   ├── index.html         # Main dashboard
│   ├── admin.html         # Admin panel
│   ├── landing.html       # Landing page
│   └── *.html            # Other pages
└── check_dashboard.py     # Health check script
```

## Removed Features

The following complex/unused features have been removed to focus on core functionality:

- ❌ Biometric authentication
- ❌ Offline queue system
- ❌ Social proof widgets
- ❌ Complex carrier selection
- ❌ Cryptocurrency payments
- ❌ PWA features
- ❌ Cookie consent banners
- ❌ Multiple backup files

## Development

### Testing
```bash
python check_dashboard.py  # Test core endpoints
```

### Database Reset
```bash
rm -f *.db
python -c "from main import Base, engine; Base.metadata.create_all(bind=engine)"
```

### Production Deployment
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Support

- Check `/docs` for API documentation
- Use admin dashboard for user management
- Monitor `/health` endpoint for system status

---

**Version**: Simplified Dashboard v1.0  
**Focus**: Core functionality that works reliably