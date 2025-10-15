# 🚀 Deployment Guide

## Quick Deploy Options

### 1. Railway (Recommended)
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Deploy
railway init
railway up
```

**Environment Variables:**
```
JWT_SECRET_KEY=your-secret-key
TEXTVERIFIED_API_KEY=your-api-key
TEXTVERIFIED_EMAIL=your-email
DATABASE_URL=sqlite:///./sms.db
```

### 2. Render
1. Connect GitHub repo
2. Select "Web Service"
3. Build: `pip install -r requirements.txt`
4. Start: `python main.py`
5. Add environment variables

### 3. Docker
```bash
docker build -t namaskah-sms .
docker run -p 8000:8000 --env-file .env namaskah-sms
```

### 4. VPS (Ubuntu/Debian)
```bash
# Install dependencies
sudo apt update
sudo apt install python3 python3-pip python3-venv

# Clone repo
git clone <your-repo>
cd namaskah-app

# Setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
nano .env

# Run with systemd
sudo nano /etc/systemd/system/namaskah.service
```

**systemd service:**
```ini
[Unit]
Description=Namaskah SMS Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/namaskah-app
Environment="PATH=/path/to/namaskah-app/.venv/bin"
ExecStart=/path/to/namaskah-app/.venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable namaskah
sudo systemctl start namaskah
```

## Production Checklist

- [ ] Change JWT_SECRET_KEY to strong random value
- [ ] Use PostgreSQL instead of SQLite for production
- [ ] Enable HTTPS/SSL
- [ ] Set up monitoring (Sentry, DataDog)
- [ ] Configure backup for database
- [ ] Set up rate limiting
- [ ] Enable CORS properly
- [ ] Use environment-specific configs
- [ ] Set up logging
- [ ] Configure firewall rules

## Performance Tips

1. **Database**: Switch to PostgreSQL for better concurrency
2. **Caching**: Services are cached client-side
3. **CDN**: Serve static files via CDN
4. **Load Balancer**: Use nginx for multiple instances
5. **Monitoring**: Track API response times

## Security

- JWT tokens expire in 30 days
- Passwords hashed with bcrypt
- User isolation enforced
- API rate limiting recommended
- HTTPS required in production
