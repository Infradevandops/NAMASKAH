# 🔐 Google OAuth Setup Guide

## Quick Setup (5 minutes)

### 1. Create Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable **Google+ API**
4. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
5. Configure OAuth consent screen:
   - User Type: External
   - App name: Namaskah SMS
   - User support email: your-email@example.com
   - Developer contact: your-email@example.com
6. Create OAuth Client ID:
   - Application type: **Web application**
   - Name: Namaskah SMS Web
   - Authorized JavaScript origins:
     - `http://localhost:8000`
     - `https://your-domain.com` (production)
   - Authorized redirect URIs:
     - `http://localhost:8000`
     - `https://your-domain.com` (production)

### 2. Configure Environment Variables

Edit `.env`:
```bash
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
```

### 3. Update Frontend

Edit `templates/index.html` line 587:
```javascript
client_id: 'YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com',
```

Replace with your actual Client ID.

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Test

```bash
./start.sh
```

Visit `http://localhost:8000/app` and click "Sign in with Google"

## Features

✅ One-click sign-in with Google  
✅ Auto-creates account if new user  
✅ $5 free credits on signup  
✅ Secure JWT token authentication  
✅ Works alongside email/password login  

## Security

- Google handles password security
- JWT tokens expire after 30 days
- User data isolated per account
- HTTPS required in production

## Troubleshooting

**"Invalid client ID"**
- Check GOOGLE_CLIENT_ID in .env
- Update client_id in index.html
- Verify domain in Google Console

**"Redirect URI mismatch"**
- Add your domain to Authorized redirect URIs
- Include both http://localhost:8000 and production URL

**"Access blocked"**
- Complete OAuth consent screen
- Add test users in Google Console
- Publish app (for production)

## Production Checklist

- [ ] Add production domain to Authorized origins
- [ ] Add production domain to Redirect URIs
- [ ] Update client_id in index.html
- [ ] Set GOOGLE_CLIENT_ID in production .env
- [ ] Enable HTTPS
- [ ] Publish OAuth consent screen

---

**Simple. Secure. Fast.**
