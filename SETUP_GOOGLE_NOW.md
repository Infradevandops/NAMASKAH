# 🚀 Setup Google OAuth NOW (5 Minutes)

## Option 1: Automated Setup (Recommended)

Run this command and follow the prompts:

```bash
./setup_google.sh
```

It will guide you through getting your Client ID and configure everything automatically.

## Option 2: Manual Setup

### Step 1: Get Client ID (3 minutes)

1. **Open**: https://console.cloud.google.com/
2. **Create** a new project (or select existing)
3. **Go to**: APIs & Services → Credentials
4. **Click**: Create Credentials → OAuth 2.0 Client ID
5. **Configure** consent screen (if needed):
   - App name: `Namaskah SMS`
   - User support email: your email
   - Save and continue
6. **Create** OAuth Client ID:
   - Application type: **Web application**
   - Name: `Namaskah SMS`
   - Authorized JavaScript origins: `http://localhost:8000`
   - Authorized redirect URIs: `http://localhost:8000`
   - Click **Create**
7. **Copy** your Client ID (looks like: `123456-abc.apps.googleusercontent.com`)

### Step 2: Configure App (30 seconds)

Edit `static/js/config.js`:

```javascript
// Replace this line:
const GOOGLE_CLIENT_ID = '1084434463992-demo.apps.googleusercontent.com';

// With your actual Client ID:
const GOOGLE_CLIENT_ID = 'YOUR-ACTUAL-CLIENT-ID.apps.googleusercontent.com';
```

### Step 3: Test (1 minute)

```bash
# Restart app
./start.sh

# Open browser
open http://localhost:8000/app

# Click "Sign in with Google" button
# Should work! ✅
```

## Troubleshooting

### "Error 400: redirect_uri_mismatch"
- Make sure you added `http://localhost:8000` to **both**:
  - Authorized JavaScript origins
  - Authorized redirect URIs

### "Error 400: invalid_client"
- Double-check your Client ID in `static/js/config.js`
- Make sure there are no extra spaces or quotes

### Buttons don't appear
- Check browser console for errors
- Make sure Client ID is not `null` or contains 'demo'
- Refresh the page (Cmd+Shift+R / Ctrl+Shift+R)

## What You Get

✅ One-click sign-in with Google  
✅ One-click sign-up with Google  
✅ Auto-creates accounts for new users  
✅ $5 free credits on signup  
✅ No password needed  
✅ Secure authentication  

## Production Deployment

When deploying to production:

1. Add your production domain to Google Console:
   - `https://yourdomain.com`
2. Use the same Client ID
3. Deploy!

---

**Need help?** Open an issue or check `GOOGLE_OAUTH_SETUP.md` for detailed guide.
