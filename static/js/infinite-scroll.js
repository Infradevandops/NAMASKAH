/**
 * Infinite Scroll Implementation for Chat Messages
 * Handles loading older messages as user scrolls up
 */

class InfiniteScroll {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            threshold: 100, // pixels from top to trigger load
            limit: 50, // messages per load
            loadingClass: 'loading-messages',
            ...options
        };

        this.isLoading = false;
        this.hasMore = true;
        this.oldestMessageId = null;
        this.conversationId = null;
        this.totalMessages = 0;
        this.loadedMessages = 0;

        this.init();
    }

    init() {
        if (!this.container) {
            console.error('Infinite scroll container not found');
            return;
        }

        this.setupScrollListener();
        this.createLoadingIndicator();

        // Get conversation ID from URL or data attribute
        this.conversationId = this.getConversationId();

        // Load initial messages
        this.loadInitialMessages();
    }

    setupScrollListener() {
        this.container.addEventListener('scroll', this.throttle(() => {
            this.handleScroll();
        }, 100));
    }

    handleScroll() {
        if (this.isLoading || !this.hasMore) return;

        const scrollTop = this.container.scrollTop;

        // Check if user scrolled near the top
        if (scrollTop <= this.options.threshold) {
            this.loadMoreMessages();
        }
    }

    async loadInitialMessages() {
        if (!this.conversationId) return;

        try {
            this.showLoading();

            const response = await fetch(`/api/conversations/${this.conversationId}/messages?limit=${this.options.limit}`, {
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`Failed to load messages: ${response.statusText}`);
            }

            const data = await response.json();

            this.displayMessages(data.messages, false);
            this.totalMessages = data.total_count;
            this.loadedMessages = data.messages.length;
            this.hasMore = data.has_more;

            if (data.messages.length > 0) {
                this.oldestMessageId = data.messages[0].id;
            }

            // Scroll to bottom for initial load
            this.scrollToBottom();

        } catch (error) {
            console.error('Error loading initial messages:', error);
            this.showError('Failed to load messages');
        } finally {
            this.hideLoading();
        }
    }

    async loadMoreMessages() {
        if (this.isLoading || !this.hasMore || !this.conversationId) return;

        this.isLoading = true;
        this.showLoading();

        try {
            const params = new URLSearchParams({
                limit: this.options.limit.toString(),
                before_message_id: this.oldestMessageId || ''
            });

            const response = await fetch(`/api/conversations/${this.conversationId}/messages?${params}`, {
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`Failed to load more messages: ${response.statusText}`);
            }

            const data = await response.json();

            if (data.messages.length > 0) {
                // Store current scroll position
                const previousScrollHeight = this.container.scrollHeight;
                const previousScrollTop = this.container.scrollTop;

                // Add messages to the top
                this.displayMessages(data.messages, true);

                // Update state
                this.loadedMessages += data.messages.length;
                this.hasMore = data.has_more;
                this.oldestMessageId = data.messages[0].id;

                // Maintain scroll position
                const newScrollHeight = this.container.scrollHeight;
                const scrollDiff = newScrollHeight - previousScrollHeight;
                this.container.scrollTop = previousScrollTop + scrollDiff;

                // Update progress indicator
                this.updateProgressIndicator();

            } else {
                this.hasMore = false;
            }

        } catch (error) {
            console.error('Error loading more messages:', error);
            this.showError('Failed to load more messages');
        } finally {
            this.isLoading = false;
            this.hideLoading();
        }
    }

    displayMessages(messages, prepend = false) {
        const messagesContainer = this.getMessagesContainer();
        if (!messagesContainer) return;

        const fragment = document.createDocumentFragment();

        messages.forEach(message => {
            const messageElement = this.createMessageElement(message);
            if (prepend) {
                fragment.appendChild(messageElement);
            } else {
                fragment.appendChild(messageElement);
            }
        });

        if (prepend) {
            messagesContainer.insertBefore(fragment, messagesContainer.firstChild);
        } else {
            messagesContainer.appendChild(fragment);
        }

        // Mark messages as displayed
        this.markMessagesAsDisplayed(messages);
    }

    createMessageElement(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${message.sender_id === this.getCurrentUserId() ? 'sent' : 'received'}`;
        messageDiv.dataset.messageId = message.id;

        const timestamp = new Date(message.created_at);
        const timeString = this.formatMessageTime(timestamp);

        messageDiv.innerHTML = `
            <div class="message-header">
                <span class="sender-name">${message.sender_username || 'Unknown'}</span>
                <span class="message-time" title="${timestamp.toLocaleString()}">${timeString}</span>
                ${message.is_edited ? '<span class="edited-indicator">edited</span>' : ''}
            </div>
            <div class="message-content">${this.formatMessageContent(message.content)}</div>
            <div class="message-footer">
                <span class="message-type ${message.message_type}">${message.message_type}</span>
                ${message.is_delivered ? '<i class="fas fa-check delivery-status delivered" title="Delivered"></i>' : ''}
                ${message.is_read ? '<i class="fas fa-check-double read-status read" title="Read"></i>' : ''}
            </div>
        `;

        // Add click handler for message actions
        messageDiv.addEventListener('click', (e) => {
            if (e.detail === 2) { // Double click
                this.handleMessageDoubleClick(message);
            }
        });

        // Add context menu
        messageDiv.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            this.showMessageContextMenu(e, message);
        });

        return messageDiv;
    }

    formatMessageContent(content) {
        // Basic formatting for mentions, links, etc.
        let formatted = content;

        // Format mentions
        formatted = formatted.replace(/@(\w+)/g, '<span class="mention">@$1</span>');

        // Format URLs
        formatted = formatted.replace(
            /(https?:\/\/[^\s]+)/g,
            '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>'
        );

        // Format line breaks
        formatted = formatted.replace(/\n/g, '<br>');

        return formatted;
    }

    getMessagesContainer() {
        return this.container.querySelector('.messages-list') || this.container;
    }

    createLoadingIndicator() {
        const loadingDiv = document.createElement('div');
        loadingDiv.id = 'infinite-scroll-loading';
        loadingDiv.className = 'loading-indicator';
        loadingDiv.style.display = 'none';
        loadingDiv.innerHTML = `
            <div class="loading-spinner">
                <i class="fas fa-spinner fa-spin"></i>
                <span>Loading messages...</span>
            </div>
        `;

        // Insert at the top of the container
        this.container.insertBefore(loadingDiv, this.container.firstChild);
        this.loadingIndicator = loadingDiv;
    }

    showLoading() {
        if (this.loadingIndicator) {
            this.loadingIndicator.style.display = 'block';
        }
    }

    hideLoading() {
        if (this.loadingIndicator) {
            this.loadingIndicator.style.display = 'none';
        }
    }

    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.innerHTML = `
            <i class="fas fa-exclamation-triangle"></i>
            <span>${message}</span>
            <button onclick="this.parentElement.remove()">×</button>
        `;

        this.container.insertBefore(errorDiv, this.container.firstChild);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (errorDiv.parentElement) {
                errorDiv.remove();
            }
        }, 5000);
    }

    updateProgressIndicator() {
        const progressElement = document.getElementById('scroll-progress');
        if (progressElement && this.totalMessages > 0) {
            const percentage = Math.round((this.loadedMessages / this.totalMessages) * 100);
            progressElement.textContent = `${this.loadedMessages} of ${this.totalMessages} messages loaded (${percentage}%)`;
        }
    }

    scrollToBottom() {
        this.container.scrollTop = this.container.scrollHeight;
    }

    scrollToMessage(messageId) {
        const messageElement = this.container.querySelector(`[data-message-id="${messageId}"]`);
        if (messageElement) {
            messageElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
            messageElement.classList.add('highlighted');
            setTimeout(() => {
                messageElement.classList.remove('highlighted');
            }, 3000);
        }
    }

    markMessagesAsDisplayed(messages) {
        // Mark messages as read when they come into view
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const messageId = entry.target.dataset.messageId;
                    this.markMessageAsRead(messageId);
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.5 });

        messages.forEach(message => {
            const messageElement = this.container.querySelector(`[data-message-id="${message.id}"]`);
            if (messageElement && !message.is_read && message.sender_id !== this.getCurrentUserId()) {
                observer.observe(messageElement);
            }
        });
    }

    async markMessageAsRead(messageId) {
        try {
            await fetch(`/api/conversations/${this.conversationId}/messages/mark-read`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ up_to_message_id: messageId })
            });
        } catch (error) {
            console.error('Error marking message as read:', error);
        }
    }

    handleMessageDoubleClick(message) {
        // Handle message double-click (e.g., reply, quote)
        const event = new CustomEvent('messageDoubleClick', { detail: message });
        document.dispatchEvent(event);
    }

    showMessageContextMenu(event, message) {
        // Show context menu for message actions
        const contextMenu = document.createElement('div');
        contextMenu.className = 'message-context-menu';
        contextMenu.innerHTML = `
            <div class="context-menu-item" onclick="window.enhancedChat.replyToMessage('${message.id}')">
                <i class="fas fa-reply"></i> Reply
            </div>
            <div class="context-menu-item" onclick="window.enhancedChat.quoteMessage('${message.id}')">
                <i class="fas fa-quote-right"></i> Quote
            </div>
            ${message.sender_id === this.getCurrentUserId() ? `
                <div class="context-menu-item" onclick="window.enhancedChat.editMessage('${message.id}')">
                    <i class="fas fa-edit"></i> Edit
                </div>
                <div class="context-menu-item danger" onclick="window.enhancedChat.deleteMessage('${message.id}')">
                    <i class="fas fa-trash"></i> Delete
                </div>
            ` : ''}
        `;

        contextMenu.style.position = 'absolute';
        contextMenu.style.left = `${event.pageX}px`;
        contextMenu.style.top = `${event.pageY}px`;

        document.body.appendChild(contextMenu);

        // Remove on click outside
        const removeMenu = (e) => {
            if (!contextMenu.contains(e.target)) {
                contextMenu.remove();
                document.removeEventListener('click', removeMenu);
            }
        };

        setTimeout(() => {
            document.addEventListener('click', removeMenu);
        }, 100);
    }

    // Utility methods
    getConversationId() {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get('conversation') ||
            this.container.dataset.conversationId ||
            null;
    }

    getCurrentUserId() {
        // Get current user ID from global variable or data attribute
        return window.currentUserId ||
            document.body.dataset.userId ||
            null;
    }

    getAuthToken() {
        return localStorage.getItem('auth_token') || '';
    }

    formatMessageTime(timestamp) {
        const now = new Date();
        const diffMs = now - timestamp;
        const diffMinutes = Math.floor(diffMs / (1000 * 60));
        const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

        if (diffMinutes < 1) {
            return 'Just now';
        } else if (diffMinutes < 60) {
            return `${diffMinutes}m ago`;
        } else if (diffHours < 24) {
            return `${diffHours}h ago`;
        } else if (diffDays === 1) {
            return 'Yesterday';
        } else if (diffDays < 7) {
            return timestamp.toLocaleDateString([], { weekday: 'short' });
        } else {
            return timestamp.toLocaleDateString([], { month: 'short', day: 'numeric' });
        }
    }

    throttle(func, limit) {
        let inThrottle;
        return function () {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    // Public methods for external control
    refresh() {
        this.hasMore = true;
        this.oldestMessageId = null;
        this.loadedMessages = 0;
        this.getMessagesContainer().innerHTML = '';
        this.loadInitialMessages();
    }

    addNewMessage(message) {
        this.displayMessages([message], false);
        this.scrollToBottom();
    }

    updateMessage(messageId, updatedMessage) {
        const messageElement = this.container.querySelector(`[data-message-id="${messageId}"]`);
        if (messageElement) {
            const newElement = this.createMessageElement(updatedMessage);
            messageElement.replaceWith(newElement);
        }
    }

    removeMessage(messageId) {
        const messageElement = this.container.querySelector(`[data-message-id="${messageId}"]`);
        if (messageElement) {
            messageElement.remove();
        }
    }
}

// Export for use in other modules
window.InfiniteScroll = InfiniteScroll;