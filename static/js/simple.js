// Minimal Namaskah SMS Frontend - Core Functionality Only
const API_BASE = '';
let currentVerificationId = null;
let autoRefreshInterval = null;

// Authentication
async function login(email, password) {
    try {
        const res = await fetch('/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        
        const data = await res.json();
        
        if (res.ok) {
            localStorage.setItem('token', data.token);
            return { success: true, data };
        } else {
            return { success: false, error: data.detail || 'Login failed' };
        }
    } catch (err) {
        return { success: false, error: 'Network error' };
    }
}

async function register(email, password) {
    try {
        const res = await fetch('/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        
        const data = await res.json();
        
        if (res.ok) {
            localStorage.setItem('token', data.token);
            return { success: true, data };
        } else {
            return { success: false, error: data.detail || 'Registration failed' };
        }
    } catch (err) {
        return { success: false, error: 'Network error' };
    }
}

async function getUserData() {
    const token = localStorage.getItem('token');
    if (!token) return null;
    
    try {
        const res = await fetch('/auth/me', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (res.ok) {
            return await res.json();
        }
    } catch (err) {
        console.error('Failed to load user data:', err);
    }
    return null;
}

// Verification
async function createVerification(serviceName) {
    const token = localStorage.getItem('token');
    if (!token) return { success: false, error: 'Not authenticated' };
    
    try {
        const res = await fetch('/verify/create', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ service_name: serviceName })
        });
        
        const data = await res.json();
        
        if (res.ok) {
            currentVerificationId = data.id;
            return { success: true, data };
        } else {
            return { success: false, error: data.detail || 'Failed to create verification', status: res.status };
        }
    } catch (err) {
        return { success: false, error: 'Network error' };
    }
}

async function checkMessages() {
    if (!currentVerificationId) return { success: false, error: 'No active verification' };
    
    const token = localStorage.getItem('token');
    
    try {
        const res = await fetch(`/verify/${currentVerificationId}/messages`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (res.ok) {
            const data = await res.json();
            return { success: true, data };
        } else {
            return { success: false, error: 'Failed to check messages' };
        }
    } catch (err) {
        return { success: false, error: 'Network error' };
    }
}

async function cancelVerification() {
    if (!currentVerificationId) return { success: false, error: 'No active verification' };
    
    const token = localStorage.getItem('token');
    
    try {
        const res = await fetch(`/verify/${currentVerificationId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        const data = await res.json();
        
        if (res.ok) {
            currentVerificationId = null;
            return { success: true, data };
        } else {
            return { success: false, error: data.detail || 'Failed to cancel verification' };
        }
    } catch (err) {
        return { success: false, error: 'Network error' };
    }
}

// Wallet
async function fundWallet(amount) {
    const token = localStorage.getItem('token');
    if (!token) return { success: false, error: 'Not authenticated' };
    
    try {
        const res = await fetch('/wallet/fund', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ amount, method: 'paystack' })
        });
        
        const data = await res.json();
        
        if (res.ok) {
            return { success: true, data };
        } else {
            return { success: false, error: data.detail || 'Payment failed' };
        }
    } catch (err) {
        return { success: false, error: 'Network error' };
    }
}

// Auto-refresh
function startAutoRefresh(callback) {
    if (autoRefreshInterval) clearInterval(autoRefreshInterval);
    
    autoRefreshInterval = setInterval(async () => {
        if (currentVerificationId) {
            const result = await checkMessages();
            if (callback) callback(result);
        }
    }, 10000);
}

function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }
}

// Utilities
function extractCode(message) {
    const match = message.match(/\b\d{4,8}\b/);
    return match ? match[0] : message;
}

function copyToClipboard(text) {
    return navigator.clipboard.writeText(text);
}

function logout() {
    localStorage.removeItem('token');
    currentVerificationId = null;
    stopAutoRefresh();
}

// Export functions for global use
window.NamaskahAPI = {
    login,
    register,
    getUserData,
    createVerification,
    checkMessages,
    cancelVerification,
    fundWallet,
    startAutoRefresh,
    stopAutoRefresh,
    extractCode,
    copyToClipboard,
    logout
};