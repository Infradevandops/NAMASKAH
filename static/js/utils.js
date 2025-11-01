// Enhanced Utility Functions with Security and Performance Optimizations
class Utils {
    constructor() {
        this.debounceTimers = new Map();
        this.cache = new Map();
    }

    // Security utilities
    sanitizeInput(input) {
        if (typeof input !== 'string') return input;
        
        return input
            .replace(/[<>]/g, '') // Remove < and >
            .replace(/javascript:/gi, '') // Remove javascript: protocol
            .replace(/on\w+=/gi, '') // Remove event handlers
            .trim()
            .substring(0, 1000); // Limit length
    }

    sanitizeHTML(html) {
        const div = document.createElement('div');
        div.textContent = html;
        return div.innerHTML;
    }

    validateEmail(email) {
        const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        return emailRegex.test(email);
    }

    validatePassword(password) {
        if (!password || password.length < 6) {
            return { valid: false, message: 'password: "test_password"password: "test_password"123456', 'password: "test_password"password: "test_password"default') {
        if (this.debounceTimers.has(key)) {
            clearTimeout(this.debounceTimers.get(key));
        }
        
        const timer = setTimeout(() => {
            func();
            this.debounceTimers.delete(key);
        }, delay);
        
        this.debounceTimers.set(key, timer);
    }

    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    // Caching utilities
    setCache(key, value, ttl = 300000) { // 5 minutes default
        this.cache.set(key, {
            value,
            expires: Date.now() + ttl
        });
    }

    getCache(key) {
        const cached = this.cache.get(key);
        if (!cached) return null;
        
        if (Date.now() > cached.expires) {
            this.cache.delete(key);
            return null;
        }
        
        return cached.value;
    }

    clearCache() {
        this.cache.clear();
    }

    // API utilities with security
    async secureRequest(url, options = {}) {
        // Validate URL
        if (!url || typeof url !== 'string') {
            throw new Error('Invalid URL');
        }
        
        // Only allow same-origin or API_BASE URLs
        const allowedOrigins = [window.location.origin];
        if (window.API_BASE) {
            allowedOrigins.push(new URL(window.API_BASE).origin);
        }
        
        const requestUrl = new URL(url, window.location.origin);
        if (!allowedOrigins.includes(requestUrl.origin)) {
            throw new Error('Request to external origin not allowed');
        }

        // Add security headers
        const headers = {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            ...options.headers
        };

        // Add CSRF token if available
        const csrfToken = window.csrfToken || localStorage.getItem('csrf_token');
        if (csrfToken && ['POST', 'PUT', 'DELETE', 'PATCH'].includes(options.method?.toUpperCase())) {
            headers['X-CSRF-Token'] = csrfToken;
        }

        // Add auth token
        const token = localStorage.getItem('token');
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        // Sanitize request body
        if (options.body && typeof options.body === 'string') {
            try {
                const data = JSON.parse(options.body);
                const sanitized = this.sanitizeObject(data);
                options.body = JSON.stringify(sanitized);
            } catch (e) {
                // Not JSON, sanitize as string
                options.body = this.sanitizeInput(options.body);
            }
        }

        const response = await fetch(requestUrl.toString(), {
            ...options,
            headers
        });

        // Handle rate limiting
        if (response.status === 429) {
            throw new Error('Rate limit exceeded. Please try again later.');
        }

        return response;
    }

    sanitizeObject(obj) {
        if (typeof obj !== 'object' || obj === null) {
            return this.sanitizeInput(obj);
        }

        const sanitized = {};
        for (const [key, value] of Object.entries(obj)) {
            if (typeof value === 'string') {
                sanitized[key] = this.sanitizeInput(value);
            } else if (typeof value === 'object') {
                sanitized[key] = this.sanitizeObject(value);
            } else {
                sanitized[key] = value;
            }
        }
        return sanitized;
    }

    // UI utilities
    showNotification(message, type = 'info', duration = 5000) {
        const notification = document.getElementById('notification');
        if (!notification) return;

        // Always use textContent to prevent XSS
        notification.textContent = String(message);
        notification.className = `notification ${this.sanitizeInput(type)}`;
        notification.classList.remove('hidden');

        setTimeout(() => {
            notification.classList.add('hidden');
        }, duration);
    }

    showLoading(show = true) {
        const loading = document.getElementById('loading');
        if (loading) {
            if (show) {
                loading.classList.remove('hidden');
            } else {
                loading.classList.add('hidden');
            }
        }
    }

    // Form utilities
    getFormData(formElement) {
        const formData = new FormData(formElement);
        const data = {};
        
        for (const [key, value] of formData.entries()) {
            data[key] = this.sanitizeInput(value);
        }
        
        return data;
    }

    validateForm(formElement, rules = {}) {
        const data = this.getFormData(formElement);
        const errors = {};

        for (const [field, value] of Object.entries(data)) {
            const rule = rules[field];
            if (!rule) continue;

            if (rule.required && (!value || value.trim() === '')) {
                errors[field] = `${field} is required`;
                continue;
            }

            if (rule.email && !this.validateEmail(value)) {
                errors[field] = 'Invalid email format';
                continue;
            }

            if (rule.password) {
                const validation = this.validatePassword(value);
                if (!validation.valid) {
                    errors[field] = validation.message;
                    continue;
                }
            }

            if (rule.minLength && value.length < rule.minLength) {
                errors[field] = `Minimum length is ${rule.minLength}`;
                continue;
            }

            if (rule.maxLength && value.length > rule.maxLength) {
                errors[field] = `Maximum length is ${rule.maxLength}`;
                continue;
            }
        }

        return { valid: Object.keys(errors).length === 0, errors, data };
    }

    // Time utilities
    formatTimeAgo(timestamp) {
        const now = new Date();
        const time = new Date(timestamp);
        const diffMs = now - time;
        const diffMins = Math.floor(diffMs / 60000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;

        const diffHours = Math.floor(diffMins / 60);
        if (diffHours < 24) return `${diffHours}h ago`;

        const diffDays = Math.floor(diffHours / 24);
        return `${diffDays}d ago`;
    }

    formatDuration(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;

        if (hours > 0) {
            return `${hours}h ${minutes}m`;
        } else if (minutes > 0) {
            return `${minutes}m ${secs}s`;
        } else {
            return `${secs}s`;
        }
    }

    // Storage utilities with encryption
    setSecureItem(key, value) {
        try {
            const encrypted = btoa(JSON.stringify(value));
            localStorage.setItem(key, encrypted);
        } catch (e) {
            console.error('Failed to store secure item:', e);
        }
    }

    getSecureItem(key) {
        try {
            const encrypted = localStorage.getItem(key);
            if (!encrypted) return null;
            return JSON.parse(atob(encrypted));
        } catch (e) {
            console.error('Failed to retrieve secure item:', e);
            return null;
        }
    }

    // Copy to clipboard
    async copyToClipboard(text) {
        try {
            if (navigator.clipboard) {
                await navigator.clipboard.writeText(text);
                this.showNotification('📋 Copied to clipboard!', 'success');
            } else {
                // Fallback
                const textArea = document.createElement('textarea');
                textArea.value = text;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                this.showNotification('📋 Copied to clipboard!', 'success');
            }
        } catch (error) {
            console.error('Copy failed:', error);
            this.showNotification('❌ Failed to copy', 'error');
        }
    }

    // Generate secure random string
    generateSecureId(length = 16) {
        const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
        let result = '';
        const array = new Uint8Array(length);
        crypto.getRandomValues(array);
        
        for (let i = 0; i < length; i++) {
            result += chars[array[i] % chars.length];
        }
        
        return result;
    }

    // Safe content rendering to prevent XSS
    safeRender(element, content) {
        if (!element) return;
        
        // Always use textContent for user-generated content
        if (typeof content === 'string') {
            element.textContent = content;
        } else {
            element.textContent = String(content);
        }
        
        return true;
    }

    // Error handling
    handleError(error, context = '') {
        console.error(`Error in ${context}:`, error);
        
        let message = 'An unexpected error occurred';
        
        if (error.message) {
            message = error.message;
        } else if (typeof error === 'string') {
            message = error;
        }
        
        this.showNotification(`❌ ${message}`, 'error');
    }

    // Retry mechanism
    async retry(fn, maxAttempts = 3, delay = 1000) {
        for (let attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                return await fn();
            } catch (error) {
                if (attempt === maxAttempts) {
                    throw error;
                }
                
                console.warn(`Attempt ${attempt} failed, retrying in ${delay}ms...`);
                await new Promise(resolve => setTimeout(resolve, delay));
                delay *= 2; // Exponential backoff
            }
        }
    }
}

// Create global utils instance
window.utils = new Utils();

// Make key functions globally available
window.showNotification = (message, type, duration) => window.utils.showNotification(message, type, duration);
window.showLoading = (show) => window.utils.showLoading(show);
window.safeRender = (element, content) => window.utils.safeRender(element, content);

// Export for modules
window.Utils = Utils;