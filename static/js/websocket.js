// WebSocket Client for Real-time SMS Updates and Notifications
class WebSocketManager {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.isConnected = false;
        this.subscriptions = new Map();
        this.messageQueue = [];
        this.heartbeatInterval = null;
        this.init();
    }

    init() {
        this.updateConnectionStatus('connecting');
        this.connect();
        this.setupHeartbeat();
    }

    connect() {
        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            this.ws = new WebSocket(wsUrl);
            this.setupEventHandlers();
        } catch (error) {
            console.error('WebSocket connection error:', error);
            this.handleConnectionError();
        }
    }

    setupEventHandlers() {
        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            this.updateConnectionStatus('connected');
            this.authenticate();
            this.processMessageQueue();
        };

        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                // Validate message structure
                if (this.validateMessage(data)) {
                    this.handleMessage(data);
                }
            } catch (error) {
                console.error('WebSocket message parse error:', error);
            }
        };

        this.ws.onclose = (event) => {
            console.log('WebSocket disconnected:', event.code, event.reason);
            this.isConnected = false;
            this.updateConnectionStatus('disconnected');
            this.handleReconnect();
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.handleConnectionError();
        };
    }

    authenticate() {
        const token = localStorage.getItem('token');
        if (token && window.securityManager?.validateToken(token)) {
            this.send({
                type: 'auth',
                token: token
            });
        }
    }

    send(data) {
        if (this.isConnected && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        } else {
            this.messageQueue.push(data);
        }
    }

    processMessageQueue() {
        while (this.messageQueue.length > 0) {
            const message = this.messageQueue.shift();
            this.send(message);
        }
    }

    handleMessage(data) {
        switch (data.type) {
            case 'auth_success':
                console.log('WebSocket authenticated');
                break;
                
            case 'auth_error':
                console.error('WebSocket auth error:', data.message);
                this.updateConnectionStatus('auth_failed');
                break;
                
            case 'verification_update':
                this.handleVerificationUpdate(data);
                break;
                
            case 'sms_received':
                this.handleSMSReceived(data);
                break;
                
            case 'notification':
                this.handleNotification(data);
                break;
                
            case 'pong':
                // Heartbeat response
                break;
                
            default:
                console.log('Unknown WebSocket message type:', data.type);
        }
    }

    handleVerificationUpdate(data) {
        const { verification_id, status, phone_number } = data;
        
        // Update verification status in UI
        this.updateVerificationStatus(verification_id, status);
        
        // Notify subscribers
        const callback = this.subscriptions.get(verification_id);
        if (callback) {
            callback(data);
        }
        
        // Show notification
        if (typeof showNotification === 'function') {
            const statusEmoji = status === 'completed' ? '✅' : status === 'failed' ? '❌' : '🔄';
            showNotification(`${statusEmoji} Verification ${status}: ${phone_number}`, 'info');
        }
    }

    handleSMSReceived(data) {
        const { verification_id, message, sender, timestamp } = data;
        
        // Update messages in UI
        this.displayNewMessage(verification_id, message, sender, timestamp);
        
        // Notify subscribers
        const callback = this.subscriptions.get(verification_id);
        if (callback) {
            callback(data);
        }
        
        // Show notification
        if (typeof showNotification === 'function') {
            showNotification(`📨 New SMS from ${sender}: ${message.substring(0, 50)}...`, 'success');
        }
        
        // Play notification sound
        this.playNotificationSound();
    }

    handleNotification(data) {
        const { title, message, type } = data;
        
        if (typeof showNotification === 'function') {
            showNotification(`${title}: ${message}`, type || 'info');
        }
        
        // Update notification badge
        if (typeof updateNotificationIndicators === 'function') {
            updateNotificationIndicators(data.unread_count || 0);
        }
    }

    updateVerificationStatus(verificationId, status) {
        const statusElement = document.querySelector(`[data-verification-id="${verificationId}"] .status`);
        if (statusElement) {
            statusElement.textContent = status;
            statusElement.className = `status ${status}`;
        }
        
        // Update active verifications
        if (typeof enhancedVerification !== 'undefined') {
            enhancedVerification.updateVerificationInList(verificationId, { status });
        }
    }

    displayNewMessage(verificationId, message, sender, timestamp) {
        const messagesContainer = document.getElementById('messages-list');
        if (messagesContainer && document.getElementById('verification-details')?.dataset.verificationId === verificationId) {
            const messageElement = this.createMessageElement(message, sender, timestamp);
            messagesContainer.appendChild(messageElement);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
            
            // Hide "no messages" state
            const noMessages = document.getElementById('no-messages');
            if (noMessages) {
                noMessages.style.display = 'none';
            }
        }
    }

    createMessageElement(message, sender, timestamp) {
        const div = document.createElement('div');
        div.className = 'message-item';
        
        const header = document.createElement('div');
        header.className = 'message-header';
        
        const senderEl = document.createElement('strong');
        senderEl.textContent = this.sanitizeText(sender);
        
        const timeEl = document.createElement('span');
        timeEl.className = 'message-time';
        timeEl.textContent = new Date(timestamp).toLocaleTimeString();
        
        header.appendChild(senderEl);
        header.appendChild(timeEl);
        
        const content = document.createElement('div');
        content.className = 'message-content';
        content.textContent = this.sanitizeText(message);
        
        div.appendChild(header);
        div.appendChild(content);
        
        return div;
    }

    playNotificationSound() {
        try {
            const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIG2m98OScTgwOUarm7blmGgU7k9n1unEiBC13yO/eizEIHWq+8+OWT');
            audio.volume = 0.3;
            audio.play().catch(() => {}); // Ignore errors
        } catch (error) {
            // Ignore audio errors
        }
    }

    subscribeToVerification(verificationId, callback) {
        this.subscriptions.set(verificationId, callback);
        
        // Send subscription message
        this.send({
            type: 'subscribe',
            verification_id: verificationId
        });
    }

    unsubscribeFromVerification(verificationId) {
        this.subscriptions.delete(verificationId);
        
        // Send unsubscription message
        this.send({
            type: 'unsubscribe',
            verification_id: verificationId
        });
    }

    updateConnectionStatus(status) {
        const indicators = document.querySelectorAll('.status-dot, #connection-status');
        indicators.forEach(indicator => {
            indicator.className = `status-dot ${status}`;
            
            switch (status) {
                case 'connected':
                    indicator.title = 'Connected - Real-time updates active';
                    break;
                case 'connecting':
                    indicator.title = 'Connecting...';
                    break;
                case 'disconnected':
                    indicator.title = 'Disconnected - Using polling fallback';
                    break;
                case 'auth_failed':
                    indicator.title = 'Authentication failed';
                    break;
            }
        });
        
        // Update realtime indicator
        const realtimeIndicator = document.getElementById('realtime-indicator');
        if (realtimeIndicator) {
            realtimeIndicator.style.display = status === 'connected' ? 'block' : 'none';
        }
    }

    setupHeartbeat() {
        this.heartbeatInterval = setInterval(() => {
            if (this.isConnected) {
                this.send({ type: 'ping' });
            }
        }, 30000); // 30 seconds
    }

    handleConnectionError() {
        this.isConnected = false;
        this.updateConnectionStatus('disconnected');
        
        // Fallback to polling
        if (typeof startPollingFallback === 'function') {
            startPollingFallback();
        }
    }

    handleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
            
            console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
            
            setTimeout(() => {
                this.connect();
            }, delay);
        } else {
            console.log('Max reconnection attempts reached');
            this.updateConnectionStatus('failed');
            
            // Fallback to polling
            if (typeof startPollingFallback === 'function') {
                startPollingFallback();
            }
        }
    }

    disconnect() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
        }
        
        if (this.ws) {
            this.ws.close();
        }
        
        this.isConnected = false;
        this.subscriptions.clear();
        this.messageQueue = [];
    }

    // Public API
    isWebSocketConnected() {
        return this.isConnected;
    }

    getConnectionStatus() {
        if (this.isConnected) return 'connected';
        if (this.reconnectAttempts > 0) return 'reconnecting';
        return 'disconnected';
    }
}

// Polling fallback for when WebSocket fails
function startPollingFallback() {
    console.log('Starting polling fallback');
    
    // Poll for verification updates every 5 seconds
    const pollInterval = setInterval(async () => {
        if (window.wsManager?.isConnected) {
            clearInterval(pollInterval);
            return;
        }
        
        // Poll active verifications
        if (typeof enhancedVerification !== 'undefined') {
            await enhancedVerification.refreshActiveVerifications();
        }
    }, 5000);
    
    // Store interval for cleanup
    window.pollingInterval = pollInterval;
}

// Initialize WebSocket Manager
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize if user is authenticated
    const token = localStorage.getItem('token');
    if (token && window.securityManager?.validateToken(token)) {
        window.wsManager = new WebSocketManager();
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.wsManager) {
        window.wsManager.disconnect();
    }
    
    if (window.pollingInterval) {
        clearInterval(window.pollingInterval);
    }
});

    validateMessage(data) {
        if (!data || typeof data !== 'object') return false;
        if (!data.type || typeof data.type !== 'string') return false;
        
        const allowedTypes = ['auth_success', 'auth_error', 'verification_update', 'sms_received', 'notification', 'pong'];
        return allowedTypes.includes(data.type);
    }
    
    sanitizeText(text) {
        if (typeof text !== 'string') return '';
        return text.replace(/[<>"'&]/g, (match) => {
            const map = {
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#x27;',
                '&': '&amp;'
            };
            return map[match];
        });
    }
}

// Export for use in other modules
window.WebSocketManager = WebSocketManager;