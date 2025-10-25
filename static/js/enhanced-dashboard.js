/**
 * Enhanced Dashboard JavaScript
 * Handles dashboard functionality, real-time updates, and user interactions
 */

class EnhancedDashboard {
    constructor() {
        this.user = null;
        this.activeVerifications = [];
        this.websocket = null;
        this.refreshInterval = null;
        this.init();
    }

    async init() {
        await this.loadUser();
        this.setupEventListeners();
        this.loadActiveVerifications();
        this.loadStats();
        this.setupWebSocket();
        this.startAutoRefresh();
    }

    async loadUser() {
        try {
            const token = localStorage.getItem('token');
            if (!token) {
                window.location.href = '/login';
                return;
            }

            const response = await fetch('/auth/me', {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (!response.ok) {
                throw new Error('Authentication failed');
            }

            this.user = await response.json();
            this.updateUserDisplay();
        } catch (error) {
            console.error('Failed to load user:', error);
            localStorage.removeItem('token');
            window.location.href = '/login';
        }
    }

    updateUserDisplay() {
        const creditsEl = document.getElementById('user-credits');
        if (creditsEl && this.user) {
            creditsEl.textContent = `N${this.user.credits.toFixed(2)}`;
        }
    }

    setupEventListeners() {
        // Logout button
        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', this.logout.bind(this));
        }

        // Refresh verifications button
        const refreshBtn = document.getElementById('refresh-verifications');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', this.loadActiveVerifications.bind(this));
        }

        // Handle payment verification from URL
        const urlParams = new URLSearchParams(window.location.search);
        const reference = urlParams.get('reference');
        if (reference) {
            this.verifyPayment(reference);
        }
    }

    async loadActiveVerifications() {
        try {
            const token = localStorage.getItem('token');
            const response = await fetch('/verifications/active', {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            const data = await response.json();
            this.activeVerifications = data.verifications;
            this.displayActiveVerifications();
        } catch (error) {
            console.error('Failed to load verifications:', error);
            this.displayVerificationError();
        }
    }

    displayActiveVerifications() {
        const container = document.getElementById('active-verifications');
        if (!container) return;

        if (this.activeVerifications.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <p>No active verifications</p>
                    <p class="text-muted">Create a verification to get started</p>
                </div>
            `;
            return;
        }

        container.innerHTML = this.activeVerifications.map(verification => `
            <div class="verification-item" data-id="${verification.id}">
                <div class="verification-info">
                    <div class="verification-service">${this.formatServiceName(verification.service_name)}</div>
                    <div class="verification-phone">${verification.phone_number || 'Pending...'}</div>
                </div>
                <div class="verification-status status-${verification.status}">
                    ${verification.status}
                </div>
                <div class="verification-cost">N${verification.cost.toFixed(2)}</div>
                <div class="verification-actions">
                    <button class="btn-secondary btn-sm" onclick="window.open('/verify/${verification.id}', '_blank')">
                        View
                    </button>
                    ${verification.status === 'pending' ? `
                        <button class="btn-secondary btn-sm" onclick="dashboard.cancelVerification('${verification.id}')">
                            Cancel
                        </button>
                    ` : ''}
                </div>
            </div>
        `).join('');
    }

    displayVerificationError() {
        const container = document.getElementById('active-verifications');
        if (container) {
            container.innerHTML = `
                <div class="error-state">
                    <p>Failed to load verifications</p>
                    <button class="btn-secondary" onclick="dashboard.loadActiveVerifications()">
                        Retry
                    </button>
                </div>
            `;
        }
    }

    async loadStats() {
        try {
            const token = localStorage.getItem('token');
            const response = await fetch('/analytics/dashboard', {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            const stats = await response.json();
            this.displayStats(stats);
        } catch (error) {
            console.error('Failed to load stats:', error);
        }
    }

    displayStats(stats) {
        const totalEl = document.getElementById('total-verifications');
        const successRateEl = document.getElementById('success-rate');
        const totalSpentEl = document.getElementById('total-spent');

        if (totalEl) totalEl.textContent = stats.total_verifications || 0;
        if (successRateEl) successRateEl.textContent = `${stats.success_rate || 0}%`;
        if (totalSpentEl) totalSpentEl.textContent = `N${(stats.total_spent || 0).toFixed(2)}`;
    }

    setupWebSocket() {
        if (!this.user) return;

        try {
            const token = localStorage.getItem('token');
            const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${wsProtocol}//${window.location.host}/ws?token=${token}`;
            
            this.websocket = new WebSocket(wsUrl);

            this.websocket.onopen = () => {
                console.log('WebSocket connected');
                this.startHeartbeat();
            };

            this.websocket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            };

            this.websocket.onclose = () => {
                console.log('WebSocket disconnected');
                this.stopHeartbeat();
                // Attempt to reconnect after 5 seconds
                setTimeout(() => this.setupWebSocket(), 5000);
            };

            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
        } catch (error) {
            console.error('WebSocket setup failed:', error);
        }
    }

    startHeartbeat() {
        this.heartbeatInterval = setInterval(() => {
            if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
                this.websocket.send(JSON.stringify({ type: 'ping' }));
            }
        }, 30000); // Ping every 30 seconds
    }

    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'pong':
                // Heartbeat response
                break;
            
            case 'verification_status':
                this.handleVerificationUpdate(data.payload);
                break;
            
            case 'sms_received':
                this.handleSMSReceived(data.payload);
                break;
            
            case 'balance_update':
                this.handleBalanceUpdate(data.payload);
                break;
            
            default:
                console.log('Unknown WebSocket message:', data);
        }
    }

    handleVerificationUpdate(payload) {
        // Update verification in the list
        const verificationEl = document.querySelector(`[data-id="${payload.verification_id}"]`);
        if (verificationEl) {
            const statusEl = verificationEl.querySelector('.verification-status');
            if (statusEl) {
                statusEl.textContent = payload.status;
                statusEl.className = `verification-status status-${payload.status}`;
            }
        }

        // Show notification
        if (payload.status === 'completed') {
            this.showNotification('Verification completed!', 'success');
            this.loadActiveVerifications(); // Refresh the list
        }
    }

    handleSMSReceived(payload) {
        this.showNotification(`SMS received for ${payload.phone_number}`, 'success');
    }

    handleBalanceUpdate(payload) {
        if (this.user) {
            this.user.credits = payload.new_balance;
            this.updateUserDisplay();
        }
    }

    startAutoRefresh() {
        // Refresh verifications every 30 seconds
        this.refreshInterval = setInterval(() => {
            this.loadActiveVerifications();
        }, 30000);
    }

    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    async cancelVerification(verificationId) {
        if (!confirm('Are you sure you want to cancel this verification? You will be refunded.')) {
            return;
        }

        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`/verify/${verificationId}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });

            const result = await response.json();

            if (response.ok) {
                this.showNotification(result.message, 'success');
                this.loadActiveVerifications();
                this.loadUser(); // Refresh balance
            } else {
                throw new Error(result.detail || 'Cancellation failed');
            }
        } catch (error) {
            console.error('Cancellation failed:', error);
            this.showNotification(error.message, 'error');
        }
    }

    async verifyPayment(reference) {
        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`/wallet/paystack/verify/${reference}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            const result = await response.json();

            if (result.status === 'success') {
                this.showNotification(`Payment successful! Credited N${result.amount}`, 'success');
                this.loadUser(); // Refresh balance
            } else if (result.status === 'already_credited') {
                this.showNotification('Payment already processed', 'warning');
            } else {
                this.showNotification('Payment verification failed', 'error');
            }

            // Clean up URL
            const url = new URL(window.location);
            url.searchParams.delete('reference');
            window.history.replaceState({}, document.title, url);
        } catch (error) {
            console.error('Payment verification failed:', error);
            this.showNotification('Payment verification failed', 'error');
        }
    }

    showNotification(message, type = 'info') {
        const container = document.getElementById('notification-container');
        if (!container) return;

        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;

        container.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }

    formatServiceName(service) {
        return service.charAt(0).toUpperCase() + service.slice(1).replace(/[-_]/g, ' ');
    }

    logout() {
        localStorage.removeItem('token');
        localStorage.removeItem('admin_token');
        this.stopAutoRefresh();
        if (this.websocket) {
            this.websocket.close();
        }
        window.location.href = '/login';
    }

    // Cleanup when page unloads
    destroy() {
        this.stopAutoRefresh();
        this.stopHeartbeat();
        if (this.websocket) {
            this.websocket.close();
        }
    }
}

// Global notification function
window.showNotification = function(message, type = 'info') {
    if (window.dashboard) {
        window.dashboard.showNotification(message, type);
    }
};

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new EnhancedDashboard();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.dashboard) {
        window.dashboard.destroy();
    }
});

// Additional utility functions for the dashboard

// Format currency
function formatCurrency(amount) {
    return `N${amount.toFixed(2)}`;
}

// Format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
}

// Copy to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification('Copied to clipboard', 'success');
    }).catch(() => {
        showNotification('Failed to copy', 'error');
    });
}

// Export functions for global use
window.formatCurrency = formatCurrency;
window.formatDate = formatDate;
window.copyToClipboard = copyToClipboard;