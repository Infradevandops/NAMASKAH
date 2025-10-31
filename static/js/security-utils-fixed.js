/**
 * Security Utilities - Fixed Version
 * Provides secure functions for common operations
 */

window.SecurityUtils = {
    // Validate input against known patterns
    validateInput: function(input, type) {
        if (!input || typeof input !== 'string') return false;
        
        const patterns = {
            service: /^[a-zA-Z0-9_-]+$/,
            email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
            phone: /^\+?[\d\s\-\(\)]+$/,
            alphanumeric: /^[a-zA-Z0-9]+$/
        };
        
        return patterns[type] ? patterns[type].test(input) : false;
    },
    
    // Secure fetch with CSRF protection
    secureFetch: async function(url, options = {}) {
        const token = localStorage.getItem('token');
        
        const secureOptions = {
            ...options,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                ...(token && { 'Authorization': `Bearer ${token}` }),
                ...options.headers
            }
        };
        
        return fetch(url, secureOptions);
    },
    
    // Sanitize text content
    sanitizeText: function(text) {
        if (!text) return '';
        return text.toString().replace(/[<>&"']/g, function(match) {
            const escapeMap = {
                '<': '&lt;',
                '>': '&gt;',
                '&': '&amp;',
                '"': '&quot;',
                "'": '&#x27;'
            };
            return escapeMap[match];
        });
    },
    
    // Create safe DOM element with text content
    createSafeElement: function(tagName, textContent, className) {
        const element = document.createElement(tagName);
        if (textContent) element.textContent = textContent;
        if (className) element.className = className;
        return element;
    },
    
    // Encode URL parameters
    encodeParam: function(param) {
        return encodeURIComponent(param);
    }
};