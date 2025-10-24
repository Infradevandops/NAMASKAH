// Enhanced Verification System with Real-time Features and Bulk Operations
class EnhancedVerification {
    constructor() {
        this.activeVerifications = new Map();
        this.autoRefreshEnabled = true;
        this.refreshInterval = null;
        this.bulkOperations = [];
        this.init();
    }

    init() {
        this.setupAutoRefresh();
        this.loadActiveVerifications();
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Auto-refresh toggle
        const autoRefreshToggle = document.getElementById('auto-refresh-toggle');
        if (autoRefreshToggle) {
            autoRefreshToggle.addEventListener('change', (e) => {
                this.autoRefreshEnabled = e.target.checked;
                if (this.autoRefreshEnabled) {
                    this.setupAutoRefresh();
                } else {
                    this.stopAutoRefresh();
                }
            });
        }
    }

    setupAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }

        if (this.autoRefreshEnabled && localStorage.getItem('token')) {
            this.refreshInterval = setInterval(() => {
                if (!window.wsManager?.isConnected && localStorage.getItem('token')) {
                    this.refreshActiveVerifications();
                }
            }, 10000); // 10 seconds
        }
    }

    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    async loadActiveVerifications() {
        // Don't make requests if no token
        const token = localStorage.getItem('token');
        if (!token) {
            return;
        }
        
        try {
            const response = await window.securityManager.secureRequest('/verifications/active', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.displayActiveVerifications(data.verifications || []);
            } else if (response.status === 401) {
                // Stop retrying on auth errors
                console.log('Auth error - stopping verification requests');
                this.stopAutoRefresh();
            }
        } catch (error) {
            console.error('Failed to load active verifications:', error);
        }
    }

    async refreshActiveVerifications() {
        await this.loadActiveVerifications();
    }

    displayActiveVerifications(verifications) {
        const container = document.getElementById('active-verifications-container');
        const card = document.getElementById('active-verifications-card');
        
        if (!container || !card) return;

        if (verifications.length === 0) {
            card.style.display = 'none';
            return;
        }

        card.style.display = 'block';
        
        container.innerHTML = verifications.map(verification => {
            this.activeVerifications.set(verification.id, verification);
            
            // Subscribe to WebSocket updates
            if (window.wsManager?.isConnected) {
                window.wsManager.subscribeToVerification(verification.id, (data) => {
                    this.handleRealtimeUpdate(verification.id, data);
                });
            }

            return this.createVerificationCard(verification);
        }).join('');
    }

    createVerificationCard(verification) {
        const statusClass = this.getStatusClass(verification.status);
        const timeAgo = this.getTimeAgo(verification.created_at);
        
        return `
            <div class="verification-card" data-verification-id="${verification.id}">
                <div class="verification-header">
                    <div class="service-info">
                        <span class="service-name">${verification.service_name}</span>
                        <span class="phone-number">${verification.phone_number}</span>
                    </div>
                    <div class="status-info">
                        <span class="status ${statusClass}">${verification.status}</span>
                        <span class="time-ago">${timeAgo}</span>
                    </div>
                </div>
                <div class="verification-actions">
                    <button onclick="enhancedVerification.checkMessages('${verification.id}')" class="btn-small">
                        📨 Check
                    </button>
                    <button onclick="enhancedVerification.viewDetails('${verification.id}')" class="btn-small">
                        👁️ View
                    </button>
                    <button onclick="enhancedVerification.cancelVerification('${verification.id}')" class="btn-small btn-danger">
                        ❌ Cancel
                    </button>
                </div>
                <div class="verification-progress">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${this.getProgressPercentage(verification)}%"></div>
                    </div>
                </div>
            </div>
        `;
    }

    getStatusClass(status) {
        const statusMap = {
            'pending': 'pending',
            'active': 'active',
            'completed': 'success',
            'failed': 'error',
            'cancelled': 'cancelled'
        };
        return statusMap[status] || 'pending';
    }

    getTimeAgo(timestamp) {
        const now = new Date();
        const created = new Date(timestamp);
        const diffMs = now - created;
        const diffMins = Math.floor(diffMs / 60000);
        
        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        
        const diffHours = Math.floor(diffMins / 60);
        if (diffHours < 24) return `${diffHours}h ago`;
        
        const diffDays = Math.floor(diffHours / 24);
        return `${diffDays}d ago`;
    }

    getProgressPercentage(verification) {
        const statusProgress = {
            'pending': 25,
            'active': 50,
            'completed': 100,
            'failed': 100,
            'cancelled': 100
        };
        return statusProgress[verification.status] || 0;
    }

    handleRealtimeUpdate(verificationId, data) {
        const verification = this.activeVerifications.get(verificationId);
        if (!verification) return;

        // Update verification data
        Object.assign(verification, data);

        // Update UI
        this.updateVerificationInList(verificationId, data);
    }

    updateVerificationInList(verificationId, updates) {
        const card = document.querySelector(`[data-verification-id="${verificationId}"]`);
        if (!card) return;

        // Update status
        if (updates.status) {
            const statusElement = card.querySelector('.status');
            if (statusElement) {
                statusElement.textContent = updates.status;
                statusElement.className = `status ${this.getStatusClass(updates.status)}`;
            }

            // Update progress bar
            const progressFill = card.querySelector('.progress-fill');
            if (progressFill) {
                progressFill.style.width = `${this.getProgressPercentage({status: updates.status})}%`;
            }
        }

        // Update time
        const timeElement = card.querySelector('.time-ago');
        if (timeElement && updates.created_at) {
            timeElement.textContent = this.getTimeAgo(updates.created_at);
        }
    }

    async checkMessages(verificationId) {
        try {
            const response = await window.securityManager.secureRequest(`/verify/${verificationId}/messages`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.displayMessages(data.messages || []);
                
                if (data.messages && data.messages.length > 0) {
                    showNotification('📨 Messages received!', 'success');
                } else {
                    showNotification('📭 No messages yet', 'info');
                }
            } else {
                const error = await response.json();
                showNotification('❌ ' + (error.detail || 'Failed to check messages'), 'error');
            }
        } catch (error) {
            console.error('Check messages error:', error);
            showNotification('❌ Network error', 'error');
        }
    }

    displayMessages(messages) {
        const messagesSection = document.getElementById('messages-section');
        const messagesList = document.getElementById('messages-list');
        const noMessages = document.getElementById('no-messages');
        
        if (!messagesSection || !messagesList) return;

        messagesSection.classList.remove('hidden');

        if (messages.length === 0) {
            messagesList.innerHTML = '';
            noMessages.style.display = 'block';
            return;
        }

        noMessages.style.display = 'none';
        messagesList.innerHTML = messages.map(msg => `
            <div class="message-item">
                <div class="message-header">
                    <strong>${msg.sender || 'Unknown'}</strong>
                    <span class="message-time">${new Date(msg.timestamp).toLocaleString()}</span>
                </div>
                <div class="message-content">${window.securityManager?.sanitizeHTML(msg.message) || msg.message}</div>
            </div>
        `).join('');
    }

    async viewDetails(verificationId) {
        try {
            const response = await window.securityManager.secureRequest(`/verify/${verificationId}`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.showVerificationDetails(data);
            } else {
                const error = await response.json();
                showNotification('❌ ' + (error.detail || 'Failed to load details'), 'error');
            }
        } catch (error) {
            console.error('View details error:', error);
            showNotification('❌ Network error', 'error');
        }
    }

    showVerificationDetails(verification) {
        const detailsSection = document.getElementById('verification-details');
        if (!detailsSection) return;

        // Store verification ID for WebSocket updates
        detailsSection.dataset.verificationId = verification.id;

        // Update details
        document.getElementById('phone-number').textContent = verification.phone_number;
        document.getElementById('service-name').textContent = verification.service_name;
        document.getElementById('status').textContent = verification.status;
        document.getElementById('status').className = `badge ${this.getStatusClass(verification.status)}`;

        // Show details section
        detailsSection.classList.remove('hidden');

        // Subscribe to real-time updates
        if (window.wsManager?.isConnected) {
            window.wsManager.subscribeToVerification(verification.id, (data) => {
                this.handleVerificationDetailsUpdate(data);
            });
        }

        // Auto-check for messages
        this.checkMessages(verification.id);
    }

    handleVerificationDetailsUpdate(data) {
        if (data.type === 'sms_received') {
            // Message already handled by WebSocket manager
            return;
        }

        if (data.type === 'verification_update') {
            // Update status
            const statusElement = document.getElementById('status');
            if (statusElement && data.status) {
                statusElement.textContent = data.status;
                statusElement.className = `badge ${this.getStatusClass(data.status)}`;
            }
        }
    }

    async cancelVerification(verificationId) {
        if (!confirm('Are you sure you want to cancel this verification?')) {
            return;
        }

        try {
            const response = await window.securityManager.secureRequest(`/verify/${verificationId}/cancel`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });

            if (response.ok) {
                showNotification('✅ Verification cancelled', 'success');
                this.refreshActiveVerifications();
            } else {
                const error = await response.json();
                showNotification('❌ ' + (error.detail || 'Failed to cancel'), 'error');
            }
        } catch (error) {
            console.error('Cancel verification error:', error);
            showNotification('❌ Network error', 'error');
        }
    }

    // Bulk Operations
    showBulkModal() {
        const modal = document.getElementById('bulk-verify-modal');
        if (modal) {
            modal.style.display = 'flex';
        } else {
            this.createBulkModal();
        }
    }

    createBulkModal() {
        const modal = document.createElement('div');
        modal.id = 'bulk-verify-modal';
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content" style="max-width: 600px;">
                <span class="close" onclick="enhancedVerification.closeBulkModal()">&times;</span>
                <h2>🚀 Bulk Verification</h2>
                <p style="color: #6b7280; margin-bottom: 20px;">Create multiple verifications at once</p>
                
                <div style="margin-bottom: 20px;">
                    <label style="font-weight: bold; display: block; margin-bottom: 10px;">Services (one per line)</label>
                    <textarea id="bulk-services" rows="5" placeholder="telegram&#10;whatsapp&#10;instagram&#10;discord" 
                              style="width: 100%; padding: 12px; border: 2px solid #e5e7eb; border-radius: 8px;"></textarea>
                    <p style="font-size: 12px; color: #6b7280; margin-top: 5px;">Enter one service name per line</p>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <label style="font-weight: bold; display: block; margin-bottom: 10px;">Capability</label>
                    <select id="bulk-capability" style="width: 100%; padding: 12px; border: 2px solid #e5e7eb; border-radius: 8px;">
                        <option value="sms">SMS</option>
                        <option value="voice">Voice</option>
                    </select>
                </div>
                
                <div style="background: #f0fdf4; border: 2px solid #10b981; border-radius: 8px; padding: 15px; margin-bottom: 20px;">
                    <h4 style="margin: 0 0 10px 0; color: #059669;">💡 Bulk Pricing</h4>
                    <p style="margin: 0; color: #059669;">5+ verifications: 10% discount | 10+ verifications: 20% discount</p>
                </div>
                
                <div style="display: flex; gap: 10px;">
                    <button onclick="enhancedVerification.createBulkVerifications()" style="flex: 1; background: #10b981;">
                        Create All
                    </button>
                    <button onclick="enhancedVerification.closeBulkModal()" class="btn-danger" style="flex: 1;">
                        Cancel
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        modal.style.display = 'flex';
    }

    closeBulkModal() {
        const modal = document.getElementById('bulk-verify-modal');
        if (modal) {
            modal.style.display = 'none';
        }
    }

    async createBulkVerifications() {
        const servicesText = document.getElementById('bulk-services').value.trim();
        const capability = document.getElementById('bulk-capability').value;
        
        if (!servicesText) {
            showNotification('❌ Please enter at least one service', 'error');
            return;
        }

        const services = servicesText.split('\n').map(s => s.trim()).filter(s => s);
        
        if (services.length === 0) {
            showNotification('❌ Please enter valid service names', 'error');
            return;
        }

        showLoading(true);
        
        try {
            const results = [];
            
            for (const service of services) {
                try {
                    const response = await window.securityManager.secureRequest('/verify/create', {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${localStorage.getItem('token')}`
                        },
                        body: JSON.stringify({
                            service_name: service,
                            capability: capability
                        })
                    });

                    if (response.ok) {
                        const data = await response.json();
                        results.push({ service, success: true, data });
                    } else {
                        const error = await response.json();
                        results.push({ service, success: false, error: error.detail });
                    }
                } catch (error) {
                    results.push({ service, success: false, error: error.message });
                }
                
                // Small delay between requests
                await new Promise(resolve => setTimeout(resolve, 500));
            }
            
            showLoading(false);
            this.closeBulkModal();
            this.showBulkResults(results);
            this.refreshActiveVerifications();
            
        } catch (error) {
            showLoading(false);
            console.error('Bulk verification error:', error);
            showNotification('❌ Bulk operation failed', 'error');
        }
    }

    showBulkResults(results) {
        const successful = results.filter(r => r.success);
        const failed = results.filter(r => !r.success);
        
        let message = `✅ ${successful.length} verifications created successfully`;
        if (failed.length > 0) {
            message += `\n❌ ${failed.length} failed`;
        }
        
        showNotification(message, successful.length > 0 ? 'success' : 'error');
        
        // Show detailed results
        console.log('Bulk verification results:', results);
    }

    copyPhone(phoneNumber) {
        if (navigator.clipboard) {
            navigator.clipboard.writeText(phoneNumber).then(() => {
                showNotification('📋 Phone number copied!', 'success');
            });
        } else {
            // Fallback
            const textArea = document.createElement('textarea');
            textArea.value = phoneNumber;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            showNotification('📋 Phone number copied!', 'success');
        }
    }
}

// Initialize Enhanced Verification
document.addEventListener('DOMContentLoaded', () => {
    window.enhancedVerification = new EnhancedVerification();
});

// Export for use in other modules
window.EnhancedVerification = EnhancedVerification;