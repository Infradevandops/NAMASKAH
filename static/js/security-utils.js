/**
 * Security Utilities Module - Critical Security Fixes
 * Addresses: XSS, Code Injection, CSRF, Input Sanitization
 */

class SecurityUtils {
    constructor() {
        this.csrfToken = this.getCSRFToken();
        this.trustedDomains = ['localhost', '127.0.0.1', window.location.hostname];
    }

    // XSS Protection - Sanitize HTML content
    sanitizeHTML(input) {
        if (typeof input !== 'string') return '';
        
        const div = document.createElement('div');
        div.textContent = input;
        return div.innerHTML;
    }

    // Safe DOM manipulation - prevents XSS
    safeSetHTML(element, content) {
        if (!element) return;
        
        // Clear existing content
        element.textContent = '';
        
        // Create safe text node
        const textNode = document.createTextNode(content);
        element.appendChild(textNode);
    }

    // Safe innerHTML with sanitization
    safeSetInnerHTML(element, htmlContent) {
        if (!element) return;
        
        // Basic HTML sanitization
        const sanitized = htmlContent
            .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
            .replace(/javascript:/gi, '')
            .replace(/on\w+\s*=/gi, '')
            .replace(/data:/gi, '');
        
        element.innerHTML = sanitized;
    }

    // Validate and sanitize service names
    sanitizeServiceName(serviceName) {
        if (typeof serviceName !== 'string') return '';
        
        return serviceName
            .replace(/[<>\"'&]/g, '')
            .replace(/[^\w\s-]/g, '')
            .trim()
            .toLowerCase();
    }

    // CSRF Token management
    getCSRFToken() {
        const token = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') ||
                     document.querySelector('input[name="csrf_token"]')?.value ||
                     localStorage.getItem('csrf_token');
        return token;
    }

    // Secure fetch wrapper with CSRF protection
    async secureFetch(url, options = {}) {
        // Validate URL
        if (!this.isValidURL(url)) {
            throw new Error('Invalid URL');
        }

        const secureOptions = {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                ...options.headers
            }
        };

        // Add CSRF token for state-changing requests
        if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(options.method?.toUpperCase())) {
            if (this.csrfToken) {
                secureOptions.headers['X-CSRF-Token'] = this.csrfToken;
            }
        }

        // Add auth token if available
        const authToken = localStorage.getItem('token');
        if (authToken) {
            secureOptions.headers['Authorization'] = `Bearer ${authToken}`;
        }

        return fetch(url, secureOptions);
    }

    // URL validation
    isValidURL(url) {
        try {
            const urlObj = new URL(url, window.location.origin);
            return this.trustedDomains.includes(urlObj.hostname) || 
                   urlObj.hostname.endsWith('.namaskah.app');
        } catch {
            return false;
        }
    }

    // Input validation for forms
    validateInput(input, type = 'text') {
        if (typeof input !== 'string') return false;

        const validators = {
            email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
            phone: /^\+?[\d\s-()]+$/,
            service: /^[a-zA-Z0-9\s-_]+$/,
            alphanumeric: /^[a-zA-Z0-9]+$/
        };

        return validators[type] ? validators[type].test(input) : input.length > 0;
    }

    // Safe event handler attachment
    safeAddEventListener(element, event, handler) {
        if (!element || typeof handler !== 'function') return;
        
        element.addEventListener(event, (e) => {
            try {
                handler(e);
            } catch (error) {
                console.error('Event handler error:', error);
            }
        });
    }

    // Rate limiting for API calls
    createRateLimiter(maxCalls = 10, windowMs = 60000) {
        const calls = [];
        
        return function(fn) {
            const now = Date.now();
            const windowStart = now - windowMs;
            
            // Remove old calls
            while (calls.length > 0 && calls[0] < windowStart) {
                calls.shift();
            }
            
            if (calls.length >= maxCalls) {
                throw new Error('Rate limit exceeded');
            }
            
            calls.push(now);
            return fn();
        };
    }
}

// Create global security instance
window.SecurityUtils = new SecurityUtils();

// Safe service selection function
window.safeSelectService = function(serviceName) {
    const sanitizedService = window.SecurityUtils.sanitizeServiceName(serviceName);
    if (!sanitizedService) {
        console.error('Invalid service name');
        return;
    }
    
    // Use the original selectService function with sanitized input
    if (typeof window.selectService === 'function') {
        window.selectService(sanitizedService);
    }
};

// Safe notification function
window.safeShowNotification = function(message, type = 'info') {
    const sanitizedMessage = window.SecurityUtils.sanitizeHTML(message);
    if (typeof window.showNotification === 'function') {
        window.showNotification(sanitizedMessage, type);
    }
};

console.log('✅ Security utilities loaded - XSS and injection protection active');