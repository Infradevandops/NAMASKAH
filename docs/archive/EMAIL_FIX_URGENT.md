# 🚨 URGENT: Fix Email System

**Status**: ❌ BROKEN  
**Priority**: 🔥 CRITICAL  
**Time**: 10 minutes  
**Impact**: Users can't verify email or reset passwords

---

## ⚠️ Current Problem

**Email system is NOT working**:
- SMTP not configured on Render
- Verification URLs point to localhost
- Users can't verify email
- Password reset broken
- No notifications sent

**Affected User**: worldkingctn@gmail.com (and all users)

---

## ✅ Fix Steps (10 minutes)

### Step 1: Get Gmail App Password (3 min)

1. Go to: https://myaccount.google.com/apppasswords
2. Sign in with your Gmail
3. Create app password:
   - App: "Namaskah SMS"
   - Device: "Web Server"
4. Copy the 16-character password (xxxx-xxxx-xxxx-xxxx)

---

### Step 2: Add to Render (2 min)

1. Go to: https://dashboard.render.com
2. Select: namaskah-sms service
3. Go to: Environment tab
4. Add these variables:

```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-actual-email@gmail.com
SMTP_PASSWORD=xxxx-xxxx-xxxx-xxxx
FROM_EMAIL=noreply@namaskah.app
```

5. Click "Save Changes"

---

### Step 3: Fix Code (3 min)

**File**: `main.py`

**Change 1** - Line 852:
```python
# FROM:
verification_url = f"http://localhost:8000/auth/verify?token={verification_token}"

# TO:
verification_url = f"https://namaskah.app/auth/verify?token={verification_token}"
```

**Change 2** - Line 967:
```python
# FROM:
verification_url = f"http://localhost:8000/auth/verify?token={verification_token}"

# TO:
verification_url = f"https://namaskah.app/auth/verify?token={verification_token}"
```

**Change 3** - Line 992 (password reset):
```python
# FROM:
reset_url = f"http://localhost:8000/auth/reset-password?token={reset_token}"

# TO:
reset_url = f"https://namaskah.app/auth/reset-password?token={reset_token}"
```

---

### Step 4: Deploy (2 min)

```bash
git add main.py
git commit -m "Fix: Email URLs for production"
git push origin main
```

Render auto-deploys in ~3 minutes.

---

## ✅ Test It Works

**After deployment**:

1. Register new test user
2. Check email inbox
3. Click verification link
4. Should redirect to namaskah.app (not localhost)
5. Email should be verified

---

## 📊 Impact

**Before Fix**:
- ❌ Email verification broken
- ❌ Password reset broken
- ❌ No notifications
- ❌ Support emails don't work
- ❌ Users stuck unverified

**After Fix**:
- ✅ Email verification works
- ✅ Password reset works
- ✅ Notifications sent
- ✅ Support emails work
- ✅ Users can verify

---

## 🎯 Priority

**DO THIS FIRST** before anything else!

Without email:
- Users can't complete registration
- Platform appears broken
- No way to recover passwords
- Support system doesn't work

---

**Estimated Time**: 10 minutes  
**Difficulty**: Easy  
**Status**: ⏳ Waiting to be fixed
