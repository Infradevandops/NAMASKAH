// Google OAuth Configuration
window.GOOGLE_CLIENT_ID = null;
window.googleConfigLoaded = false;

// Create a timeout promise
const timeoutPromise = new Promise((_, reject) => 
    setTimeout(() => reject(new Error('Timeout')), 3000)
);

// Race between fetch and timeout
Promise.race([
    fetch('/auth/google/config'),
    timeoutPromise
])
    .then(r => r.ok ? r.json() : Promise.reject(new Error('Network error')))
    .then(data => {
        console.log('Google config loaded:', data);
        window.GOOGLE_CLIENT_ID = data.client_id;
        window.googleConfigLoaded = true;
        if (data.enabled && window.GOOGLE_CLIENT_ID) {
            console.log('Google OAuth enabled, loading SDK...');
            if (typeof window.loadGoogleSDK === 'function') {
                window.loadGoogleSDK();
            }
        } else {
            console.log('Google OAuth disabled, removing buttons');
            document.getElementById('google-auth-btn')?.remove();
            document.getElementById('google-separator')?.remove();
        }
    })
    .catch(error => {
        console.error('Google config error:', error);
        window.googleConfigLoaded = true;
        document.getElementById('google-auth-btn')?.remove();
        document.getElementById('google-separator')?.remove();
    });
