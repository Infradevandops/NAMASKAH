// CSRF Token Management
(function() {
    'use strict';
    
    // Generate CSRF token
    function generateCSRFToken() {
        const array = new Uint8Array(32);
        crypto.getRandomValues(array);
        return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
    }
    
    // Initialize CSRF token
    if (!window.csrfToken) {
        window.csrfToken = generateCSRFToken();
    }
    
    // Add CSRF token to all forms
    document.addEventListener('DOMContentLoaded', function() {
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            if (!form.querySelector('input[name="csrf_token"]')) {
                const csrfInput = document.createElement('input');
                csrfInput.type = 'hidden';
                csrfInput.name = 'csrf_token';
                csrfInput.value = window.csrfToken;
                form.appendChild(csrfInput);
            }
        });
    });
    
    // Override fetch to add CSRF token
    const originalFetch = window.fetch;
    window.fetch = function(url, options = {}) {
        if (options.method && ['POST', 'PUT', 'DELETE', 'PATCH'].includes(options.method.toUpperCase())) {
            options.headers = {
                ...options.headers,
                'X-CSRF-Token': window.csrfToken
            };
        }
        return originalFetch(url, options);
    };
})();