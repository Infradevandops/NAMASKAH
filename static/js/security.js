// Security Manager - CSRF Protection, Input Sanitization, XSS Prevention
class SecurityManager {
    constructor() {
        this.csrfToken = null;
        this.rateLimiter = new Map();
        this.init();
    }

    init() {
        this.generateCSRFToken();
        this.setupCSRFHeaders();
        this.setupInputSanitization();
        this.setupXSSProtection();
    }

    // CSRF Token Management
    generateCSRFToken() {
        this.csrfToken = this.generateSecureToken();
        localStorage.setItem('csrf_token', this.csrfToken);
    }

    generateSecureToken() {
        const array = new Uint8Array(32);
        crypto.getRandomValues(array);
        return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
    }

    setupCSRFHeaders() {
        const originalFetch = window.fetch;
        window.fetch = (url, options = {}) => {
            if (options.method && ['POST', 'PUT', 'DELETE', 'PATCH'].includes(options.method.toUpperCase())) {
                options.headers = {
                    ...options.headers,
                    'X-CSRF-Token': this.csrfToken
                };
            }
            return originalFetch(url, options);
        };
    }

    // Input Sanitization
    sanitizeInput(input) {
        if (typeof input !== 'string') return input;
        
        return input
            .replace(/[<>]/g, '') // Remove < and >
            .replace(/javascript:/gi, '') // Remove javascript: protocol
            .replace(/on\w+=/gi, '') // Remove event handlers
            .trim();
    }

    sanitizeHTML(html) {
        const div = document.createElement('div');
        div.textContent = html;
        return div.innerHTML;
    }

    setupInputSanitization() {
        document.addEventListener('input', (e) => {
            if (e.target.type === 'text' || e.target.type === 'email' || e.target.tagName === 'TEXTAREA') {
                const sanitized = this.sanitizeInput(e.target.value);
                if (sanitized !== e.target.value) {
                    e.target.value = sanitized;
                }
            }
        });
    }

    // XSS Protection
    setupXSSProtection() {
        // Override innerHTML to sanitize content
        const originalInnerHTML = Object.getOwnPropertyDescriptor(Element.prototype, 'innerHTML');
        
        Object.defineProperty(Element.prototype, 'innerHTML', {
            set: function(value) {
                if (typeof value === 'string') {
                    value = window.securityManager.sanitizeHTML(value);
                }
                originalInnerHTML.set.call(this, value);
            },
            get: originalInnerHTML.get
        });
    }

    // Rate Limiting
    checkRateLimit(endpoint, limit = 10, window = 60000) {
        const now = Date.now();
        const key = endpoint;
        
        if (!this.rateLimiter.has(key)) {
            this.rateLimiter.set(key, []);
        }
        
        const requests = this.rateLimiter.get(key);
        const validRequests = requests.filter(time => now - time < window);
        
        if (validRequests.length >= limit) {
            return false;
        }
        
        validRequests.push(now);
        this.rateLimiter.set(key, validRequests);
        return true;
    }

    // Secure API Request
    async secureRequest(url, options = {}) {
        // Validate URL to prevent SSRF
        if (!this.isValidURL(url)) {
            throw new Error('Invalid or unsafe URL');
        }
        
        // Rate limiting check
        if (!this.checkRateLimit(url)) {
            throw new Error('Rate limit exceeded. Please try again later.');
        }

        // Add security headers
        options.headers = {
            'Content-Type': 'application/json',
            'X-CSRF-Token': this.csrfToken,
            'X-Requested-With': 'XMLHttpRequest',
            ...options.headers
        };

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

        const response = await fetch(url, options);
        
        // Check for security headers in response
        this.validateResponseHeaders(response);
        
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

    validateResponseHeaders(response) {
        const securityHeaders = [
            'X-Content-Type-Options',
            'X-Frame-Options',
            'X-XSS-Protection'
        ];

        securityHeaders.forEach(header => {
            if (!response.headers.get(header)) {
                console.warn(`Missing security header: ${header}`);
            }
        });
    }

    // Content Security Policy
    setupCSP() {
        const meta = document.createElement('meta');
        meta.httpEquiv = 'Content-Security-Policy';
        meta.content = "default-src 'self'; script-src 'self' 'unsafe-inline' https://accounts.google.com; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' wss: https:;";
        document.head.appendChild(meta);
    }

    // Secure Local Storage
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

    // URL Validation to prevent SSRF
    isValidURL(url) {
        try {
            const parsedUrl = new URL(url, window.location.origin);
            
            // Only allow same origin or API_BASE
            const allowedOrigins = [window.location.origin];
            if (window.API_BASE) {
                allowedOrigins.push(new URL(window.API_BASE).origin);
            }
            
            if (!allowedOrigins.includes(parsedUrl.origin)) {
                return false;
            }
            
            // Block private IP ranges
            const hostname = parsedUrl.hostname;
            if (this.isPrivateIP(hostname)) {
                return false;
            }
            
            return true;
        } catch (e) {
            return false;
        }
    }
    
    isPrivateIP(hostname) {
        // Check for private IP ranges
        const privateRanges = [
            /^127\./,
            /^10\./,
            /^172\.(1[6-9]|2[0-9]|3[0-1])\./,
            /^192\.168\./,
            /^169\.254\./,
            /^::1$/,
            /^fc00:/,
            /^fe80:/
        ];
        
        return privateRanges.some(range => range.test(hostname));
    }

    // Token Validation
    validateToken(token) {
        if (!token || typeof token !== 'string') return false;
        
        // Basic JWT structure check
        const parts = token.split('.');
        if (parts.length !== 3) return false;
        
        try {
            const payload = JSON.parse(atob(parts[1]));
            const now = Math.floor(Date.now() / 1000);
            
            // Check expiration
            if (payload.exp && payload.exp < now) {
                return false;
            }
            
            return true;
        } catch (e) {
            return false;
        }
    }

    // Secure Form Submission
    secureFormSubmit(form, callback) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(form);
            const data = {};
            
            for (const [key, value] of formData.entries()) {
                data[key] = this.sanitizeInput(value);
            }
            
            try {
                await callback(data);
            } catch (error) {
                console.error('Secure form submission error:', error);
                if (typeof showNotification === 'function') {
                    showNotification('❌ Security error: ' + error.message, 'error');
                }
            }
        });
    }

    // Clean up sensitive data
    clearSensitiveData() {
        // Clear tokens
        localStorage.removeItem('token');
        localStorage.removeItem('admin_token');
        localStorage.removeItem('csrf_token');
        
        // Clear rate limiter
        this.rateLimiter.clear();
        
        // Generate new CSRF token
        this.generateCSRFToken();
    }
}

// Initialize Security Manager
window.securityManager = new SecurityManager();

// Export for use in other modules
window.SecurityManager = SecurityManager;