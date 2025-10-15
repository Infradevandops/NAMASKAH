# 📱 Namaskah SMS - Simple Verification Service

**Minimal SMS verification platform using TextVerified API**

## ✨ Features

- 🔐 User authentication (JWT + Google OAuth)
- 📱 SMS verification for 1,807 services
- 🎨 Clean web interface
- 🚀 Single-file backend
- 💾 SQLite database
- 🐳 Docker ready

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
- TextVerified API account ([Get one here](https://www.textverified.com))

## 🔧 Configuration

Edit `.env`:
```bash
JWT_SECRET_KEY=your-secret-key-here
TEXTVERIFIED_API_KEY=your-api-key
TEXTVERIFIED_EMAIL=your-email@example.com
DATABASE_URL=sqlite:///./sms.db
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

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Web interface |
| GET | `/health` | Health check |
| POST | `/auth/register` | Register user |
| POST | `/auth/login` | Login |
| GET | `/auth/me` | Get user info |
| POST | `/verify/create` | Create verification |
| GET | `/verify/{id}` | Get verification status |
| GET | `/verify/{id}/messages` | Get SMS messages |
| DELETE | `/verify/{id}` | Cancel verification |

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
├── main.py              # Backend API (200 lines)
├── requirements.txt     # Dependencies
├── Dockerfile          # Container config
├── .env.example        # Config template
├── static/
│   ├── css/
│   │   └── style.css   # Styles
│   └── js/
│       └── app.js      # Frontend logic
└── templates/
    └── index.html      # Web interface
```

## 🔒 Security

- JWT token authentication
- Password hashing (bcrypt)
- Secure API communication
- Environment-based secrets

## 🐛 Troubleshooting

**"Invalid token"**
- Token expired (30 days)
- Login again

**"Authentication failed"**
- Check TextVerified API key
- Verify account has balance

**Database errors**
- Delete `sms.db` and restart

## 📝 License

MIT

## 🆘 Support

- API Docs: `http://localhost:8000/docs`
- TextVerified: [textverified.com](https://www.textverified.com)

---

**Simple. Fast. Focused.**
