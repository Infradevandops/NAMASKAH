# 🔐 Security Guide - Namaskah SMS

## **Environment Variables & Secrets Management**

### **🚨 CRITICAL SECURITY RULES**

1. **NEVER commit `.env` files to version control**
2. **Use different secrets for each environment**
3. **Rotate secrets regularly (every 90 days)**
4. **Use strong, randomly generated secrets**
5. **Limit access to production secrets**

### **📁 File Structure**

```
project/
├── .env.template          # ✅ Safe to commit - template only
├── .env.example          # ✅ Safe to commit - example values
├── .env.development      # ✅ Safe to commit - dev values only
├── .env                  # ❌ NEVER commit - your actual secrets
├── .env.production       # ❌ NEVER commit - production secrets
├── .env.staging          # ❌ NEVER commit - staging secrets
└── .gitignore           # ✅ Must exclude all .env files
```

### **🔧 Setup Instructions**

#### **1. Initial Setup**
```bash
# Generate environment file for development
python scripts/manage_secrets.py generate --env development

# Copy template for your local environment
cp .env.template .env

# Edit .env with your actual values
nano .env
```

#### **2. Production Deployment**
```bash
# Generate production environment file
python scripts/manage_secrets.py generate --env production

# Edit with production values
nano .env.production

# Validate before deployment
python scripts/manage_secrets.py validate --env production
```

### **🔑 Secret Categories**

#### **Critical Secrets (Never expose)**
- `SECRET_KEY` - Application encryption key
- `JWT_SECRET_KEY` - JWT token signing key
- `DATABASE_URL` - Database connection string
- `PAYSTACK_SECRET_KEY` - Payment processing key
- `TEXTVERIFIED_API_KEY` - SMS service key

#### **Semi-Sensitive**
- `PAYSTACK_PUBLIC_KEY` - Payment public key (can be in frontend)
- `GOOGLE_CLIENT_ID` - OAuth client ID
- `SENTRY_DSN` - Error tracking URL

#### **Non-Sensitive**
- `BASE_URL` - Application URL
- `ENVIRONMENT` - Environment name
- Crypto addresses (display only)

### **🛡️ Security Best Practices**

#### **1. Secret Generation**
```bash
# Generate strong secrets
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Or use the management script
python scripts/manage_secrets.py rotate --key SECRET_KEY
```

#### **2. Environment Separation**
- **Development**: Use test/fake credentials
- **Staging**: Use staging-specific credentials
- **Production**: Use live credentials only

#### **3. Access Control**
```bash
# Set secure file permissions
chmod 600 .env.production

# Restrict directory access
chmod 700 /path/to/secrets/
```

#### **4. Regular Auditing**
```bash
# Audit current environment
python scripts/manage_secrets.py audit

# Validate all secrets are present
python scripts/manage_secrets.py validate
```

### **🚀 Deployment Strategies**

#### **1. Cloud Platforms (Render, Heroku, etc.)**
- Use platform environment variables
- Never upload .env files
- Set secrets through web interface or CLI

#### **2. Docker Deployment**
```bash
# Use environment files
docker run --env-file .env.production myapp

# Or pass individual variables
docker run -e SECRET_KEY=xxx -e DATABASE_URL=yyy myapp
```

#### **3. Kubernetes**
```yaml
# Use Kubernetes secrets
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
type: Opaque
data:
  SECRET_KEY: <base64-encoded-value>
  DATABASE_URL: <base64-encoded-value>
```

### **🔄 Secret Rotation**

#### **Monthly Rotation (Recommended)**
```bash
# Rotate application secrets
python scripts/manage_secrets.py rotate --key SECRET_KEY
python scripts/manage_secrets.py rotate --key JWT_SECRET_KEY

# Update deployment
# Restart application
```

### **🚨 Incident Response**

#### **If Secrets Are Exposed**
1. **Immediate Actions**:
   - Rotate all exposed secrets
   - Revoke compromised API keys
   - Change database passwords
   - Update all deployments

2. **Investigation**:
   - Check git history for exposed secrets
   - Audit access logs
   - Review who had access

3. **Prevention**:
   - Update .gitignore
   - Add pre-commit hooks
   - Train team on security practices

### **🔍 Monitoring & Alerting**

#### **Set up alerts for**:
- Failed authentication attempts
- Unusual API usage patterns
- Database connection failures
- Payment processing errors

#### **Regular Security Checks**:
```bash
# Weekly security audit
python scripts/security_check.py

# Monthly secret validation
python scripts/manage_secrets.py audit
```

---

**Remember**: Security is everyone's responsibility. When in doubt, ask for help!