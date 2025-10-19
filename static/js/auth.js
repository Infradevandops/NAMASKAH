// Authentication Module
window.token = localStorage.getItem('token');

async function register() {
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    
    console.log('Register attempt for:', email);
    
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
    
    console.log('Fetching:', url);
    
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
        console.log('Response status:', res.status);
        
        const data = await res.json();
        console.log('Response data:', data);
        showLoading(false);
        
        if (res.ok) {
            window.token = data.token;
            localStorage.setItem('token', data.token);
            showNotification(`✅ Welcome! You got ₵${data.credits} free credits`, 'success');
            console.log('Reloading page in 500ms');
            setTimeout(() => location.reload(), 500);
        } else {
            showNotification(`❌ ${data.detail || 'Registration failed'}`, 'error');
        }
    } catch (err) {
        showLoading(false);
        console.error('Register error:', err);
        console.error('Error name:', err.name);
        console.error('Error message:', err.message);
        if (err.name === 'AbortError') {
            showNotification('⏱️ Request timeout. Server may be down', 'error');
        } else {
            showNotification(`🌐 Network error: ${err.message}`, 'error');
        }
    }
}

async function login() {
    const email = document.getElementById('login-email')?.value;
    const password = document.getElementById('login-password')?.value;
    
    console.log('Login attempt for:', email);
    
    if (!email || !password) {
        showNotification('⚠️ Please enter email and password', 'error');
        return;
    }
    
    showLoading(true);
    
    try {
        const url = `${API_BASE}/auth/login`;
        console.log('Fetching:', url);
        
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000); // 10s timeout
        
        const res = await fetch(url, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({email, password}),
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        console.log('Response status:', res.status);
        
        const data = await res.json();
        console.log('Response data:', data);
        
        if (res.ok && data.token) {
            window.token = data.token;
            localStorage.setItem('token', data.token);
            
            showLoading(false);
            showNotification('✅ Login successful!', 'success');
            
            console.log('Reloading page in 500ms');
            setTimeout(() => {
                location.reload();
            }, 500);
        } else {
            showLoading(false);
            showNotification(`❌ ${data.detail || 'Invalid credentials'}`, 'error');
        }
    } catch (err) {
        showLoading(false);
        console.error('Login error:', err);
        console.error('Error name:', err.name);
        console.error('Error message:', err.message);
        if (err.name === 'AbortError') {
            showNotification('⏱️ Request timeout. Server may be down', 'error');
        } else {
            showNotification(`🌐 Network error: ${err.message}`, 'error');
        }
    }
}

async function checkAuth() {
    console.log('checkAuth called, token:', window.token);
    if (!window.token) {
        console.log('No token, showing auth section');
        document.getElementById('auth-section').classList.remove('hidden');
        document.getElementById('app-section').classList.add('hidden');
        return;
    }
    
    try {
        const res = await fetch(`${API_BASE}/auth/me`, {
            headers: {'Authorization': `Bearer ${window.token}`}
        });
        
        console.log('Auth response:', res.status);
        
        if (res.ok) {
            const user = await res.json();
            console.log('User loaded:', user.email);
            document.getElementById('user-email').textContent = user.email;
            document.getElementById('user-credits').textContent = user.credits.toFixed(2);
            document.getElementById('free-verifications').textContent = Math.floor(user.free_verifications || 0);
            console.log('Calling showApp()');
            if (typeof showApp === 'function') {
                showApp();
            } else {
                console.error('showApp function not found!');
            }
        } else {
            console.log('Auth failed, logging out');
            logout();
        }
    } catch (err) {
        console.error('Auth check error:', err);
        logout();
    }
}

function logout() {
    window.token = null;
    localStorage.removeItem('token');
    clearSession();
    stopAutoRefresh();
    stopHistoryRefresh();
    
    const authSection = document.getElementById('auth-section');
    const appSection = document.getElementById('app-section');
    
    // Fade out app section
    appSection.classList.add('fade-out');
    
    setTimeout(() => {
        document.getElementById('verifications').innerHTML = '';
        document.getElementById('top-logout-btn').classList.add('hidden');
        appSection.classList.add('hidden');
        appSection.classList.remove('fade-out');
        authSection.classList.remove('hidden');
        
        // Fade in auth section
        requestAnimationFrame(() => {
            authSection.style.opacity = '1';
        });
    }, 300);
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
            headers: { 'Authorization': `Bearer ${window.token}` }
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
            headers: { 'Authorization': `Bearer ${window.token}` }
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
