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

function showApp() {
    const authSection = document.getElementById('auth-section');
    const appSection = document.getElementById('app-section');
    
    // Fade out auth section
    authSection.classList.add('fade-out');
    
    setTimeout(() => {
        authSection.classList.add('hidden');
        authSection.classList.remove('fade-out');
        appSection.classList.remove('hidden');
        document.getElementById('top-logout-btn').classList.remove('hidden');
        
        // Fade in app section
        requestAnimationFrame(() => {
            appSection.style.opacity = '1';
        });
        
        showLoading(false);
        
        // Load data with error handling
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
    }, 300);
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text);
    showNotification('✅ Address copied to clipboard!', 'success');
}

// Check auth on load
window.token = localStorage.getItem('token');
if (window.token) {
    if (typeof checkAuth === 'function') {
        checkAuth();
    }
} else {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('ref')) {
        setTimeout(() => showTab('register'), 100);
    }
}
