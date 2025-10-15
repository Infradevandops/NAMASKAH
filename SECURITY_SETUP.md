# 🔒 Security Setup Guide

## ✅ Implemented Security Features

### 1. **PostgreSQL Migration**
- Switched from SQLite to PostgreSQL for production
- Better concurrency, ACID compliance, and scalability
- Connection pooling and prepared statements

### 2. **Authentication & Authorization**
- JWT tokens with 30-day expiration
- Bcrypt password hashing (cost factor 12)
- User isolation with strict `user_id` filtering
- Admin role-based access control

### 3. **Rate Limiting**
- 100 requests per minute per user
- Prevents brute force and DDoS attacks
- Token-based tracking

### 4. **Input Validation**
- Pydantic models for all inputs
- Email validation
- SQL injection prevention (SQLAlchemy ORM)
- XSS protection (FastAPI auto-escaping)

### 5. **CORS Configuration**
- Restricted origins (localhost + production domain)
- Credentials support
- Secure headers

### 6. **Environment Security**
- All secrets in `.env` file
- `.env` excluded from git
- Separate dev/prod configurations

### 7. **Database Security**
- Parameterized queries (SQLAlchemy)
- User-level data isolation
- Transaction logging
- Audit trail

## 🚀 Setup Instructions

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Setup PostgreSQL
```bash
# Install PostgreSQL (macOS)
brew install postgresql@15
brew services start postgresql@15

# Run setup script
./setup_postgres.sh
```

### Step 3: Update Environment Variables
Edit `.env`:
```bash
# Use PostgreSQL (comment out SQLite)
DATABASE_URL=postgresql://namaskah_user:YOUR_SECURE_PASSWORD@localhost:5432/namaskah_db

# Generate strong JWT secret
JWT_SECRET_KEY=$(openssl rand -hex 32)

# Set allowed hosts
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com
CORS_ORIGINS=http://localhost:8000,https://yourdomain.com
```

### Step 4: Initialize Database
```bash
python reset_db.py
```

### Step 5: Run Application
```bash
./start.sh
```

## 🛡️ Additional Security Recommendations

### 1. **HTTPS/TLS**
```bash
# Use Let's Encrypt for free SSL
sudo certbot --nginx -d yourdomain.com
```

### 2. **Firewall Rules**
```bash
# Allow only necessary ports
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

### 3. **Database Backups**
```bash
# Daily automated backups
0 2 * * * pg_dump namaskah_db > /backups/namaskah_$(date +\%Y\%m\%d).sql
```

### 4. **Monitoring**
- Set up error logging (Sentry)
- Monitor failed login attempts
- Track API usage patterns
- Alert on suspicious activity

### 5. **Password Policy**
- Minimum 8 characters
- Require uppercase, lowercase, numbers
- Password reset via email
- Account lockout after 5 failed attempts

### 6. **API Security**
- API key rotation every 90 days
- Webhook signature verification
- Request signing for sensitive operations

### 7. **Production Checklist**
- [ ] Change all default passwords
- [ ] Enable HTTPS only
- [ ] Set DEBUG=False
- [ ] Use strong JWT secret (32+ chars)
- [ ] Configure proper CORS origins
- [ ] Set up database backups
- [ ] Enable logging and monitoring
- [ ] Use environment-specific configs
- [ ] Implement IP whitelisting for admin
- [ ] Set up WAF (Web Application Firewall)

## 🔐 Security Best Practices

### Password Storage
✅ **Current**: Bcrypt with salt
❌ **Never**: Plain text, MD5, SHA1

### Token Management
✅ **Current**: JWT with expiration
❌ **Never**: Permanent tokens, predictable tokens

### Database Access
✅ **Current**: ORM with parameterized queries
❌ **Never**: String concatenation, raw SQL

### API Keys
✅ **Current**: Prefixed (`nsk_`), random, revocable
❌ **Never**: Sequential, predictable, permanent

## 📊 Security Monitoring

### Log Important Events
- Failed login attempts
- Password changes
- Credit additions/deductions
- Admin actions
- API key usage
- Webhook failures

### Alert Triggers
- 5+ failed logins in 5 minutes
- Unusual spending patterns
- API rate limit violations
- Database connection failures
- Unauthorized access attempts

## 🆘 Incident Response

### If Compromised:
1. **Immediately**: Rotate all secrets (JWT, API keys, DB passwords)
2. **Revoke**: All active sessions and API keys
3. **Audit**: Check logs for unauthorized access
4. **Notify**: Affected users if data breach
5. **Patch**: Fix vulnerability
6. **Monitor**: Watch for continued attacks

## 📞 Support
For security issues: security@namaskah.app
