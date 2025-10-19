// Google OAuth Configuration
window.GOOGLE_CLIENT_ID = null;
window.googleConfigLoaded = false;

// Fetch config from backend with timeout
const configTimeout = setTimeout(() => {
    window.googleConfigLoaded = true;
    const btn = document.getElementById('google-auth-btn');
    const sep = document.getElementById('google-separator');
    if (btn) btn.style.display = 'none';
    if (sep) sep.style.display = 'none';
}, 3000);

fetch('/auth/google/config', { timeout: 2000 })
    .then(r => r.json())
    .then(data => {
        clearTimeout(configTimeout);
        window.GOOGLE_CLIENT_ID = data.client_id;
        window.googleConfigLoaded = true;
        
        if (window.GOOGLE_CLIENT_ID && typeof window.loadGoogleSDK === 'function') {
            window.loadGoogleSDK();
        } else if (!window.GOOGLE_CLIENT_ID) {
            const btn = document.getElementById('google-auth-btn');
            const sep = document.getElementById('google-separator');
            if (btn) btn.style.display = 'none';
            if (sep) sep.style.display = 'none';
        }
    })
    .catch(() => {
        clearTimeout(configTimeout);
        window.googleConfigLoaded = true;
        const btn = document.getElementById('google-auth-btn');
        const sep = document.getElementById('google-separator');
        if (btn) btn.style.display = 'none';
        if (sep) sep.style.display = 'none';
    });
