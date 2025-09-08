// Security utilities for frontend
class SecurityUtils {
    static sanitizeHTML(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }
    
    static escapeHTML(str) {
        return str.replace(/[&<>"']/g, (match) => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;'
        })[match]);
    }
    
    static validateInput(input, type) {
        switch(type) {
            case 'phone':
                return /^\+?[1-9]\d{1,14}$/.test(input.replace(/[\s-]/g, ''));
            case 'email':
                return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(input);
            default:
                return input.length > 0;
        }
    }
}

// CSRF Protection
class CSRFProtection {
    static getToken() {
        return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    }
    
    static addToRequest(options = {}) {
        const token = this.getToken();
        if (token) {
            options.headers = { ...options.headers, 'X-CSRF-Token': token };
        }
        return options;
    }
}

window.SecurityUtils = SecurityUtils;
window.CSRFProtection = CSRFProtection;