// Google OAuth Configuration
window.GOOGLE_CLIENT_ID = null;
window.googleConfigLoaded = false;

fetch('/auth/google/config', { timeout: 3000 })
    .then(r => r.ok ? r.json() : Promise.reject())
    .then(data => {
        window.GOOGLE_CLIENT_ID = data.client_id;
        window.googleConfigLoaded = true;
        if (data.enabled && window.GOOGLE_CLIENT_ID) {
            if (typeof window.loadGoogleSDK === 'function') window.loadGoogleSDK();
        } else {
            document.getElementById('google-auth-btn')?.remove();
            document.getElementById('google-separator')?.remove();
        }
    })
    .catch(() => {
        window.googleConfigLoaded = true;
        document.getElementById('google-auth-btn')?.remove();
        document.getElementById('google-separator')?.remove();
    });
