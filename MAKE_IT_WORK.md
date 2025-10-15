# ⚡ Make Google OAuth Work RIGHT NOW

## 🎯 Goal
Get Google Sign-In working in 5 minutes

## 🚀 Quick Start

### Method 1: Automated (Easiest)
```bash
./setup_google.sh
```
Follow the prompts. Done!

### Method 2: Manual (5 steps)

#### 1. Get Client ID (3 min)
- Go to: https://console.cloud.google.com/
- Create project → APIs & Services → Credentials
- Create OAuth 2.0 Client ID
- Add origin: `http://localhost:8000`
- Copy Client ID

#### 2. Configure (30 sec)
Edit `static/js/config.js`:
```javascript
const GOOGLE_CLIENT_ID = 'paste-your-client-id-here';
```

#### 3. Restart (10 sec)
```bash
./start.sh
```

#### 4. Test (30 sec)
- Open: http://localhost:8000/app
- Click "Sign in with Google"
- ✅ Works!

## 📸 What You'll See

### Before Setup:
- Clean login form
- Email/password only
- No Google buttons (hidden)

### After Setup:
- "Sign in with Google" button appears
- "Sign up with Google" button appears
- One-click authentication
- $5 free credits on signup

## ✅ Verification

Test if it's working:
```bash
# Open browser console (F12)
# Look for: "Google Sign-In initialized"
# Click Google button
# Should redirect to Google login
```

## 🔧 Files to Edit

Only ONE file needs editing:
- `static/js/config.js` (line 13)

That's it!

## 📚 Detailed Guides

- **Quick**: `SETUP_GOOGLE_NOW.md`
- **Full**: `GOOGLE_OAUTH_SETUP.md`
- **Status**: `GOOGLE_OAUTH_STATUS.md`

## 💡 Pro Tips

1. **Use the automated script**: `./setup_google.sh`
2. **Test locally first**: http://localhost:8000
3. **Same Client ID works for production**: Just add your domain
4. **No backend changes needed**: Everything is ready

## 🆘 Common Issues

**Buttons don't show?**
- Check `static/js/config.js` has real Client ID
- Refresh page (Cmd+Shift+R)

**Error 400?**
- Add `http://localhost:8000` to Google Console origins
- Check Client ID is correct

**Still not working?**
- Run: `./setup_google.sh`
- Follow the prompts
- It will fix everything

---

**Ready?** Run `./setup_google.sh` now! 🚀
