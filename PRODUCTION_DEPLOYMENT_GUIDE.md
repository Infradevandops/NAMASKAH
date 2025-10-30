# 🚀 Namaskah SMS - Production Deployment Guide

## **Phase 1: Critical Security Fixes (30 minutes)**

### 1.1 Remove Hardcoded Credentials
```bash
# Check for any hardcoded credentials in JS files
grep -r "password\|secret\|key" static/js/ --exclude-dir=node_modules

# Remove any test files with credentials (if found)
# rm static/js/test-credentials.js
```

### 1.2 Add Input Sanitization
```bash
# Update security middleware
nano app/middleware/security.py
```
Add CSP headers:
```python
response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'"
response.headers["X-Content-Type-Options"] = "nosniff"
response.headers["X-Frame-Options"] = "DENY"
```

### 1.3 Enable HTTPS (Production)
```bash
# Update .env for production
echo "BASE_URL=https://yourdomain.com" >> .env
echo "SECURE_COOKIES=true" >> .env
```

### 1.4 Add CSRF Protection
```bash
# Install CSRF protection
pip install python-multipart

# Add to main.py
echo "from fastapi_csrf_protect import CsrfProtect" >> main.py
```

---

## **Phase 2: Core Functionality Verification (45 minutes)**

### 2.1 Test TextVerified Integration
```bash
# Set up TextVerified API key
echo "TEXTVERIFIED_API_KEY=your-api-key-here" >> .env

# Test API connection
python3 -c "
from app.services.textverified_service import TextVerifiedService
import asyncio
async def test():
    service = TextVerifiedService()
    result = await service.get_services()
    print('✅ TextVerified API connected' if 'services' in result else '❌ API connection failed')
asyncio.run(test())
"
```

### 2.2 Verify All UI Functions
```bash
# Start server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &

# Test checklist (manual verification):
# □ Login works (admin@namaskah.app / Namaskah@Admin2024)
# □ Dashboard loads
# □ "Get Number" button works
# □ Service selection dropdown populated
# □ "Get SMS" button retrieves messages
# □ Payment flow functional
# □ User registration works
# □ API key generation works
```

### 2.3 Test Payment Integration
```bash
# Add Paystack keys
echo "PAYSTACK_SECRET_KEY=your-secret-key" >> .env
echo "PAYSTACK_PUBLIC_KEY=your-public-key" >> .env

# Test payment endpoint
curl -X POST http://localhost:8000/wallet/paystack/initialize \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-jwt-token" \
  -d '{"amount": 1000}'
```

### 2.4 Test Error Handling
```bash
# Test with invalid API key
TEXTVERIFIED_API_KEY=invalid python3 -c "
from app.services.verification_service import VerificationService
import asyncio
async def test():
    service = VerificationService()
    # Should handle error gracefully
    print('Error handling test completed')
asyncio.run(test())
"
```

---

## **Phase 3: Production Readiness (30 minutes)**

### 3.1 Environment Configuration
```bash
# Create production environment file
cp .env.example .env.production

# Update production settings
cat > .env.production << EOF
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=postgresql://user:pass@host:5432/namaskah_sms
BASE_URL=https://yourdomain.com
TEXTVERIFIED_API_KEY=your-production-key
PAYSTACK_SECRET_KEY=your-production-key
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
EOF
```

### 3.2 Database Setup
```bash
# Run migrations
alembic upgrade head

# Create admin user
python3 create_admin.py

# Verify database
python3 -c "
from app.core.database import SessionLocal
from app.models.user import User
db = SessionLocal()
count = db.query(User).count()
print(f'✅ Database ready with {count} users')
db.close()
"
```

### 3.3 Monitoring Setup
```bash
# Create health check endpoint test
curl http://localhost:8000/system/health

# Expected response: {"status": "healthy", "timestamp": "..."}

# Set up log monitoring
mkdir -p logs
echo "LOG_LEVEL=INFO" >> .env
echo "LOG_FILE=logs/app.log" >> .env
```

### 3.4 Performance Testing
```bash
# Install testing tools
pip install locust

# Create simple load test
cat > locustfile.py << EOF
from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def test_health(self):
        self.client.get("/system/health")
    
    @task
    def test_homepage(self):
        self.client.get("/app")
EOF

# Run load test (optional)
# locust --host=http://localhost:8000 --users=10 --spawn-rate=2 -t 60s --headless
```

---

## **Final Production Checklist**

### **Security ✅**
- [ ] All secrets in environment variables
- [ ] HTTPS enabled with valid SSL certificate
- [ ] CSP headers configured
- [ ] Input validation active
- [ ] Rate limiting enabled
- [ ] Error logging configured

### **Functionality ✅**
- [ ] TextVerified API integration working
- [ ] SMS verification flow complete
- [ ] Payment processing functional
- [ ] User authentication working
- [ ] Admin dashboard accessible
- [ ] API endpoints responding correctly

### **Production ✅**
- [ ] Database migrations applied
- [ ] Admin user created
- [ ] Health checks responding
- [ ] Monitoring configured
- [ ] Backup strategy implemented
- [ ] Documentation complete

---

## **Deployment Commands**

### **Docker Deployment**
```bash
# Build and deploy
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose ps
```

### **Manual Deployment**
```bash
# Install dependencies
pip install -r requirements.txt

# Set production environment
export $(cat .env.production | xargs)

# Run migrations
alembic upgrade head

# Start application
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### **Verification**
```bash
# Test production deployment
curl https://yourdomain.com/system/health
curl https://yourdomain.com/app

# Monitor logs
tail -f logs/app.log
```

---

## **🎯 Success Criteria**

Your Namaskah SMS platform is production-ready when:

1. **Security scan shows 0 critical issues**
2. **All verification flows work end-to-end**
3. **Payment processing completes successfully**
4. **Health checks return 200 OK**
5. **Load testing passes without errors**
6. **SSL certificate is valid and active**

**Estimated Total Time: 1 hour 45 minutes**

**Next Steps:** Follow each phase sequentially, checking off items as completed. The platform will be industry-standard and ready for users.