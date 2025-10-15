# 🚀 Render Deployment Setup

## Add Your Domain to Google OAuth

### Step 1: Update Google Cloud Console

1. Go to: https://console.cloud.google.com/
2. Navigate to: **APIs & Services** → **Credentials**
3. Click on your **OAuth 2.0 Client ID**
4. Add to **Authorized JavaScript origins**:
   ```
   https://namaskah-app.onrender.com
   ```
5. Add to **Authorized redirect URIs**:
   ```
   https://namaskah-app.onrender.com
   ```
6. Click **Save**

### Step 2: Set Environment Variables on Render

In your Render dashboard, add these environment variables:

```bash
# Required
TEXTVERIFIED_API_KEY=MSZ9Lr6XnKPTBNjnrHjD6mXi0ESmYUX7pdDEve9TbK8msE3hag6N1OQcPYREg
TEXTVERIFIED_EMAIL=huff_06psalm@icloud.com
JWT_SECRET_KEY=Namaskah2024SecureJWTKeyForProductionUse32Chars
DATABASE_URL=sqlite:///./sms.db

# Google OAuth
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret

# Security
ALLOWED_HOSTS=namaskah-app.onrender.com
CORS_ORIGINS=https://namaskah-app.onrender.com
```

### Step 3: Deploy

```bash
git push origin main
```

Render will auto-deploy!

### Step 4: Test

Visit: https://namaskah-app.onrender.com/app

Click "Sign in with Google" - should work! ✅

## Summary

**Add to Google Console**:
- Authorized JavaScript origins: `https://namaskah-app.onrender.com`
- Authorized redirect URIs: `https://namaskah-app.onrender.com`

**That's it!** Google OAuth will work on production.
