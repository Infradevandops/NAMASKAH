/**
 * Secure Verification Module - Fixes Critical Security Issues
 * Replaces unsafe verification.js functionality
 */

class SecureVerification {
    constructor() {
        this.rateLimiter = window.SecurityUtils?.createRateLimiter(5, 60000);
        this.activeVerifications = new Map();
        this.pollingIntervals = new Map();
    }

    // Secure verification creation
    async createVerification(serviceData) {
        try {
            // Rate limiting
            if (this.rateLimiter) {
                this.rateLimiter(() => {});
            }

            // Validate input
            if (!serviceData?.service || !window.SecurityUtils?.validateInput(serviceData.service, 'service')) {
                throw new Error('Invalid service name');
            }

            const sanitizedData = {
                service: window.SecurityUtils.sanitizeServiceName(serviceData.service),
                capability: ['sms', 'voice'].includes(serviceData.capability) ? serviceData.capability : 'sms',
                country: serviceData.country || 'US'
            };

            const response = await window.SecurityUtils.secureFetch('/verify/create', {
                method: 'POST',
                body: JSON.stringify(sanitizedData)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Verification creation failed');
            }

            const verification = await response.json();
            this.activeVerifications.set(verification.id, verification);
            
            // Start secure polling
            this.startSecurePolling(verification.id);
            
            return verification;

        } catch (error) {
            console.error('Verification creation error:', error);
            this.showSecureNotification(error.message, 'error');
            throw error;
        }
    }

    // Secure message polling
    startSecurePolling(verificationId) {
        if (this.pollingIntervals.has(verificationId)) {
            clearInterval(this.pollingIntervals.get(verificationId));
        }

        const interval = setInterval(async () => {
            try {
                await this.checkMessages(verificationId);
            } catch (error) {
                console.error('Polling error:', error);
                this.stopPolling(verificationId);
            }
        }, 3000);

        this.pollingIntervals.set(verificationId, interval);
        
        // Auto-stop after 10 minutes
        setTimeout(() => this.stopPolling(verificationId), 600000);
    }

    // Secure message checking
    async checkMessages(verificationId) {
        if (!verificationId || typeof verificationId !== 'string') {
            throw new Error('Invalid verification ID');
        }

        const response = await window.SecurityUtils.secureFetch(`/verify/${encodeURIComponent(verificationId)}/messages`);
        
        if (!response.ok) {
            throw new Error('Failed to fetch messages');
        }

        const data = await response.json();
        
        if (data.messages && data.messages.length > 0) {
            this.displaySecureMessages(verificationId, data.messages);
            this.stopPolling(verificationId);
        }

        return data;
    }

    // Secure message display
    displaySecureMessages(verificationId, messages) {
        const container = document.getElementById('messages-container');
        if (!container) return;

        // Clear existing content safely
        container.textContent = '';

        messages.forEach(message => {
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message-item';
            
            // Sanitize message content
            const safeContent = window.SecurityUtils.sanitizeHTML(message.content || '');
            const safeTimestamp = window.SecurityUtils.sanitizeHTML(message.timestamp || '');
            
            messageDiv.innerHTML = `
                <div class="message-content">${safeContent}</div>
                <div class="message-timestamp">${safeTimestamp}</div>
            `;
            
            container.appendChild(messageDiv);
        });

        this.showSecureNotification('✅ Messages received!', 'success');
    }

    // Stop polling
    stopPolling(verificationId) {
        if (this.pollingIntervals.has(verificationId)) {
            clearInterval(this.pollingIntervals.get(verificationId));
            this.pollingIntervals.delete(verificationId);
        }
    }

    // Secure notification display
    showSecureNotification(message, type = 'info') {
        const safeMessage = window.SecurityUtils?.sanitizeHTML(message) || message;
        
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = safeMessage;
        
        // Add to page
        const container = document.getElementById('notifications') || document.body;
        container.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }

    // Secure form handling
    setupSecureForm() {
        const form = document.getElementById('verification-form');
        if (!form) return;

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(form);
            const serviceData = {
                service: formData.get('service'),
                capability: formData.get('capability'),
                country: formData.get('country')
            };

            try {
                await this.createVerification(serviceData);
            } catch (error) {
                console.error('Form submission error:', error);
            }
        });
    }

    // Cleanup on page unload
    cleanup() {
        this.pollingIntervals.forEach((interval, id) => {
            clearInterval(interval);
        });
        this.pollingIntervals.clear();
        this.activeVerifications.clear();
    }
}

// Initialize secure verification
window.SecureVerification = new SecureVerification();

// Setup on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    window.SecureVerification.setupSecureForm();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    window.SecureVerification.cleanup();
});

console.log('✅ Secure verification module loaded - CSRF and XSS protection active');