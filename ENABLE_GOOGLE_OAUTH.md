# 🚀 Enable Google OAuth - 2 Minute Setup

## Current Status
❌ Google Sign-In is **DISABLED** (shows Error 400 if clicked)

## Quick Enable (2 steps)

### Step 1: Get Google Client ID (2 minutes)

1. Go to https://console.cloud.google.com/
2. Create new project or select existing
3. Go to **APIs & Services** → **Credentials**
4. Click **Create Credentials** → **OAuth 2.0 Client ID**
5. Configure consent screen (if needed):
   - App name: `Namaskah SMS`
   - User support email: your email
6. Create OAuth Client:
   - Application type: **Web application**
   - Authorized JavaScript origins: `http://localhost:8000`
   - Authorized redirect URIs: `http://localhost:8000`
7. Copy your **Client ID** (looks like: `123456-abc.apps.googleusercontent.com`)

### Step 2: Enable in App (10 seconds)

Edit `static/js/config.js`:

```javascript
// Change this line:
const GOOGLE_CLIENT_ID = null;

// To this (with YOUR Client ID):
const GOOGLE_CLIENT_ID = '123456-abc.apps.googleusercontent.com';
```

**That's it!** Refresh the page and Google Sign-In buttons will appear! 🎉

## Test It

1. Restart app: `./start.sh`
2. Visit: http://localhost:8000/app
3. Click **"Sign in with Google"** button
4. Should work perfectly! ✅

## Keep It Disabled

If you don't want Google OAuth, just leave `GOOGLE_CLIENT_ID = null` in config.js.
The buttons will be hidden automatically.

## Production Deployment

When deploying to production:

1. Add your production domain to Google Console:
   - Authorized origins: `https://yourdomain.com`
   - Redirect URIs: `https://yourdomain.com`
2. Update `static/js/config.js` with same Client ID
3. Deploy!

---

**Need help?** See full guide: `GOOGLE_OAUTH_SETUP.md`
