// Utility Functions
let isOnline = navigator.onLine;

window.addEventListener('online', () => {
    isOnline = true;
    showNotification('✅ Connection restored', 'success');
    if (window.token) checkAuth();
});

window.addEventListener('offline', () => {
    isOnline = false;
    showNotification('⚠️ Connection lost. Working offline...', 'error');
});

function formatPhoneNumber(phone) {
    if (!phone) return 'N/A';
    
    const cleaned = phone.replace(/\D/g, '');
    
    if (cleaned.length === 10) {
        return `+1-${cleaned.slice(0,3)}-${cleaned.slice(3,6)}-${cleaned.slice(6)}`;
    }
    else if (cleaned.length === 11 && cleaned[0] === '1') {
        return `+${cleaned[0]}-${cleaned.slice(1,4)}-${cleaned.slice(4,7)}-${cleaned.slice(7)}`;
    }
    else if (cleaned.length > 10) {
        const countryCode = cleaned.slice(0, cleaned.length - 10);
        const rest = cleaned.slice(-10);
        return `+${countryCode}-${rest.slice(0,3)}-${rest.slice(3,6)}-${rest.slice(6)}`;
    }
    
    return phone;
}

function showLoading(show = true) {
    document.getElementById('loading').classList.toggle('hidden', !show);
}

function showNotification(message, type) {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `notification ${type}`;
    notification.classList.remove('hidden');
    
    setTimeout(() => {
        notification.classList.add('hidden');
    }, 3000);
}

window.showApp = function() {
    console.log('showApp called');
    const authSection = document.getElementById('auth-section');
    const appSection = document.getElementById('app-section');
    
    if (!authSection || !appSection) {
        console.error('Auth or app section not found!');
        return;
    }
    
    console.log('Hiding auth, showing app');
    
    // Immediately hide auth and show app
    authSection.classList.add('hidden');
    appSection.classList.remove('hidden');
    document.getElementById('top-logout-btn').classList.remove('hidden');
    
    // Set opacity for fade in
    appSection.style.opacity = '1';
    
    showLoading(false);
    
    // Load data with error handling
    setTimeout(() => {
        try {
            if (typeof checkEmailVerification === 'function') checkEmailVerification();
            if (typeof loadServices === 'function') loadServices();
            if (typeof loadAPIKeys === 'function') loadAPIKeys();
            if (typeof loadWebhooks === 'function') loadWebhooks();
            if (typeof loadAnalytics === 'function') loadAnalytics();
            if (typeof loadNotificationSettings === 'function') loadNotificationSettings();
            if (typeof loadReferralStats === 'function') loadReferralStats();
            if (typeof loadActiveRentals === 'function') loadActiveRentals();
            if (typeof startHistoryRefresh === 'function') startHistoryRefresh();
        } catch (err) {
            console.error('Error loading app data:', err);
        }
    }, 100);
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text);
    showNotification('✅ Address copied to clipboard!', 'success');
}

// Check auth on load
window.token = localStorage.getItem('token');
console.log('Utils.js loaded, token:', window.token ? 'exists' : 'none');

if (window.token) {
    console.log('Token found, will check auth when ready');
    // Wait for DOM and all scripts to load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            setTimeout(() => {
                if (typeof checkAuth === 'function') {
                    checkAuth();
                } else {
                    console.error('checkAuth not found!');
                }
            }, 100);
        });
    } else {
        setTimeout(() => {
            if (typeof checkAuth === 'function') {
                checkAuth();
            } else {
                console.error('checkAuth not found!');
            }
        }, 100);
    }
} else {
    console.log('No token, checking for referral');
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('ref')) {
        setTimeout(() => {
            if (typeof showTab === 'function') showTab('register');
        }, 100);
    }
}
