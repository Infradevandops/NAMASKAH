/**
 * Enhanced Chat Search and Infinite Scroll Functionality
 * Handles message search, conversation search, and user mentions
 */

class EnhancedChatSearch {
    constructor() {
        this.searchTimeout = null;
        this.searchDelay = 300; // ms
        this.currentSearchQuery = '';
        this.searchResults = [];
        this.isSearching = false;
        this.mentionUsers = [];
        this.mentionTimeout = null;
        
        this.initializeSearch();
        this.initializeMentions();
    }
    
    initializeSearch() {
        // Message search functionality
        const messageSearchInput = document.getElementById('message-search-input');
        const conversationSearchInput = document.getElementById('conversation-search-input');
        
        if (messageSearchInput) {
            messageSearchInput.addEventListener('input', (e) => {
                this.handleMessageSearch(e.target.value);
            });
            
            messageSearchInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.performMessageSearch(e.target.value);
                }
            });
        }
        
        if (conversationSearchInput) {
            conversationSearchInput.addEventListener('input', (e) => {
                this.handleConversationSearch(e.target.value);
            });
        }
        
        // Search filters
        this.initializeSearchFilters();
        
        // Clear search functionality
        const clearSearchBtn = document.getElementById('clear-search-btn');
        if (clearSearchBtn) {
            clearSearchBtn.addEventListener('click', () => {
                this.clearSearch();
            });
        }
    }
    
    initializeSearchFilters() {
        const filterElements = document.querySelectorAll('.search-filter');
        filterElements.forEach(filter => {
            filter.addEventListener('change', () => {
                if (this.currentSearchQuery) {
                    this.performMessageSearch(this.currentSearchQuery);
                }
            });
        });
    }
    
    handleMessageSearch(query) {
        clearTimeout(this.searchTimeout);
        this.currentSearchQuery = query.trim();
        
        if (this.currentSearchQuery.length === 0) {
            this.clearSearchResults();
            return;
        }
        
        if (this.currentSearchQuery.length < 2) {
            return; // Wait for at least 2 characters
        }
        
        this.searchTimeout = setTimeout(() => {
            this.performMessageSearch(this.currentSearchQuery);
        }, this.searchDelay);
    }
    
    async performMessageSearch(query) {
        if (this.isSearching) return;
        
        this.isSearching = true;
        this.showSearchLoading();
        
        try {
            const filters = this.getSearchFilters();
            const params = new URLSearchParams({
                query: query,
                limit: '50',
                offset: '0',
                ...filters
            });
            
            const response = await fetch(`/api/conversations/search/messages?${params}`, {
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`Search failed: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.displaySearchResults(data.messages, data.total_count, data.has_more);
            
        } catch (error) {
            console.error('Message search error:', error);
            this.showSearchError('Failed to search messages. Please try again.');
        } finally {
            this.isSearching = false;
            this.hideSearchLoading();
        }
    }
    
    async handleConversationSearch(query) {
        clearTimeout(this.searchTimeout);
        
        if (query.trim().length === 0) {
            this.clearConversationSearchResults();
            return;
        }
        
        if (query.trim().length < 2) {
            return;
        }
        
        this.searchTimeout = setTimeout(async () => {
            try {
                const params = new URLSearchParams({
                    query: query.trim(),
                    limit: '20',
                    offset: '0'
                });
                
                const response = await fetch(`/api/conversations/search/conversations?${params}`, {
                    headers: {
                        'Authorization': `Bearer ${this.getAuthToken()}`,
                        'Content-Type': 'application/json'
                    }
                });
                
                if (!response.ok) {
                    throw new Error(`Conversation search failed: ${response.statusText}`);
                }
                
                const data = await response.json();
                this.displayConversationSearchResults(data.conversations, data.total_count);
                
            } catch (error) {
                console.error('Conversation search error:', error);
                this.showSearchError('Failed to search conversations. Please try again.');
            }
        }, this.searchDelay);
    }
    
    getSearchFilters() {
        const filters = {};
        
        const messageTypeFilter = document.getElementById('message-type-filter');
        if (messageTypeFilter && messageTypeFilter.value) {
            filters.message_type = messageTypeFilter.value;
        }
        
        const senderFilter = document.getElementById('sender-filter');
        if (senderFilter && senderFilter.value) {
            filters.sender_id = senderFilter.value;
        }
        
        const conversationFilter = document.getElementById('conversation-filter');
        if (conversationFilter && conversationFilter.value) {
            filters.conversation_id = conversationFilter.value;
        }
        
        const dateAfterFilter = document.getElementById('date-after-filter');
        if (dateAfterFilter && dateAfterFilter.value) {
            filters.created_after = new Date(dateAfterFilter.value).toISOString();
        }
        
        const dateBeforeFilter = document.getElementById('date-before-filter');
        if (dateBeforeFilter && dateBeforeFilter.value) {
            filters.created_before = new Date(dateBeforeFilter.value).toISOString();
        }
        
        return filters;
    }
    
    displaySearchResults(messages, totalCount, hasMore) {
        const resultsContainer = document.getElementById('search-results-container');
        if (!resultsContainer) return;
        
        resultsContainer.innerHTML = '';
        
        if (messages.length === 0) {
            resultsContainer.innerHTML = `
                <div class="no-results">
                    <i class="fas fa-search"></i>
                    <p>No messages found for "${this.currentSearchQuery}"</p>
                </div>
            `;
            return;
        }
        
        // Results header
        const header = document.createElement('div');
        header.className = 'search-results-header';
        header.innerHTML = `
            <h3>Search Results</h3>
            <span class="results-count">${totalCount} message${totalCount !== 1 ? 's' : ''} found</span>
        `;
        resultsContainer.appendChild(header);
        
        // Results list
        const resultsList = document.createElement('div');
        resultsList.className = 'search-results-list';
        
        messages.forEach(message => {
            const messageElement = this.createSearchResultElement(message);
            resultsList.appendChild(messageElement);
        });
        
        resultsContainer.appendChild(resultsList);
        
        // Load more button if needed
        if (hasMore) {
            const loadMoreBtn = document.createElement('button');
            loadMoreBtn.className = 'load-more-btn';
            loadMoreBtn.textContent = 'Load More Results';
            loadMoreBtn.onclick = () => this.loadMoreSearchResults();
            resultsContainer.appendChild(loadMoreBtn);
        }
        
        // Show results container
        resultsContainer.style.display = 'block';
    }
    
    createSearchResultElement(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'search-result-item';
        messageDiv.onclick = () => this.navigateToMessage(message.conversation_id, message.id);
        
        // Highlight search terms in content
        const highlightedContent = this.highlightSearchTerms(message.content, this.currentSearchQuery);
        
        messageDiv.innerHTML = `
            <div class="search-result-header">
                <span class="sender-name">${message.sender_username || 'Unknown'}</span>
                <span class="message-time">${this.formatMessageTime(message.created_at)}</span>
                <span class="message-type ${message.message_type}">${message.message_type}</span>
            </div>
            <div class="search-result-content">${highlightedContent}</div>
            <div class="search-result-meta">
                <span class="conversation-indicator">
                    <i class="fas fa-comments"></i>
                    Conversation
                </span>
            </div>
        `;
        
        return messageDiv;
    }
    
    highlightSearchTerms(content, query) {
        if (!query) return content;
        
        const words = query.split(' ').filter(word => word.length >= 2);
        let highlightedContent = content;
        
        words.forEach(word => {
            const regex = new RegExp(`(${word})`, 'gi');
            highlightedContent = highlightedContent.replace(regex, '<mark>$1</mark>');
        });
        
        return highlightedContent;
    }
    
    displayConversationSearchResults(conversations, totalCount) {
        const resultsContainer = document.getElementById('conversation-search-results');
        if (!resultsContainer) return;
        
        resultsContainer.innerHTML = '';
        
        if (conversations.length === 0) {
            resultsContainer.innerHTML = `
                <div class="no-results">
                    <p>No conversations found</p>
                </div>
            `;
            return;
        }
        
        conversations.forEach(conversation => {
            const convElement = document.createElement('div');
            convElement.className = 'conversation-search-result';
            convElement.onclick = () => this.selectConversation(conversation.id);
            
            convElement.innerHTML = `
                <div class="conversation-info">
                    <h4>${conversation.title || 'Untitled Conversation'}</h4>
                    <p>${conversation.participant_count} participant${conversation.participant_count !== 1 ? 's' : ''}</p>
                    ${conversation.unread_count > 0 ? `<span class="unread-badge">${conversation.unread_count}</span>` : ''}
                </div>
                <div class="conversation-meta">
                    <span class="last-message-time">${this.formatMessageTime(conversation.last_message_at)}</span>
                </div>
            `;
            
            resultsContainer.appendChild(convElement);
        });
        
        resultsContainer.style.display = 'block';
    }
    
    // User mentions functionality
    initializeMentions() {
        const messageInput = document.getElementById('message-input');
        if (!messageInput) return;
        
        messageInput.addEventListener('input', (e) => {
            this.handleMentionInput(e);
        });
        
        messageInput.addEventListener('keydown', (e) => {
            this.handleMentionKeydown(e);
        });
        
        // Click outside to close mentions
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.mention-dropdown') && !e.target.closest('#message-input')) {
                this.hideMentionDropdown();
            }
        });
    }
    
    handleMentionInput(event) {
        const input = event.target;
        const cursorPosition = input.selectionStart;
        const textBeforeCursor = input.value.substring(0, cursorPosition);
        
        // Check if we're typing a mention (@ symbol)
        const mentionMatch = textBeforeCursor.match(/@(\w*)$/);
        
        if (mentionMatch) {
            const query = mentionMatch[1];
            this.showMentionDropdown(input, query);
        } else {
            this.hideMentionDropdown();
        }
    }
    
    async showMentionDropdown(input, query) {
        clearTimeout(this.mentionTimeout);
        
        this.mentionTimeout = setTimeout(async () => {
            try {
                const conversationId = this.getCurrentConversationId();
                const params = new URLSearchParams({
                    query: query,
                    limit: '10'
                });
                
                if (conversationId) {
                    params.append('conversation_id', conversationId);
                }
                
                const response = await fetch(`/api/conversations/mentions/users?${params}`, {
                    headers: {
                        'Authorization': `Bearer ${this.getAuthToken()}`,
                        'Content-Type': 'application/json'
                    }
                });
                
                if (!response.ok) {
                    throw new Error(`Mention search failed: ${response.statusText}`);
                }
                
                const data = await response.json();
                this.displayMentionDropdown(input, data.users, query);
                
            } catch (error) {
                console.error('Mention search error:', error);
            }
        }, 200);
    }
    
    displayMentionDropdown(input, users, query) {
        // Remove existing dropdown
        this.hideMentionDropdown();
        
        if (users.length === 0) return;
        
        const dropdown = document.createElement('div');
        dropdown.className = 'mention-dropdown';
        dropdown.id = 'mention-dropdown';
        
        users.forEach((user, index) => {
            const userElement = document.createElement('div');
            userElement.className = 'mention-user';
            if (index === 0) userElement.classList.add('selected');
            
            userElement.innerHTML = `
                <div class="user-avatar">
                    <i class="fas fa-user"></i>
                </div>
                <div class="user-info">
                    <div class="user-name">${user.display_name}</div>
                    <div class="user-username">@${user.username}</div>
                </div>
                ${user.is_participant ? '<span class="participant-badge">Participant</span>' : ''}
            `;
            
            userElement.onclick = () => this.selectMention(input, user, query);
            dropdown.appendChild(userElement);
        });
        
        // Position dropdown
        const inputRect = input.getBoundingClientRect();
        dropdown.style.position = 'absolute';
        dropdown.style.top = `${inputRect.bottom + window.scrollY}px`;
        dropdown.style.left = `${inputRect.left + window.scrollX}px`;
        dropdown.style.minWidth = `${inputRect.width}px`;
        
        document.body.appendChild(dropdown);
        this.mentionUsers = users;
    }
    
    handleMentionKeydown(event) {
        const dropdown = document.getElementById('mention-dropdown');
        if (!dropdown) return;
        
        const selectedUser = dropdown.querySelector('.mention-user.selected');
        
        switch (event.key) {
            case 'ArrowDown':
                event.preventDefault();
                this.selectNextMentionUser(1);
                break;
            case 'ArrowUp':
                event.preventDefault();
                this.selectNextMentionUser(-1);
                break;
            case 'Enter':
            case 'Tab':
                event.preventDefault();
                if (selectedUser) {
                    const userIndex = Array.from(dropdown.children).indexOf(selectedUser);
                    this.selectMention(event.target, this.mentionUsers[userIndex], '');
                }
                break;
            case 'Escape':
                this.hideMentionDropdown();
                break;
        }
    }
    
    selectNextMentionUser(direction) {
        const dropdown = document.getElementById('mention-dropdown');
        if (!dropdown) return;
        
        const users = dropdown.querySelectorAll('.mention-user');
        const currentSelected = dropdown.querySelector('.mention-user.selected');
        
        if (!currentSelected) return;
        
        const currentIndex = Array.from(users).indexOf(currentSelected);
        let newIndex = currentIndex + direction;
        
        if (newIndex < 0) newIndex = users.length - 1;
        if (newIndex >= users.length) newIndex = 0;
        
        currentSelected.classList.remove('selected');
        users[newIndex].classList.add('selected');
    }
    
    selectMention(input, user, query) {
        const cursorPosition = input.selectionStart;
        const textBeforeCursor = input.value.substring(0, cursorPosition);
        const textAfterCursor = input.value.substring(cursorPosition);
        
        // Replace the @query with @username
        const mentionText = `@${user.username} `;
        const beforeMention = textBeforeCursor.replace(/@\w*$/, '');
        
        input.value = beforeMention + mentionText + textAfterCursor;
        
        // Set cursor position after the mention
        const newCursorPosition = beforeMention.length + mentionText.length;
        input.setSelectionRange(newCursorPosition, newCursorPosition);
        
        this.hideMentionDropdown();
        input.focus();
    }
    
    hideMentionDropdown() {
        const dropdown = document.getElementById('mention-dropdown');
        if (dropdown) {
            dropdown.remove();
        }
        this.mentionUsers = [];
    }
    
    // Utility methods
    navigateToMessage(conversationId, messageId) {
        // Navigate to the conversation and highlight the message
        window.location.href = `/chat/enhanced?conversation=${conversationId}&message=${messageId}`;
    }
    
    selectConversation(conversationId) {
        // Navigate to the conversation
        window.location.href = `/chat/enhanced?conversation=${conversationId}`;
    }
    
    getCurrentConversationId() {
        // Get current conversation ID from URL or context
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get('conversation');
    }
    
    clearSearch() {
        this.currentSearchQuery = '';
        const searchInput = document.getElementById('message-search-input');
        if (searchInput) {
            searchInput.value = '';
        }
        this.clearSearchResults();
    }
    
    clearSearchResults() {
        const resultsContainer = document.getElementById('search-results-container');
        if (resultsContainer) {
            resultsContainer.style.display = 'none';
            resultsContainer.innerHTML = '';
        }
    }
    
    clearConversationSearchResults() {
        const resultsContainer = document.getElementById('conversation-search-results');
        if (resultsContainer) {
            resultsContainer.style.display = 'none';
            resultsContainer.innerHTML = '';
        }
    }
    
    showSearchLoading() {
        const loadingElement = document.getElementById('search-loading');
        if (loadingElement) {
            loadingElement.style.display = 'block';
        }
    }
    
    hideSearchLoading() {
        const loadingElement = document.getElementById('search-loading');
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }
    }
    
    showSearchError(message) {
        const errorElement = document.getElementById('search-error');
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.style.display = 'block';
            setTimeout(() => {
                errorElement.style.display = 'none';
            }, 5000);
        }
    }
    
    formatMessageTime(timestamp) {
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
    
    getAuthToken() {
        // Get JWT token from localStorage or cookie
        return localStorage.getItem('auth_token') || '';
    }
    
    async loadMoreSearchResults() {
        // Implementation for loading more search results
        // This would increment the offset and append new results
        console.log('Loading more search results...');
    }
}

// Initialize enhanced chat search when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.enhancedChatSearch = new EnhancedChatSearch();
});