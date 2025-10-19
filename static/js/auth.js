// Authentication Module
let token = localStorage.getItem('token');

async function register() {
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    
    if (!email || !password) {
        showNotification('⚠️ Please enter email and password', 'error');
        return;
    }
    
    if (password.length < 6) {
        showNotification('⚠️ Password must be at least 6 characters', 'error');
        return;
    }
    
    showLoading(true);
    
    const urlParams = new URLSearchParams(window.location.search);
    const refCode = urlParams.get('ref');
    const url = refCode ? `${API_BASE}/auth/register?referral_code=${refCode}` : `${API_BASE}/auth/register`;
    
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000);
        
        const res = await fetch(url, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({email, password}),
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        const data = await res.json();
        showLoading(false);
        
        if (res.ok) {
            token = data.token;
            localStorage.setItem('token', token);
            showNotification(`✅ Welcome! You got ₵${data.credits} free credits`, 'success');
            showApp();
        } else {
            showNotification(`❌ ${data.detail || 'Registration failed'}`, 'error');
        }
    } catch (err) {
        showLoading(false);
        if (err.name === 'AbortError') {
            showNotification('⏱️ Request timeout. Server may be down', 'error');
        } else {
            showNotification('🌐 Network error. Check your connection', 'error');
        }
    }
}

async function login() {
    const email = document.getElementById('login-email')?.value;
    const password = document.getElementById('login-password')?.value;
    
    if (!email || !password) {
        showNotification('⚠️ Please enter email and password', 'error');
        return;
    }
    
    showLoading(true);
    
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000); // 10s timeout
        
        const res = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({email, password}),
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        const data = await res.json();
        
        if (res.ok && data.token) {
            if (typeof clearSession === 'function') clearSession();
            token = data.token;
            localStorage.setItem('token', token);
            showLoading(false);
            showNotification('✅ Login successful!', 'success');
            
            // Force page transition
            setTimeout(() => {
                if (typeof showApp === 'function') {
                    showApp();
                } else {
                    checkAuth();
                }
            }, 300);
        } else {
            showLoading(false);
            showNotification(`❌ ${data.detail || 'Invalid credentials'}`, 'error');
        }
    } catch (err) {
        showLoading(false);
        console.error('Login error:', err);
        if (err.name === 'AbortError') {
            showNotification('⏱️ Request timeout. Server may be down', 'error');
        } else {
            showNotification('🌐 Network error. Check your connection', 'error');
        }
    }
}

async function checkAuth() {
    try {
        const res = await fetch(`${API_BASE}/auth/me`, {
            headers: {'Authorization': `Bearer ${token}`}
        });
        
        if (res.ok) {
            const user = await res.json();
            document.getElementById('user-email').textContent = user.email;
            document.getElementById('user-credits').textContent = user.credits.toFixed(2);
            document.getElementById('free-verifications').textContent = Math.floor(user.free_verifications || 0);
            showApp();
        } else {
            logout();
        }
    } catch (err) {
        logout();
    }
}

function logout() {
    token = null;
    localStorage.removeItem('token');
    clearSession();
    stopAutoRefresh();
    stopHistoryRefresh();
    
    document.getElementById('verifications').innerHTML = '';
    document.getElementById('top-logout-btn').classList.add('hidden');
    document.getElementById('auth-section').classList.remove('hidden');
    document.getElementById('app-section').classList.add('hidden');
}

function showTab(tab) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    event.target.classList.add('active');
    
    if (tab === 'login') {
        document.getElementById('login-form').classList.remove('hidden');
        document.getElementById('register-form').classList.add('hidden');
    } else {
        document.getElementById('login-form').classList.add('hidden');
        document.getElementById('register-form').classList.remove('hidden');
    }
}

async function checkEmailVerification() {
    try {
        const res = await fetch(`${API_BASE}/auth/me`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await res.json();
        
        const rentalBanner = document.getElementById('rental-verification-banner');
        if (rentalBanner) {
            if (!data.email_verified) {
                // Show banner if not verified
                rentalBanner.classList.remove('hidden');
            } else {
                // Hide banner if verified
                rentalBanner.classList.add('hidden');
            }
        }
    } catch (error) {
        console.error('Email verification check failed:', error);
    }
}

async function resendVerificationEmail() {
    try {
        const res = await fetch(`${API_BASE}/auth/resend-verification`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (res.ok) {
            alert('✅ Verification email sent! Check your inbox.');
        } else {
            const data = await res.json();
            alert('❌ ' + (data.detail || 'Failed to send email'));
        }
    } catch (error) {
        alert('❌ Error sending verification email');
    }
}

window.showForgotPassword = function() {
    document.getElementById('forgot-password-modal').style.display = 'block';
}

window.closeForgotPassword = function() {
    document.getElementById('forgot-password-modal').style.display = 'none';
    document.getElementById('reset-email').value = '';
}

window.sendResetEmail = async function() {
    const email = document.getElementById('reset-email').value;
    if (!email) {
        showNotification('Please enter your email', 'error');
        return;
    }
    try {
        const response = await fetch('/auth/forgot-password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email })
        });
        const data = await response.json();
        if (response.ok) {
            showNotification('Password reset link sent to your email', 'success');
            closeForgotPassword();
        } else {
            showNotification(data.detail || 'Failed to send reset link', 'error');
        }
    } catch (error) {
        showNotification('Network error', 'error');
    }
}
