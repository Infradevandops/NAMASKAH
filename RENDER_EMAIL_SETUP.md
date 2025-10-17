# 🚀 Quick Email Setup for Render (5 Minutes)

## ⚡ Fastest Method: Gmail

### Step 1: Get Gmail App Password (2 min)
1. Go to: https://myaccount.google.com/apppasswords
2. If you don't see it, enable 2FA first: https://myaccount.google.com/security
3. Create app password for "Mail" → "Other (Custom name)"
4. Copy the 16-character password (remove spaces!)

### Step 2: Add to Render (2 min)
1. Go to: https://dashboard.render.com
2. Select your service: **namaskah**
3. Click **Environment** tab
4. Add these variables:

```
BASE_URL=https://namaskah.onrender.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=abcdefghijklmnop
FROM_EMAIL=your-email@gmail.com
```

**Important**: 
- Replace `your-email@gmail.com` with your actual Gmail
- Replace `abcdefghijklmnop` with your 16-char app password (NO SPACES!)
- Keep `BASE_URL` exactly as shown

### Step 3: Redeploy (1 min)
1. Click **Manual Deploy** → **Deploy latest commit**
2. Wait ~3 minutes for deployment

### Step 4: Test (1 min)
1. Go to: https://namaskah.onrender.com/app
2. Register a new user with your email
3. Check your inbox for verification email
4. Click the link - should work! ✅

---

## 🎯 Alternative: SendGrid (Better for Production)

### Why SendGrid?
- More reliable delivery
- Better for production
- 100 emails/day free

### Setup (10 min)
1. Sign up: https://signup.sendgrid.com/
2. Create API Key: Settings → API Keys → Create
3. Verify sender: Settings → Sender Authentication
4. Add to Render:

```
BASE_URL=https://namaskah.onrender.com
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=SG.your-api-key-here
FROM_EMAIL=noreply@namaskah.app
```

**Note**: Username is literally "apikey"!

---

## ✅ Verification

After deployment, check:
- [ ] Register new user → Email received
- [ ] Click verification link → Redirects to production URL
- [ ] Email marked as verified in dashboard
- [ ] Password reset works
- [ ] SMS notifications work

---

## 🐛 Troubleshooting

### No email received?
1. Check Render logs for "Email error:"
2. Verify SMTP credentials are correct
3. Check spam folder
4. Test SMTP connection locally

### Email links go to localhost?
- Make sure `BASE_URL=https://namaskah.onrender.com` is set on Render
- Redeploy after adding

### Gmail "Less secure app" error?
- Use App Password, not regular password
- Enable 2FA first

---

## 📞 Need Help?

See full guide: `EMAIL_SETUP_GUIDE.md`

---

**Current Status**: Email system fixed, ready for production ✅
**Deployment**: Auto-deploys on push to main
**URL**: https://namaskah.onrender.com
