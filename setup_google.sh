#!/bin/bash

echo "🔐 Google OAuth Setup Helper"
echo "=============================="
echo ""
echo "To enable Google Sign-In, you need a Client ID from Google."
echo ""
echo "📋 Quick Steps:"
echo ""
echo "1. Open: https://console.cloud.google.com/"
echo "2. Create a new project (or select existing)"
echo "3. Go to: APIs & Services → Credentials"
echo "4. Click: Create Credentials → OAuth 2.0 Client ID"
echo "5. Configure consent screen if prompted:"
echo "   - App name: Namaskah SMS"
echo "   - User support email: your email"
echo "6. Create OAuth Client ID:"
echo "   - Application type: Web application"
echo "   - Name: Namaskah SMS"
echo "   - Authorized JavaScript origins: http://localhost:8000"
echo "   - Authorized redirect URIs: http://localhost:8000"
echo "7. Copy your Client ID"
echo ""
echo "8. Paste it here:"
read -p "Enter your Google Client ID: " client_id

if [ -z "$client_id" ]; then
    echo "❌ No Client ID provided. Exiting."
    exit 1
fi

# Update config.js
sed -i.bak "s|const GOOGLE_CLIENT_ID = '.*';|const GOOGLE_CLIENT_ID = '$client_id';|" static/js/config.js

echo ""
echo "✅ Google OAuth configured!"
echo ""
echo "🚀 Next steps:"
echo "1. Restart the app: ./start.sh"
echo "2. Visit: http://localhost:8000/app"
echo "3. Click 'Sign in with Google' button"
echo ""
echo "Done! 🎉"
