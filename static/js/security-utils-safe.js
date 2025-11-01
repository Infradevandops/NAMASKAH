
/**
 * Input Sanitization Utilities
 * Use these functions to sanitize user input
 */

class SecurityUtils {
    /**
     * Escape HTML to prevent XSS
     */
    static escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    /**
     * Sanitize text input
     */
    static sanitizeText(input) {
        if (typeof input !== 'string') return '';
        
        return input
            .replace(/[<>]/g, '')  // Remove < and >
            .replace(/javascript:/gi, '')  // Remove javascript: protocol
            .replace(/on\w+=/gi, '')  // Remove event handlers
            .trim()
            .substring(0, 1000);  // Limit length
    }
    
    /**
     * Validate email format
     */
    static isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email) && email.length <= 254;
    }
    
    /**
     * Validate phone number format
     */
    static isValidPhone(phone) {
        const phoneRegex = /^\+?[1-9]\d{1,14}$/;
        return phoneRegex.test(phone.replace(/[\s()-]/g, ''));
    }
    
    /**
     * Safe DOM insertion
     */
    static safeSetText(element, text) {
        if (element && typeof text === 'string') {
            element.textContent = this.sanitizeText(text);
        }
    }
    
    /**
     * Safe form data collection
     */
    static collectFormData(form) {
        const data = {};
        const formData = new FormData(form);
        
        for (let [key, value] of formData.entries()) {
            data[key] = this.sanitizeText(value);
        }
        
        return data;
    }
}

// Make available globally
window.SecurityUtils = SecurityUtils;
