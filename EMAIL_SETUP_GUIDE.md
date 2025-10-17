# Email System Setup Guide

## 🚨 CRITICAL: Email Verification Required

The platform requires email verification for new users. Without SMTP configured, users cannot:
- Verify their email addresses
- Reset passwords
- Receive SMS notifications
- Get low balance alerts

---

## ✅ What Was Fixed

1. **BASE_URL Configuration**: All email links now use `BASE_URL` environment variable instead of hardcoded `http://localhost:8000`
2. **Environment Variable**: Added `BASE_URL` to `.env` files
3. **Production Ready**: Email links will work correctly in production

---

## 🔧 Setup Instructions for Render

### Step 1: Choose Email Provider

**Option A: Gmail (Quick Setup - 5 minutes)**
- Free for low volume
- Easy to set up
- Good for testing/small scale

**Option B: SendGrid (Recommended - 10 minutes)**
- Free tier: 100 emails/day
- Professional delivery
- Better for production

**Option C: AWS SES (Advanced - 20 minutes)**
- Very cheap ($0.10 per 1000 emails)
- Requires AWS account
- Best for high volume

---

## 📧 Option A: Gmail Setup

### 1. Enable 2-Factor Authentication
1. Go to https://myaccount.google.com/security
2. Enable "2-Step Verification"

### 2. Generate App Password
1. Go to https://myaccount.google.com/apppasswords
2. Select "Mail" and "Other (Custom name)"
3. Name it "Namaskah SMS"
4. Copy the 16-character password (e.g., `abcd efgh ijkl mnop`)

### 3. Add to Render Environment Variables
Go to your Render dashboard → Service → Environment:

```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=abcdefghijklmnop
FROM_EMAIL=your-email@gmail.com
BASE_URL=https://namaskah.onrender.com
```

**Important**: Remove spaces from app password!

---

## 📧 Option B: SendGrid Setup (Recommended)

### 1. Create SendGrid Account
1. Go to https://signup.sendgrid.com/
2. Sign up (free tier: 100 emails/day)
3. Verify your email

### 2. Create API Key
1. Go to Settings → API Keys
2. Click "Create API Key"
3. Name: "Namaskah SMS"
4. Permissions: "Full Access"
5. Copy the API key (starts with `SG.`)

### 3. Verify Sender Identity
1. Go to Settings → Sender Authentication
2. Click "Verify a Single Sender"
3. Fill in your details
4. Verify the email they send you

### 4. Add to Render Environment Variables
```
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=SG.your-api-key-here
FROM_EMAIL=noreply@namaskah.app
BASE_URL=https://namaskah.onrender.com
```

**Note**: Username is literally "apikey", not your email!

---

## 📧 Option C: AWS SES Setup

### 1. Create AWS Account
1. Go to https://aws.amazon.com/
2. Sign up (requires credit card)

### 2. Verify Email Address
1. Go to AWS SES Console
2. Click "Verified identities"
3. Click "Create identity"
4. Choose "Email address"
5. Enter your email and verify

### 3. Create SMTP Credentials
1. Go to "SMTP settings"
2. Click "Create SMTP credentials"
3. Download the credentials CSV

### 4. Request Production Access
1. Go to "Account dashboard"
2. Click "Request production access"
3. Fill out the form (takes 24 hours)

### 5. Add to Render Environment Variables
```
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USER=your-smtp-username
SMTP_PASSWORD=your-smtp-password
FROM_EMAIL=noreply@namaskah.app
BASE_URL=https://namaskah.onrender.com
```

---

## 🚀 Deployment Steps

### 1. Set Environment Variables on Render

Go to: https://dashboard.render.com → Your Service → Environment

Add these variables:
```
BASE_URL=https://namaskah.onrender.com
SMTP_HOST=<your-smtp-host>
SMTP_PORT=587
SMTP_USER=<your-smtp-user>
SMTP_PASSWORD=<your-smtp-password>
FROM_EMAIL=noreply@namaskah.app
```

### 2. Trigger Redeploy

After adding environment variables:
1. Click "Manual Deploy" → "Deploy latest commit"
2. Or push a new commit to trigger auto-deploy

### 3. Test Email System

1. Register a new user at https://namaskah.onrender.com/app
2. Check your email for verification link
3. Click the link - should redirect to production URL
4. Verify email is marked as verified

---

## 🧪 Testing Locally

### 1. Update .env file
```bash
BASE_URL=http://localhost:8000
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com
```

### 2. Restart server
```bash
python main.py
```

### 3. Test registration
1. Go to http://localhost:8000/app
2. Register with your email
3. Check inbox for verification email
4. Click link to verify

---

## 🔍 Troubleshooting

### Email not sending?

**Check 1: SMTP credentials**
```bash
# Test SMTP connection
python -c "
import smtplib
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login('your-email@gmail.com', 'your-app-password')
print('✅ SMTP connection successful!')
server.quit()
"
```

**Check 2: Environment variables**
- Go to Render dashboard
- Check all SMTP variables are set
- No extra spaces in values
- BASE_URL is correct

**Check 3: Logs**
- Check Render logs for email errors
- Look for "Email error:" messages

### Email links go to localhost?

**Fix**: Set `BASE_URL` environment variable on Render:
```
BASE_URL=https://namaskah.onrender.com
```

### Gmail "Less secure app" error?

**Fix**: Use App Password, not regular password
- Enable 2FA first
- Generate App Password
- Use 16-char password without spaces

### SendGrid "Sender not verified" error?

**Fix**: Verify sender identity
- Go to SendGrid → Settings → Sender Authentication
- Verify your email address
- Use verified email in `FROM_EMAIL`

---

## 📊 Email Limits

| Provider | Free Tier | Cost After |
|----------|-----------|------------|
| Gmail | ~500/day | N/A (personal use) |
| SendGrid | 100/day | $19.95/month (40k/month) |
| AWS SES | 62,000/month | $0.10 per 1,000 emails |

---

## ✅ Verification Checklist

- [ ] SMTP credentials configured on Render
- [ ] BASE_URL set to production URL
- [ ] FROM_EMAIL matches verified sender
- [ ] Test registration sends email
- [ ] Email links redirect to production
- [ ] Password reset works
- [ ] SMS notifications work

---

## 🎯 Quick Start (5 minutes)

**For immediate testing with Gmail:**

1. **Get Gmail App Password**
   - https://myaccount.google.com/apppasswords
   - Create password, copy it

2. **Add to Render**
   ```
   BASE_URL=https://namaskah.onrender.com
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=abcdefghijklmnop
   FROM_EMAIL=your-email@gmail.com
   ```

3. **Redeploy**
   - Click "Manual Deploy"

4. **Test**
   - Register new user
   - Check email
   - Click verification link

Done! ✅

---

## 📞 Support

If you encounter issues:
1. Check Render logs for errors
2. Test SMTP connection locally
3. Verify environment variables are set
4. Check email provider dashboard for errors

---

**Last Updated**: 2024
**Status**: Ready for production deployment
