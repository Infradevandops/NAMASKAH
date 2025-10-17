// Utility Functions
let isOnline = navigator.onLine;

window.addEventListener('online', () => {
    isOnline = true;
    showNotification('✅ Connection restored', 'success');
    if (token) checkAuth();
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
    document.getElementById('auth-section').classList.add('hidden');
    document.getElementById('app-section').classList.remove('hidden');
    document.getElementById('top-logout-btn').classList.remove('hidden');
    
    checkEmailVerification();
    
    loadServices();
    loadHistory();
    loadTransactions();
    loadAPIKeys();
    loadWebhooks();
    loadAnalytics();
    loadNotificationSettings();
    loadReferralStats();
    loadActiveRentals();
    startHistoryRefresh();
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text);
    showNotification('✅ Address copied to clipboard!', 'success');
}

// Check auth on load
if (token) {
    checkAuth();
} else {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('ref')) {
        setTimeout(() => showTab('register'), 100);
    }
}
