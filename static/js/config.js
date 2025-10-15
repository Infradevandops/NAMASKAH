// Google OAuth Configuration
// Loaded from backend .env file
let GOOGLE_CLIENT_ID = null;

// Fetch config from backend
fetch('/auth/google/config')
    .then(r => r.json())
    .then(data => {
        GOOGLE_CLIENT_ID = data.client_id;
        if (GOOGLE_CLIENT_ID && window.initGoogleSignIn) {
            window.initGoogleSignIn();
        }
    })
    .catch(() => console.log('Google OAuth not configured'));
