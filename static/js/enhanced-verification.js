// Enhanced Verification Module for Text and Voice Verification
class VerificationManager {
    constructor() {
        this.currentVerificationId = null;
        this.autoRefreshInterval = null;
        this.currentCapability = 'sms';
        this.verificationStartTime = null;
        this.maxRetries = 3;
        this.currentRetryCount = 0;
    }

    // Initialize the verification manager
    init() {
        this.setupEventListeners();
        this.updateEstimatedCost();
        this.updateCapabilitySelection();
    }

    // Setup event listeners
    setupEventListeners() {
        const serviceSelect = document.getElementById('service-select');
        if (serviceSelect) {
            serviceSelect.addEventListener('change', () => this.updateEstimatedCost());
        }

        document.querySelectorAll('input[name="capability"]').forEach(radio => {
            radio.addEventListener('change', () => this.updateCapabilitySelection());
        });
    }

    // Update estimated cost based on service and capability
    updateEstimatedCost() {
        const serviceSelect = document.getElementById('service-select');
        const capabilityRadio = document.querySelector('input[name="capability"]:checked');
        
        if (!serviceSelect || !capabilityRadio) return;
        
        const serviceOption = serviceSelect.options[serviceSelect.selectedIndex];
        const basePrice = parseFloat(serviceOption.text.match(/\$([0-9.]+)/)?.[1] || '1.00');
        const isVoice = capabilityRadio.value === 'voice';
        const totalPrice = isVoice ? basePrice + 0.30 : basePrice;
        
        const costElement = document.getElementById('estimated-cost');
        if (costElement) {
            costElement.textContent = `$${totalPrice.toFixed(2)}`;
        }
    }

    // Update capability selection styling
    updateCapabilitySelection() {
        document.querySelectorAll('.capability-option').forEach(option => {
            const radio = option.querySelector('input[type="radio"]');
            if (radio && radio.checked) {
                option.style.borderColor = '#10b981';
                option.style.background = '#064e3b';
            } else {
                option.style.borderColor = '#334155';
                option.style.background = '#1a2942';
            }
        });
        this.updateEstimatedCost();
    }

    // Create new verification
    async createVerification() {
        const token = localStorage.getItem('token');
        if (!token) {
            this.showNotification('Please login first', 'error');
            return;
        }

        const serviceName = document.getElementById('service-select')?.value;
        const capability = document.querySelector('input[name="capability"]:checked')?.value || 'sms';
        const country = document.getElementById('country-select')?.value || 'US';

        if (!serviceName) {
            this.showNotification('Please select a service', 'error');
            return;
        }

        this.currentCapability = capability;
        this.verificationStartTime = Date.now();
        this.currentRetryCount = 0;

        const createBtnText = document.getElementById('create-btn-text');
        const createLoading = document.getElementById('create-loading');

        if (createBtnText) createBtnText.style.display = 'none';
        if (createLoading) createLoading.style.display = 'inline';

        try {
            const response = await fetch('/verify/create', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    service_name: serviceName,
                    capability: capability,
                    country: country
                })
            });

            const data = await response.json();

            if (response.ok) {
                this.currentVerificationId = data.id;
                this.displayVerification(data);
                this.updateUserCredits(data.remaining_credits);

                const capabilityText = capability === 'voice' ? '📞 Voice' : '📱 SMS';
                this.showNotification(`${capabilityText} verification created! Cost: $${data.cost}`, 'success');
                this.startAutoRefresh();
            } else {
                if (response.status === 402) {
                    this.showNotification('Insufficient funds. Please fund your wallet', 'error');
                } else {
                    this.showNotification(data.detail || 'Failed to create verification', 'error');
                }
            }
        } catch (error) {
            this.showNotification('Network error. Please try again.', 'error');
        } finally {
            if (createBtnText) createBtnText.style.display = 'inline';
            if (createLoading) createLoading.style.display = 'none';
        }
    }

    // Display verification details
    displayVerification(data) {
        const serviceNameEl = document.getElementById('service-name');
        const phoneNumberEl = document.getElementById('phone-number');
        const statusEl = document.getElementById('status');
        const checkBtnText = document.getElementById('check-btn-text');

        if (serviceNameEl) serviceNameEl.textContent = data.service_name;
        if (phoneNumberEl) phoneNumberEl.textContent = data.phone_number;
        if (statusEl) statusEl.textContent = data.status;

        // Update check button text based on capability
        if (checkBtnText) {
            const icon = data.capability === 'voice' ? '📞' : '📱';
            const text = data.capability === 'voice' ? 'Check Voice Call' : 'Check SMS';
            checkBtnText.textContent = `${icon} ${text}`;
        }

        // Add capability indicator
        const verificationCard = document.getElementById('verification-card');
        if (verificationCard) {
            const existingIndicator = verificationCard.querySelector('.capability-indicator');
            if (existingIndicator) existingIndicator.remove();

            const capabilityDiv = document.createElement('div');
            capabilityDiv.className = 'capability-indicator';
            capabilityDiv.style.cssText = 'background: #f0f9ff; color: #0369a1; padding: 8px 12px; border-radius: 6px; margin: 10px 0; font-size: 14px; font-weight: 600;';
            
            const capabilityIcon = data.capability === 'voice' ? '📞' : '📱';
            const capabilityText = data.capability === 'voice' ? 'Voice Call' : 'SMS Text';
            capabilityDiv.textContent = `${capabilityIcon} ${capabilityText} Verification`;

            const phoneDiv = verificationCard.querySelector('.phone-display');
            if (phoneDiv) {
                phoneDiv.parentNode.insertBefore(capabilityDiv, phoneDiv.nextSibling);
            }

            verificationCard.style.display = 'block';
        }

        const messagesSection = document.getElementById('messages-section');
        if (messagesSection) messagesSection.style.display = 'none';
    }

    // Check for messages or voice calls
    async checkMessages() {
        if (!this.currentVerificationId) return;

        const token = localStorage.getItem('token');
        const capability = this.currentCapability;
        const endpoint = capability === 'voice' ? 'voice' : 'messages';

        try {
            const response = await fetch(`/verify/${this.currentVerificationId}/${endpoint}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (response.ok) {
                const data = await response.json();

                if (data.messages && data.messages.length > 0) {
                    this.stopAutoRefresh();
                    this.displayMessages(data, capability);
                    const messageType = capability === 'voice' ? 'Voice call' : 'SMS';
                    this.showNotification(`${messageType} received!`, 'success');
                } else {
                    const waitingType = capability === 'voice' ? 'voice call' : 'SMS';
                    this.showNotification(`No ${waitingType} yet. Keep waiting...`, 'info');
                }
            } else {
                this.showNotification('Failed to check messages', 'error');
            }
        } catch (error) {
            this.showNotification('Network error', 'error');
        }
    }

    // Display received messages
    displayMessages(data, capability = 'sms') {
        const messagesList = document.getElementById('messages-list');
        if (!messagesList) return;

        const isVoice = capability === 'voice';
        const messageType = isVoice ? 'Voice Call' : 'SMS Message';
        const icon = isVoice ? '📞' : '📱';

        let html = `
            <div style="background: #10b981; color: white; padding: 20px; border-radius: 12px; margin-bottom: 20px; text-align: center;">
                <h3 style="margin: 0 0 8px 0;">${icon} ${messageType} Received!</h3>
                <p style="margin: 0; opacity: 0.9;">Your verification code has arrived</p>
            </div>
        `;

        data.messages.forEach(msg => {
            const code = msg.match(/\b\d{4,8}\b/)?.[0] || msg;
            html += `
                <div style="background: #f0fdf4; border: 2px solid #10b981; border-radius: 12px; padding: 20px; margin-bottom: 15px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <strong style="color: #166534;">Verification Code:</strong>
                        <button onclick="verificationManager.copyCode('${code}')" style="background: #10b981; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: 600;">Copy Code</button>
                    </div>
                    <div onclick="verificationManager.copyCode('${code}')" style="font-family: monospace; font-size: 24px; font-weight: bold; color: #166534; background: white; padding: 15px; border-radius: 8px; text-align: center; cursor: pointer; border: 2px dashed #10b981;">${code}</div>
                    <details style="margin-top: 12px;">
                        <summary style="cursor: pointer; color: #6b7280; font-size: 13px;">Full ${messageType.toLowerCase()}</summary>
                        <div style="margin-top: 8px; font-size: 13px; color: #6b7280; background: #f9fafb; padding: 10px; border-radius: 6px;">${msg}</div>
                    </details>
                </div>
            `;
        });

        // Add voice-specific details if available
        if (isVoice && data.transcription) {
            html += `
                <div style="background: #fef3c7; border: 2px solid #f59e0b; border-radius: 12px; padding: 15px; margin-bottom: 15px;">
                    <h4 style="color: #92400e; margin: 0 0 8px 0;">📝 Call Transcription</h4>
                    <p style="color: #92400e; margin: 0; font-style: italic;">"${data.transcription}"</p>
                    ${data.call_duration ? `<p style="color: #6b7280; font-size: 12px; margin: 8px 0 0 0;">Call duration: ${data.call_duration}s</p>` : ''}
                </div>
            `;
        }

        html += `
            <button onclick="verificationManager.tryAnotherService()" style="width: 100%; background: #667eea; color: white; padding: 14px; font-size: 16px; font-weight: 600; border: none; border-radius: 8px; cursor: pointer; margin-top: 15px;">
                ✨ Try Another Service
            </button>
        `;

        messagesList.innerHTML = html;
        const messagesSection = document.getElementById('messages-section');
        if (messagesSection) messagesSection.style.display = 'block';
    }

    // Copy verification code
    copyCode(code) {
        navigator.clipboard.writeText(code).then(() => {
            this.showNotification(`Code ${code} copied to clipboard!`, 'success');
        }).catch(() => {
            this.showNotification('Failed to copy code', 'error');
        });
    }

    // Copy phone number
    copyPhone() {
        const phoneEl = document.getElementById('phone-number');
        if (phoneEl && phoneEl.textContent && phoneEl.textContent !== 'Loading...') {
            navigator.clipboard.writeText(phoneEl.textContent).then(() => {
                this.showNotification('📱 Phone number copied to clipboard!', 'success');
            }).catch(() => {
                this.showNotification('Failed to copy phone number', 'error');
            });
        }
    }

    // Start auto-refresh for checking messages
    startAutoRefresh() {
        if (this.autoRefreshInterval) clearInterval(this.autoRefreshInterval);

        this.autoRefreshInterval = setInterval(() => {
            if (this.currentVerificationId) {
                this.checkMessages();
            }
        }, 10000); // Check every 10 seconds
    }

    // Stop auto-refresh
    stopAutoRefresh() {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
            this.autoRefreshInterval = null;
        }
    }

    // Cancel verification
    async cancelVerification() {
        if (!this.currentVerificationId) {
            this.showNotification('No active verification to cancel', 'error');
            return;
        }

        if (!confirm('Cancel this verification and get refund?')) return;

        const token = localStorage.getItem('token');
        this.stopAutoRefresh();

        try {
            const response = await fetch(`/verify/${this.currentVerificationId}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });

            const data = await response.json();

            if (response.ok) {
                this.updateUserCredits(data.new_balance);
                this.showNotification(`✅ Cancelled! Refunded $${data.refunded.toFixed(2)}`, 'success');
                this.clearSession();
            } else {
                this.showNotification(data.detail || 'Failed to cancel verification', 'error');
            }
        } catch (error) {
            this.showNotification('Network error. Please try again.', 'error');
        }
    }

    // Try another service
    tryAnotherService() {
        this.clearSession();
        const serviceSelect = document.getElementById('service-select');
        if (serviceSelect) {
            serviceSelect.scrollIntoView({ behavior: 'smooth' });
            serviceSelect.focus();
        }
        this.showNotification('Select a new service to verify', 'success');
    }

    // Clear current session
    clearSession() {
        this.currentVerificationId = null;
        this.currentCapability = 'sms';
        this.verificationStartTime = null;
        this.currentRetryCount = 0;
        this.stopAutoRefresh();

        const verificationCard = document.getElementById('verification-card');
        const messagesSection = document.getElementById('messages-section');

        if (verificationCard) verificationCard.style.display = 'none';
        if (messagesSection) messagesSection.style.display = 'none';

        // Reset capability selection to SMS
        const smsRadio = document.querySelector('input[name="capability"][value="sms"]');
        if (smsRadio) smsRadio.checked = true;
        this.updateCapabilitySelection();
    }

    // Update user credits display
    updateUserCredits(credits) {
        const creditsEl = document.getElementById('user-credits');
        if (creditsEl) {
            creditsEl.textContent = credits.toFixed(2);
        }
    }

    // Show notification
    showNotification(message, type = 'info') {
        const notification = document.getElementById('notification');
        if (notification) {
            notification.textContent = message;
            notification.className = `notification ${type}`;
            notification.style.display = 'block';

            setTimeout(() => {
                notification.style.display = 'none';
            }, 4000);
        }
    }
}

// Global verification manager instance
const verificationManager = new VerificationManager();

// Global functions for backward compatibility
function createVerification() {
    return verificationManager.createVerification();
}

function checkMessages() {
    return verificationManager.checkMessages();
}

function cancelVerification() {
    return verificationManager.cancelVerification();
}

function copyPhone() {
    return verificationManager.copyPhone();
}

function tryAnotherService() {
    return verificationManager.tryAnotherService();
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    verificationManager.init();
});