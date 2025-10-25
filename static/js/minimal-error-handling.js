// Minimal Error Handling for Namaskah SMS
// Focus: Google OAuth graceful fallback and critical button safety

// Global error handler
window.addEventListener('error', (e) => {
    console.error('Global error:', e.error);
    if (typeof showNotification === 'function') {
        showNotification('⚠️ Something went wrong. Please refresh the page.', 'error');
    }
});

// Network connectivity monitoring
window.addEventListener('online', () => {
    if (typeof showNotification === 'function') {
        showNotification('🌐 Connection restored', 'success');
    }
});

window.addEventListener('offline', () => {
    if (typeof showNotification === 'function') {
        showNotification('📡 You are offline. Some features may not work.', 'warning');
    }
});

// Enhanced Google OAuth error handling
window.safeGoogleLogin = async function() {
    try {
        // Check if Google SDK is available
        if (typeof google === 'undefined' || !google.accounts) {
            throw new Error('Google SDK not available');
        }
        
        // Check if Google is properly initialized
        if (!window.googleInitialized) {
            throw new Error('Google not initialized');
        }
        
        // Trigger Google sign-in
        google.accounts.id.prompt();
        
    } catch (error) {
        console.error('Google login error:', error);
        if (typeof showNotification === 'function') {
            showNotification('🔐 Google login unavailable. Please use email/password login.', 'error');
        }
        
        // Hide Google button if it's not working
        const googleBtns = document.querySelectorAll('[onclick*="tryGoogleLogin"], [onclick*="safeGoogleLogin"]');
        googleBtns.forEach(btn => {
            btn.style.display = 'none';
        });
    }
};

// Safe CTA navigation with error handling
window.safeCTAClick = function(action) {
    try {
        switch (action) {
            case 'login':
                window.location.href = '/app';
                break;
            case 'register':
                window.location.href = '/app#register';
                break;
            case 'affiliates':
                window.location.href = '/app#affiliates';
                break;
            default:
                window.location.href = '/app';
        }
    } catch (error) {
        console.error('Navigation error:', error);
        if (typeof showNotification === 'function') {
            showNotification('⚠️ Navigation failed. Please try again.', 'error');
        }
    }
};

// Safe form submission with validation
window.safeFormSubmit = function(formType) {
    try {
        if (formType === 'login') {
            const email = document.getElementById('login-email')?.value;
            const password = document.getElementById('login-password')?.value;
            
            if (!email || !password) {
                if (typeof showNotification === 'function') {
                    showNotification('📝 Please fill all fields', 'error');
                }
                return false;
            }
            
            if (typeof login === 'function') {
                return login();
            }
        } else if (formType === 'register') {
            const email = document.getElementById('register-email')?.value;
            const password = document.getElementById('register-password')?.value;
            
            if (!email || !password) {
                if (typeof showNotification === 'function') {
                    showNotification('📝 Please fill all fields', 'error');
                }
                return false;
            }
            
            if (password.length < 6) {
                if (typeof showNotification === 'function') {
                    showNotification('🔒 Password must be at least 6 characters', 'error');
                }
                return false;
            }
            
            if (typeof register === 'function') {
                return register();
            }
        }
    } catch (error) {
        console.error('Form submission error:', error);
        if (typeof showNotification === 'function') {
            showNotification('❌ Form submission failed. Please try again.', 'error');
        }
        return false;
    }
};

// Enhanced API error handler
window.handleAPIError = function(error, context = '') {
    console.error(`API Error ${context}:`, error);
    
    // Handle different error types
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
        if (typeof showNotification === 'function') {
            showNotification('🌐 Network error. Check your connection.', 'error');
        }
    } else if (error.status === 401) {
        if (typeof showNotification === 'function') {
            showNotification('🔐 Session expired. Please login again.', 'error');
        }
        // Auto-logout on 401
        setTimeout(() => {
            localStorage.removeItem('token');
            window.location.href = '/app';
        }, 2000);
    } else if (error.status === 403) {
        if (typeof showNotification === 'function') {
            showNotification('🚫 Access denied', 'error');
        }
    } else if (error.status === 404) {
        if (typeof showNotification === 'function') {
            showNotification('🔍 Resource not found', 'error');
        }
    } else if (error.status === 422) {
        if (typeof showNotification === 'function') {
            showNotification('📝 Please check your input', 'error');
        }
    } else if (error.status === 429) {
        if (typeof showNotification === 'function') {
            showNotification('⏳ Too many requests. Please wait a moment.', 'error');
        }
    } else if (error.status >= 500) {
        if (typeof showNotification === 'function') {
            showNotification('🔧 Server error. Please try again later.', 'error');
        }
    } else {
        if (typeof showNotification === 'function') {
            showNotification('❌ Something went wrong. Please try again.', 'error');
        }
    }
};

// Enhanced fetch with retry logic
window.fetchWithRetry = async function(url, options = {}, retries = 3) {
    for (let i = 0; i < retries; i++) {
        try {
            const response = await fetch(url, options);
            
            // Retry on server errors
            if (!response.ok && response.status >= 500 && i < retries - 1) {
                await new Promise(resolve => setTimeout(resolve, Math.pow(2, i) * 1000));
                continue;
            }
            
            return response;
        } catch (error) {
            if (i === retries - 1) throw error;
            await new Promise(resolve => setTimeout(resolve, Math.pow(2, i) * 1000));
        }
    }
};

// Safe button state management
window.safeButtonState = function(buttonId, loading = false) {
    try {
        const button = document.getElementById(buttonId);
        if (!button) return;
        
        if (loading) {
            button.disabled = true;
            button.dataset.originalText = button.textContent;
            button.textContent = 'Loading...';
        } else {
            button.disabled = false;
            if (button.dataset.originalText) {
                button.textContent = button.dataset.originalText;
            }
        }
    } catch (error) {
        console.error('Button state error:', error);
    }
};

// Initialize error handling on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    // Add error handling to existing Google buttons
    const googleButtons = document.querySelectorAll('[onclick*="tryGoogleLogin"]');
    googleButtons.forEach(btn => {
        btn.setAttribute('onclick', 'safeGoogleLogin()');
    });
    
    // Add error handling to CTA buttons
    const ctaButtons = document.querySelectorAll('[onclick*="safeCTAClick"]');
    ctaButtons.forEach(btn => {
        // Already using safeCTAClick - no changes needed
    });
    
    // Add form validation to login/register buttons
    const loginBtn = document.getElementById('login-btn');
    if (loginBtn) {
        loginBtn.addEventListener('click', (e) => {
            e.preventDefault();
            safeFormSubmit('login');
        });
    }
    
    const registerBtn = document.getElementById('register-btn');
    if (registerBtn) {
        registerBtn.addEventListener('click', (e) => {
            e.preventDefault();
            safeFormSubmit('register');
        });
    }
    
    console.log('✅ Minimal error handling initialized');
});

// Export functions for global use
window.safeGoogleLogin = window.safeGoogleLogin;
window.safeCTAClick = window.safeCTAClick;
window.safeFormSubmit = window.safeFormSubmit;
window.handleAPIError = window.handleAPIError;
window.fetchWithRetry = window.fetchWithRetry;
window.safeButtonState = window.safeButtonState;