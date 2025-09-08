/**
 * Enhanced Chat Interface JavaScript
 * Implements advanced chat features including typing indicators, read receipts,
 * desktop notifications, and message threading
 */

class EnhancedChatInterface {
    constructor() {
        this.ws = null;
        this.currentUser = null;
        this.currentConversation = null;
        this.conversations = [];
        this.typingTimer = null;
        this.isTyping = false;
        this.notificationsEnabled = false;
        this.soundEnabled = false;
        this.settings = {
            showTimestamps: true,
            showReadReceipts: true,
            autoScroll: true,
            desktopNotifications: false,
            soundNotifications: false
        };
        
        // Message pagination
        this.messageOffset = 0;
        this.messageLimit = 50;
        this.hasMoreMessages = true;
        this.loadingMessages = false;
        
        // Typing indicators
        this.typingUsers = new Set();
        
        // Initialize the interface
        this.init();
    }

    async init() {
        try {
            // Load user settings
            await this.loadUserSettings();
            
            // Initialize user
            await this.initializeUser();
            
            // Setup WebSocket connection
            await this.connectWebSocket();
            
            // Load conversations
            await this.loadConversations();
            
            // Setup event listeners
            this.setupEventListeners();
            
            // Request notification permission
            await this.requestNotificationPermission();
            
            console.log('Enhanced chat interface initialized successfully');
        } catch (error) {
            console.error('Failed to initialize chat interface:', error);
            this.showError('Failed to initialize chat interface');
        }
    }

    async initializeUser() {
        try {
            // Get current user from JWT token or session
            const response = await fetch('/api/auth/me', {
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`
                }
            });
            
            if (response.ok) {
                this.currentUser = await response.json();
                document.getElementById('current-user').textContent = this.currentUser.username;
                this.updateUserStatus('online');
            } else {
                throw new Error('Failed to get user info');
            }
        } catch (error) {
            console.error('Error initializing user:', error);
            // Fallback to demo user
            this.currentUser = { id: 'demo_user', username: 'Demo User' };
            document.getElementById('current-user').textContent = this.currentUser.username;
        }
    }

    async connectWebSocket() {
        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/chat?token=${this.getAuthToken()}`;
            
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.updateConnectionStatus('connected');
            };
            
            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            };
            
            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.updateConnectionStatus('disconnected');
                // Attempt to reconnect after 3 seconds
                setTimeout(() => this.connectWebSocket(), 3000);
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateConnectionStatus('disconnected');
            };
            
        } catch (error) {
            console.error('Failed to connect WebSocket:', error);
            this.updateConnectionStatus('disconnected');
        }
    }

    handleWebSocketMessage(data) {
        console.log('WebSocket message received:', data);
        
        switch (data.type) {
            case 'new_message':
                this.handleNewMessage(data.message);
                break;
            case 'message_read':
                this.handleMessageRead(data);
                break;
            case 'typing_indicator':
                this.handleTypingIndicator(data);
                break;
            case 'user_status':
                this.handleUserStatus(data);
                break;
            case 'conversation_updated':
                this.handleConversationUpdate(data);
                break;
            case 'error':
                this.showError(data.message);
                break;
        }
    }

    async loadConversations() {
        try {
            const response = await fetch('/api/conversations/', {
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.conversations = data.conversations;
                this.renderConversations();
            } else {
                throw new Error('Failed to load conversations');
            }
        } catch (error) {
            console.error('Error loading conversations:', error);
            this.showError('Failed to load conversations');
        }
    }

    renderConversations() {
        const container = document.getElementById('conversations-list');
        
        if (this.conversations.length === 0) {
            container.innerHTML = `
                <div class="text-center text-muted p-4">
                    <i class="fas fa-inbox fa-2x mb-2"></i>
                    <p>No conversations yet</p>
                    <button class="btn btn-primary btn-sm" onclick="chatInterface.showNewConversationModal()">
                        Start a conversation
                    </button>
                </div>
            `;
            return;
        }
        
        container.innerHTML = this.conversations.map(conv => {
            const isActive = this.currentConversation?.id === conv.id;
            const hasUnread = conv.unread_count > 0;
            
            return `
                <div class="conversation-item ${isActive ? 'active' : ''} ${hasUnread ? 'unread' : ''}" 
                     onclick="chatInterface.selectConversation('${conv.id}')">
                    <div class="conversation-name">
                        <span>${this.escapeHtml(conv.title)}</span>
                        ${hasUnread ? `<span class="unread-badge">${conv.unread_count}</span>` : ''}
                    </div>
                    <div class="conversation-preview">
                        ${conv.last_message ? this.escapeHtml(conv.last_message.content) : 'No messages yet'}
                    </div>
                    <div class="conversation-meta">
                        <span class="conversation-time">
                            ${conv.last_message ? this.formatTime(conv.last_message.created_at) : ''}
                        </span>
                        ${conv.external_number ? '<i class="fas fa-mobile-alt text-muted"></i>' : '<i class="fas fa-user text-muted"></i>'}
                    </div>
                </div>
            `;
        }).join('');
    }

    async selectConversation(conversationId) {
        try {
            const conversation = this.conversations.find(c => c.id === conversationId);
            if (!conversation) return;
            
            this.currentConversation = conversation;
            
            // Update UI
            document.getElementById('chat-header').style.display = 'block';
            document.getElementById('message-input-container').style.display = 'block';
            document.getElementById('conversation-title').textContent = conversation.title;
            
            // Update subtitle
            let subtitle = '';
            if (conversation.external_number) {
                subtitle = `SMS: ${conversation.external_number}`;
            } else if (conversation.participant_count > 0) {
                subtitle = `${conversation.participant_count} participant${conversation.participant_count > 1 ? 's' : ''}`;
            }
            document.getElementById('conversation-subtitle').textContent = subtitle;
            
            // Reset message pagination
            this.messageOffset = 0;
            this.hasMoreMessages = true;
            
            // Load messages
            await this.loadMessages(conversationId);
            
            // Mark messages as read
            await this.markMessagesAsRead(conversationId);
            
            // Update conversations list
            this.renderConversations();
            
            // Join conversation via WebSocket
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify({
                    type: 'join_conversation',
                    conversation_id: conversationId
                }));
            }
            
        } catch (error) {
            console.error('Error selecting conversation:', error);
            this.showError('Failed to load conversation');
        }
    }

    async loadMessages(conversationId, append = false) {
        if (this.loadingMessages || !this.hasMoreMessages) return;
        
        try {
            this.loadingMessages = true;
            
            const response = await fetch(
                `/api/conversations/${conversationId}/messages?limit=${this.messageLimit}&offset=${this.messageOffset}`,
                {
                    headers: {
                        'Authorization': `Bearer ${this.getAuthToken()}`
                    }
                }
            );
            
            if (response.ok) {
                const data = await response.json();
                
                if (append) {
                    this.appendMessages(data.messages);
                } else {
                    this.renderMessages(data.messages);
                }
                
                this.hasMoreMessages = data.has_more;
                this.messageOffset += data.messages.length;
            } else {
                throw new Error('Failed to load messages');
            }
        } catch (error) {
            console.error('Error loading messages:', error);
            this.showError('Failed to load messages');
        } finally {
            this.loadingMessages = false;
        }
    }

    renderMessages(messages) {
        const container = document.getElementById('messages-container');
        
        if (messages.length === 0) {
            container.innerHTML = `
                <div class="text-center text-muted mt-5">
                    <i class="fas fa-comment fa-2x mb-2"></i>
                    <p>No messages yet. Start the conversation!</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = messages.reverse().map(msg => this.createMessageElement(msg)).join('');
        
        if (this.settings.autoScroll) {
            this.scrollToBottom();
        }
    }

    appendMessages(messages) {
        const container = document.getElementById('messages-container');
        const scrollTop = container.scrollTop;
        
        messages.forEach(msg => {
            const messageEl = document.createElement('div');
            messageEl.innerHTML = this.createMessageElement(msg);
            container.insertBefore(messageEl.firstChild, container.firstChild);
        });
        
        // Maintain scroll position
        container.scrollTop = scrollTop + (container.scrollHeight - scrollTop);
    }

    createMessageElement(message) {
        const isSent = message.sender_id === this.currentUser.id;
        const timestamp = this.settings.showTimestamps ? this.formatTime(message.created_at) : '';
        const readReceipt = this.settings.showReadReceipts && isSent ? this.getReadReceiptIcon(message) : '';
        
        return `
            <div class="message ${isSent ? 'sent' : 'received'}" data-message-id="${message.id}">
                <div class="message-bubble">
                    <div class="message-content">${this.escapeHtml(message.content)}</div>
                    <div class="message-meta">
                        <span class="message-time">${timestamp}</span>
                        ${readReceipt ? `<span class="message-status">${readReceipt}</span>` : ''}
                    </div>
                </div>
            </div>
        `;
    }

    getReadReceiptIcon(message) {
        if (message.is_read) {
            return '<i class="fas fa-check-double status-read" title="Read"></i>';
        } else if (message.is_delivered) {
            return '<i class="fas fa-check-double status-delivered" title="Delivered"></i>';
        } else if (message.delivery_status === 'sent') {
            return '<i class="fas fa-check status-sent" title="Sent"></i>';
        } else if (message.delivery_status === 'failed') {
            return '<i class="fas fa-exclamation-triangle status-failed" title="Failed"></i>';
        }
        return '';
    }

    handleNewMessage(message) {
        // Update conversation in list
        const convIndex = this.conversations.findIndex(c => c.id === message.conversation_id);
        if (convIndex !== -1) {
            this.conversations[convIndex].last_message = message;
            this.conversations[convIndex].updated_at = message.created_at;
            
            // Move to top
            const conv = this.conversations.splice(convIndex, 1)[0];
            this.conversations.unshift(conv);
            
            this.renderConversations();
        }
        
        // If this is the current conversation, add message
        if (this.currentConversation && this.currentConversation.id === message.conversation_id) {
            const container = document.getElementById('messages-container');
            const messageEl = document.createElement('div');
            messageEl.innerHTML = this.createMessageElement(message);
            container.appendChild(messageEl.firstChild);
            
            if (this.settings.autoScroll) {
                this.scrollToBottom();
            }
            
            // Mark as read if not sent by current user
            if (message.sender_id !== this.currentUser.id) {
                this.markMessagesAsRead(message.conversation_id);
            }
        }
        
        // Show desktop notification
        if (message.sender_id !== this.currentUser.id) {
            this.showDesktopNotification(message);
        }
    }

    async sendMessage() {
        const textarea = document.getElementById('message-textarea');
        const content = textarea.value.trim();
        
        if (!content || !this.currentConversation) return;
        
        const sendButton = document.getElementById('send-button');
        sendButton.disabled = true;
        
        try {
            const response = await fetch(`/api/conversations/${this.currentConversation.id}/messages`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getAuthToken()}`
                },
                body: JSON.stringify({
                    content: content,
                    message_type: 'CHAT'
                })
            });
            
            if (response.ok) {
                textarea.value = '';
                this.adjustTextareaHeight(textarea);
                this.stopTyping();
            } else {
                const error = await response.json();
                this.showError('Failed to send message: ' + error.detail);
            }
        } catch (error) {
            console.error('Error sending message:', error);
            this.showError('Failed to send message');
        } finally {
            sendButton.disabled = false;
        }
    }

    handleTypingIndicator(data) {
        if (!this.currentConversation || data.conversation_id !== this.currentConversation.id) return;
        
        const typingIndicators = document.getElementById('typing-indicators');
        const typingText = document.getElementById('typing-text');
        
        if (data.typing_users && data.typing_users.length > 0) {
            const typingUsers = data.typing_users.filter(uid => uid !== this.currentUser.id);
            
            if (typingUsers.length > 0) {
                const userText = typingUsers.length === 1 ? 'Someone is' : `${typingUsers.length} people are`;
                typingText.textContent = `${userText} typing...`;
                typingIndicators.style.display = 'block';
            } else {
                typingIndicators.style.display = 'none';
            }
        } else {
            typingIndicators.style.display = 'none';
        }
    }

    startTyping() {
        if (!this.currentConversation || this.isTyping) return;
        
        this.isTyping = true;
        
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'typing',
                conversation_id: this.currentConversation.id,
                is_typing: true
            }));
        }
    }

    stopTyping() {
        if (!this.isTyping) return;
        
        this.isTyping = false;
        
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'typing',
                conversation_id: this.currentConversation.id,
                is_typing: false
            }));
        }
    }

    async markMessagesAsRead(conversationId) {
        try {
            await fetch(`/api/conversations/${conversationId}/messages/mark-read`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`
                }
            });
        } catch (error) {
            console.error('Error marking messages as read:', error);
        }
    }

    async showDesktopNotification(message) {
        if (!this.settings.desktopNotifications || !this.notificationsEnabled) return;
        
        try {
            const conversation = this.conversations.find(c => c.id === message.conversation_id);
            const title = conversation ? conversation.title : 'New Message';
            
            const notification = new Notification(title, {
                body: message.content,
                icon: '/static/images/logo.png',
                tag: message.conversation_id
            });
            
            notification.onclick = () => {
                window.focus();
                this.selectConversation(message.conversation_id);
                notification.close();
            };
            
            // Auto-close after 5 seconds
            setTimeout(() => notification.close(), 5000);
            
        } catch (error) {
            console.error('Error showing desktop notification:', error);
        }
    }

    async requestNotificationPermission() {
        if ('Notification' in window) {
            const permission = await Notification.requestPermission();
            this.notificationsEnabled = permission === 'granted';
            this.updateNotificationButton();
        }
    }

    updateNotificationButton() {
        const btn = document.getElementById('notification-btn');
        const icon = document.getElementById('notification-icon');
        
        if (this.notificationsEnabled && this.settings.desktopNotifications) {
            btn.classList.remove('btn-outline-light');
            btn.classList.add('btn-light');
            icon.classList.remove('fa-bell-slash');
            icon.classList.add('fa-bell');
        } else {
            btn.classList.remove('btn-light');
            btn.classList.add('btn-outline-light');
            icon.classList.remove('fa-bell');
            icon.classList.add('fa-bell-slash');
        }
    }

    setupEventListeners() {
        // Message input handlers
        const textarea = document.getElementById('message-textarea');
        
        textarea.addEventListener('input', () => {
            this.handleMessageInput();
        });
        
        // Scroll handler for infinite scroll
        const messagesContainer = document.getElementById('messages-container');
        messagesContainer.addEventListener('scroll', () => {
            if (messagesContainer.scrollTop === 0 && this.hasMoreMessages && !this.loadingMessages) {
                this.loadMessages(this.currentConversation.id, true);
            }
        });
        
        // Conversation search
        const searchInput = document.getElementById('conversation-search');
        searchInput.addEventListener('input', () => {
            this.filterConversations();
        });
        
        // Window focus handler
        window.addEventListener('focus', () => {
            if (this.currentConversation) {
                this.markMessagesAsRead(this.currentConversation.id);
            }
        });
    }

    handleMessageInput() {
        const textarea = document.getElementById('message-textarea');
        const sendButton = document.getElementById('send-button');
        
        // Enable/disable send button
        sendButton.disabled = !textarea.value.trim();
        
        // Adjust textarea height
        this.adjustTextareaHeight(textarea);
        
        // Handle typing indicators
        if (textarea.value.trim()) {
            this.startTyping();
            
            // Clear existing timer
            clearTimeout(this.typingTimer);
            
            // Set timer to stop typing
            this.typingTimer = setTimeout(() => {
                this.stopTyping();
            }, 1000);
        } else {
            this.stopTyping();
        }
    }

    handleMessageKeyDown(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            this.sendMessage();
        }
    }

    adjustTextareaHeight(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    }

    filterConversations() {
        const query = document.getElementById('conversation-search').value.toLowerCase();
        const items = document.querySelectorAll('.conversation-item');
        
        items.forEach(item => {
            const name = item.querySelector('.conversation-name span').textContent.toLowerCase();
            const preview = item.querySelector('.conversation-preview').textContent.toLowerCase();
            
            if (name.includes(query) || preview.includes(query)) {
                item.style.display = 'block';
            } else {
                item.style.display = 'none';
            }
        });
    }

    updateConnectionStatus(status) {
        const statusEl = document.getElementById('connection-status');
        const textEl = document.getElementById('connection-text');
        
        statusEl.className = `connection-status ${status}`;
        
        switch (status) {
            case 'connected':
                textEl.innerHTML = '<i class="fas fa-wifi me-1"></i>Connected';
                break;
            case 'connecting':
                textEl.innerHTML = '<i class="fas fa-wifi me-1"></i>Connecting...';
                break;
            case 'disconnected':
                textEl.innerHTML = '<i class="fas fa-wifi me-1"></i>Disconnected - Reconnecting...';
                break;
        }
    }

    updateUserStatus(status) {
        const statusEl = document.getElementById('user-status');
        statusEl.className = status === 'online' ? 'online-indicator' : 'offline-indicator';
    }

    scrollToBottom() {
        const container = document.getElementById('messages-container');
        container.scrollTop = container.scrollHeight;
    }

    showError(message) {
        // Create and show error toast/notification
        console.error(message);
        // You could implement a toast notification system here
    }

    showSuccess(message) {
        // Create and show success toast/notification
        console.log(message);
        // You could implement a toast notification system here
    }

    formatTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now - date;
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
        
        if (diffDays === 0) {
            return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        } else if (diffDays === 1) {
            return 'Yesterday';
        } else if (diffDays < 7) {
            return date.toLocaleDateString([], { weekday: 'short' });
        } else {
            return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    getAuthToken() {
        // Get JWT token from localStorage, sessionStorage, or cookie
        return localStorage.getItem('auth_token') || 'demo_token';
    }

    async loadUserSettings() {
        try {
            const saved = localStorage.getItem('chat_settings');
            if (saved) {
                this.settings = { ...this.settings, ...JSON.parse(saved) };
            }
        } catch (error) {
            console.error('Error loading user settings:', error);
        }
    }

    saveUserSettings() {
        try {
            localStorage.setItem('chat_settings', JSON.stringify(this.settings));
        } catch (error) {
            console.error('Error saving user settings:', error);
        }
    }

    // Modal and UI functions
    showNewConversationModal() {
        const modal = new bootstrap.Modal(document.getElementById('newConversationModal'));
        modal.show();
    }

    showSettings() {
        // Update settings modal with current values
        document.getElementById('desktop-notifications').checked = this.settings.desktopNotifications;
        document.getElementById('sound-notifications').checked = this.settings.soundNotifications;
        document.getElementById('show-timestamps').checked = this.settings.showTimestamps;
        document.getElementById('show-read-receipts').checked = this.settings.showReadReceipts;
        document.getElementById('auto-scroll').checked = this.settings.autoScroll;
        
        const modal = new bootstrap.Modal(document.getElementById('settingsModal'));
        modal.show();
    }

    updateNotificationSettings() {
        this.settings.desktopNotifications = document.getElementById('desktop-notifications').checked;
        this.settings.soundNotifications = document.getElementById('sound-notifications').checked;
        this.saveUserSettings();
        this.updateNotificationButton();
    }

    updateChatSettings() {
        this.settings.showTimestamps = document.getElementById('show-timestamps').checked;
        this.settings.showReadReceipts = document.getElementById('show-read-receipts').checked;
        this.settings.autoScroll = document.getElementById('auto-scroll').checked;
        this.saveUserSettings();
        
        // Re-render current messages if conversation is selected
        if (this.currentConversation) {
            this.loadMessages(this.currentConversation.id);
        }
    }

    toggleNotifications() {
        if (this.notificationsEnabled) {
            this.settings.desktopNotifications = !this.settings.desktopNotifications;
            this.saveUserSettings();
            this.updateNotificationButton();
        } else {
            this.requestNotificationPermission();
        }
    }
}

// Global functions for HTML event handlers
let chatInterface;

document.addEventListener('DOMContentLoaded', function() {
    chatInterface = new EnhancedChatInterface();
});

// Global functions that can be called from HTML
function sendMessage() {
    chatInterface.sendMessage();
}

function handleMessageKeyDown(event) {
    chatInterface.handleMessageKeyDown(event);
}

function handleMessageInput() {
    chatInterface.handleMessageInput();
}

function toggleNotifications() {
    chatInterface.toggleNotifications();
}

function showSettings() {
    chatInterface.showSettings();
}

function updateNotificationSettings() {
    chatInterface.updateNotificationSettings();
}

function updateChatSettings() {
    chatInterface.updateChatSettings();
}

function showNewConversationModal() {
    chatInterface.showNewConversationModal();
}