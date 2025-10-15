# 🔐 Login Credentials

## Default Accounts

### 👤 Admin Account
```
Email:    admin@namaskah.app
Password: admin123
```

### 👤 Test User
```
Email:    user@namaskah.app
Password: user123
```

### 👤 Demo User
```
Email:    test@example.com
Password: test123
```

---

## 🚀 Quick Start

1. **Start the server:**
   ```bash
   ./start.sh
   ```

2. **Open browser:**
   ```
   http://localhost:8000
   ```

3. **Login with any account above**

4. **Create SMS verification:**
   - Select service (WhatsApp, Telegram, etc.)
   - Get temporary phone number
   - Use it for verification
   - Check messages for code

---

## 🔧 Create New Users

**Option 1: Use the web interface**
- Click "Register" tab
- Enter email and password
- Click "Register"

**Option 2: Run the script**
```bash
python create_users.py
```

**Option 3: Use the API**
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "newuser@example.com", "password": "password123"}'
```

---

## 🔒 Security Notes

⚠️ **IMPORTANT:** These are default credentials for testing only!

**For production:**
1. Delete these default users
2. Create strong passwords
3. Change `JWT_SECRET_KEY` in `.env`
4. Use environment variables for secrets
5. Enable HTTPS

**Delete default users:**
```bash
rm sms.db
# Then create your own users
```

---

## 📝 Password Requirements

Current: No restrictions (for simplicity)

**Recommended for production:**
- Minimum 8 characters
- At least one uppercase letter
- At least one number
- At least one special character

---

## 🆘 Forgot Password?

Currently no password reset (minimal version).

**To reset:**
1. Delete database: `rm sms.db`
2. Recreate users: `python create_users.py`

**Or manually:**
```python
from main import User, SessionLocal
from passlib.hash import bcrypt

db = SessionLocal()
user = db.query(User).filter(User.email == "user@example.com").first()
user.password_hash = bcrypt.hash("newpassword")
db.commit()
```

---

**Ready to login! Visit http://localhost:8000** 🚀
