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
        const timeoutId = setTimeout(() => controller.abort(), 15000);
        
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
        
        if (res.ok) {
            window.token = data.token;
            localStorage.setItem('token', data.token);
            if (data.is_admin) localStorage.setItem('admin_token', data.token);
            
            // Track user registration
            if (typeof trackUserRegistration === 'function') {
                trackUserRegistration('email');
            }
            
            showLoading(false);
            showNotification(`✅ Welcome! You got 1 free verification`, 'success');
            console.log('Calling checkAuth to load app');
            
            // Call checkAuth instead of reload
            setTimeout(() => {
                if (typeof checkAuth === 'function') {
                    checkAuth();
                } else {
                    window.location.reload();
                }
            }, 500);
        } else {
            showLoading(false);
            showNotification(`❌ ${data.detail || 'Registration failed'}`, 'error');
        }
    } catch (err) {
        showLoading(false);
        console.error('Register error:', err);
        console.error('Error name:', err.name);
        console.error('Error message:', err.message);
        if (err.name === 'AbortError') {
            showNotification('⏱️ Request timeout. Please check your connection', 'error');
        } else {
            showNotification(`🌐 Network error: ${err.message}`, 'error');
        }
    }
}

async function login() {
    const email = document.getElementById('login-email')?.value;
    const password = document.getElementById('login-password')?.value;
    const loginBtn = document.getElementById('login-btn') || document.querySelector('[onclick*="login"]');
    
    console.log('Login attempt for:', email);
    
    // Use minimal validation if available
    if (typeof validateForm === 'function') {
        const form = document.getElementById('login-form') || document.querySelector('form');
        if (form && !validateForm(form)) return;
    } else if (!email || !password) {
        showNotification('⚠️ Please enter email and password', 'error');
        return;
    }
    
    showLoading(true);
    
    try {
        const url = `${API_BASE}/auth/login`;
        console.log('Fetching:', url);
        
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 15000); // 15s timeout
        
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
            if (data.is_admin) localStorage.setItem('admin_token', data.token);
            
            // Track user login
            if (typeof trackUserLogin === 'function') {
                trackUserLogin('email');
            }
            
            showLoading(false);
            showNotification('✅ Login successful!', 'success');
            console.log('Calling checkAuth to load app');
            
            // Call checkAuth instead of reload
            setTimeout(() => {
                if (typeof checkAuth === 'function') {
                    checkAuth();
                } else {
                    window.location.reload();
                }
            }, 500);
        } else {
            showLoading(false);
            showNotification(`❌ ${data.detail || 'Invalid credentials'}`, 'error');
        }
    } catch (err) {
        showLoading(false);
        console.error('Login error:', err);
        
        // Use minimal error handling if available
        if (typeof handleNetworkError === 'function') {
            handleNetworkError(err);
        } else {
            if (err.name === 'AbortError') {
                showNotification('⏱️ Request timeout. Please check your connection', 'error');
            } else {
                showNotification(`🌐 Network error: ${err.message}`, 'error');
            }
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
            console.log('User loaded:', user);
            
            if (!user || !user.email) {
                console.error('Invalid user data:', user);
                logout();
                return;
            }
            
            // Update UI
            document.getElementById('user-email').textContent = user.email;
            document.getElementById('user-credits').textContent = user.credits.toFixed(2);
            document.getElementById('free-verifications').textContent = Math.floor(user.free_verifications || 0);
            
            // Show app directly
            console.log('Showing app section');
            document.getElementById('auth-section').classList.add('hidden');
            document.getElementById('app-section').classList.remove('hidden');
            document.getElementById('top-logout-btn').classList.remove('hidden');
            
            // Load app data
            setTimeout(() => {
                if (typeof loadServices === 'function') loadServices();
                if (typeof loadAPIKeys === 'function') loadAPIKeys();
                if (typeof loadWebhooks === 'function') loadWebhooks();
                if (typeof loadAnalytics === 'function') loadAnalytics();
                if (typeof loadReferralStats === 'function') loadReferralStats();
                if (typeof loadActiveRentals === 'function') loadActiveRentals();
            }, 100);
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
    localStorage.removeItem('admin_token');
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
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach(t => {
        t.classList.remove('active');
        t.style.background = 'var(--bg-secondary)';
        t.style.color = 'var(--text-secondary)';
    });
    
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const loginHint = document.getElementById('login-hint');
    const registerHint = document.getElementById('register-hint');
    
    if (tab === 'login') {
        if (loginForm) loginForm.classList.remove('hidden');
        if (registerForm) registerForm.classList.add('hidden');
        if (loginHint) loginHint.classList.remove('hidden');
        if (registerHint) registerHint.classList.add('hidden');
        if (tabs[0]) {
            tabs[0].classList.add('active');
            tabs[0].style.background = '#667eea';
            tabs[0].style.color = 'white';
        }
    } else {
        if (loginForm) loginForm.classList.add('hidden');
        if (registerForm) registerForm.classList.remove('hidden');
        if (loginHint) loginHint.classList.add('hidden');
        if (registerHint) registerHint.classList.remove('hidden');
        if (tabs[1]) {
            tabs[1].classList.add('active');
            tabs[1].style.background = '#667eea';
            tabs[1].style.color = 'white';
        }
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
