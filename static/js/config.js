// Google OAuth Configuration
window.GOOGLE_CLIENT_ID = null;
window.googleConfigLoaded = false;

// Fetch config from backend with timeout
const configTimeout = setTimeout(() => {
    console.log('Google config timeout - hiding button');
    window.googleConfigLoaded = true;
    const btn = document.getElementById('google-auth-btn');
    const sep = document.getElementById('google-separator');
    if (btn) btn.style.display = 'none';
    if (sep) sep.style.display = 'none';
}, 5000);

fetch('/auth/google/config')
    .then(r => {
        if (!r.ok) throw new Error('Config fetch failed');
        return r.json();
    })
    .then(data => {
        clearTimeout(configTimeout);
        console.log('Google config loaded:', data);
        window.GOOGLE_CLIENT_ID = data.client_id;
        window.googleConfigLoaded = true;
        
        if (window.GOOGLE_CLIENT_ID && data.enabled) {
            console.log('Google OAuth enabled, loading SDK');
            if (typeof window.loadGoogleSDK === 'function') {
                window.loadGoogleSDK();
            }
        } else {
            console.log('Google OAuth not configured');
            const btn = document.getElementById('google-auth-btn');
            const sep = document.getElementById('google-separator');
            if (btn) btn.style.display = 'none';
            if (sep) sep.style.display = 'none';
        }
    })
    .catch(err => {
        clearTimeout(configTimeout);
        console.error('Google config error:', err);
        window.googleConfigLoaded = true;
        const btn = document.getElementById('google-auth-btn');
        const sep = document.getElementById('google-separator');
        if (btn) btn.style.display = 'none';
        if (sep) sep.style.display = 'none';
    });
