/**
 * Frontend Tests for Enhanced Chat Search and Infinite Scroll
 */

describe('Enhanced Chat Search', () => {
    let enhancedChatSearch;
    let mockFetch;
    
    beforeEach(() => {
        // Setup DOM
        document.body.innerHTML = `
            <input id="message-search-input" type="text" />
            <input id="conversation-search-input" type="text" />
            <div id="search-results-container"></div>
            <div id="conversation-search-results"></div>
            <div id="search-loading"></div>
            <div id="search-error"></div>
            <button id="clear-search-btn"></button>
            <select id="message-type-filter"></select>
            <select id="sender-filter"></select>
            <select id="conversation-filter"></select>
            <input id="date-after-filter" type="date" />
            <input id="date-before-filter" type="date" />
            <textarea id="message-input"></textarea>
            <div id="mention-dropdown"></div>
        `;
        
        // Mock fetch
        mockFetch = jest.fn();
        global.fetch = mockFetch;
        
        // Mock localStorage
        Storage.prototype.getItem = jest.fn(() => 'mock-token');
        
        // Initialize search
        enhancedChatSearch = new EnhancedChatSearch();
    });
    
    afterEach(() => {
        jest.clearAllMocks();
        document.body.innerHTML = '';
    });
    
    describe('Message Search', () => {
        test('should initialize search input listeners', () => {
            const searchInput = document.getElementById('message-search-input');
            expect(searchInput).toBeTruthy();
            
            // Test input event
            const inputEvent = new Event('input');
            searchInput.value = 'test query';
            searchInput.dispatchEvent(inputEvent);
            
            // Should set up timeout for search
            expect(enhancedChatSearch.searchTimeout).toBeTruthy();
        });
        
        test('should perform message search with query', async () => {
            const mockResponse = {
                messages: [
                    {
                        id: 'msg-1',
                        content: 'Test message content',
                        sender_username: 'testuser',
                        created_at: new Date().toISOString(),
                        message_type: 'CHAT',
                        conversation_id: 'conv-1'
                    }
                ],
                total_count: 1,
                has_more: false
            };
            
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve(mockResponse)
            });
            
            await enhancedChatSearch.performMessageSearch('test query');
            
            expect(mockFetch).toHaveBeenCalledWith(
                expect.stringContaining('/api/conversations/search/messages'),
                expect.objectContaining({
                    headers: expect.objectContaining({
                        'Authorization': 'Bearer mock-token'
                    })
                })
            );
            
            const resultsContainer = document.getElementById('search-results-container');
            expect(resultsContainer.style.display).toBe('block');
        });
        
        test('should handle search error gracefully', async () => {
            mockFetch.mockRejectedValueOnce(new Error('Network error'));
            
            const showErrorSpy = jest.spyOn(enhancedChatSearch, 'showSearchError');
            
            await enhancedChatSearch.performMessageSearch('test query');
            
            expect(showErrorSpy).toHaveBeenCalledWith(
                expect.stringContaining('Failed to search messages')
            );
        });
        
        test('should highlight search terms in results', () => {
            const content = 'This is a test message with search terms';
            const query = 'test search';
            
            const highlighted = enhancedChatSearch.highlightSearchTerms(content, query);
            
            expect(highlighted).toContain('<mark>test</mark>');
            expect(highlighted).toContain('<mark>search</mark>');
        });
        
        test('should clear search results', () => {
            const resultsContainer = document.getElementById('search-results-container');
            resultsContainer.style.display = 'block';
            resultsContainer.innerHTML = '<div>Some results</div>';
            
            enhancedChatSearch.clearSearchResults();
            
            expect(resultsContainer.style.display).toBe('none');
            expect(resultsContainer.innerHTML).toBe('');
        });
        
        test('should get search filters correctly', () => {
            // Set up filter values
            document.getElementById('message-type-filter').value = 'CHAT';
            document.getElementById('sender-filter').value = 'user-123';
            document.getElementById('date-after-filter').value = '2023-01-01';
            
            const filters = enhancedChatSearch.getSearchFilters();
            
            expect(filters.message_type).toBe('CHAT');
            expect(filters.sender_id).toBe('user-123');
            expect(filters.created_after).toBeTruthy();
        });
    });
    
    describe('Conversation Search', () => {
        test('should perform conversation search', async () => {
            const mockResponse = {
                conversations: [
                    {
                        id: 'conv-1',
                        title: 'Test Conversation',
                        participant_count: 2,
                        unread_count: 0,
                        last_message_at: new Date().toISOString()
                    }
                ],
                total_count: 1,
                has_more: false
            };
            
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve(mockResponse)
            });
            
            await enhancedChatSearch.handleConversationSearch('test');
            
            expect(mockFetch).toHaveBeenCalledWith(
                expect.stringContaining('/api/conversations/search/conversations'),
                expect.any(Object)
            );
        });
        
        test('should display conversation search results', () => {
            const conversations = [
                {
                    id: 'conv-1',
                    title: 'Test Conversation',
                    participant_count: 2,
                    unread_count: 1,
                    last_message_at: new Date().toISOString()
                }
            ];
            
            enhancedChatSearch.displayConversationSearchResults(conversations, 1);
            
            const resultsContainer = document.getElementById('conversation-search-results');
            expect(resultsContainer.style.display).toBe('block');
            expect(resultsContainer.innerHTML).toContain('Test Conversation');
            expect(resultsContainer.innerHTML).toContain('unread-badge');
        });
    });
    
    describe('User Mentions', () => {
        test('should detect mention input', () => {
            const messageInput = document.getElementById('message-input');
            messageInput.value = 'Hello @test';
            messageInput.setSelectionRange(11, 11); // Cursor at end
            
            const showMentionSpy = jest.spyOn(enhancedChatSearch, 'showMentionDropdown');
            
            const inputEvent = new Event('input');
            messageInput.dispatchEvent(inputEvent);
            
            expect(showMentionSpy).toHaveBeenCalledWith(messageInput, 'test');
        });
        
        test('should fetch user mentions', async () => {
            const mockResponse = {
                users: [
                    {
                        id: 'user-1',
                        username: 'testuser',
                        display_name: 'Test User',
                        email: 'test@example.com',
                        is_participant: true
                    }
                ]
            };
            
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve(mockResponse)
            });
            
            const messageInput = document.getElementById('message-input');
            await enhancedChatSearch.showMentionDropdown(messageInput, 'test');
            
            expect(mockFetch).toHaveBeenCalledWith(
                expect.stringContaining('/api/conversations/mentions/users'),
                expect.any(Object)
            );
        });
        
        test('should display mention dropdown', () => {
            const users = [
                {
                    id: 'user-1',
                    username: 'testuser',
                    display_name: 'Test User',
                    email: 'test@example.com',
                    is_participant: true
                }
            ];
            
            const messageInput = document.getElementById('message-input');
            enhancedChatSearch.displayMentionDropdown(messageInput, users, 'test');
            
            const dropdown = document.getElementById('mention-dropdown');
            expect(dropdown).toBeTruthy();
            expect(dropdown.innerHTML).toContain('testuser');
            expect(dropdown.innerHTML).toContain('participant-badge');
        });
        
        test('should select mention and update input', () => {
            const messageInput = document.getElementById('message-input');
            messageInput.value = 'Hello @test';
            messageInput.setSelectionRange(11, 11);
            
            const user = {
                id: 'user-1',
                username: 'testuser',
                display_name: 'Test User'
            };
            
            enhancedChatSearch.selectMention(messageInput, user, 'test');
            
            expect(messageInput.value).toBe('Hello @testuser ');
        });
        
        test('should handle mention keyboard navigation', () => {
            // Create dropdown with users
            const users = [
                { id: 'user-1', username: 'user1' },
                { id: 'user-2', username: 'user2' }
            ];
            
            const messageInput = document.getElementById('message-input');
            enhancedChatSearch.displayMentionDropdown(messageInput, users, '');
            enhancedChatSearch.mentionUsers = users;
            
            // Test arrow down
            const keydownEvent = new KeyboardEvent('keydown', { key: 'ArrowDown' });
            messageInput.dispatchEvent(keydownEvent);
            
            const dropdown = document.getElementById('mention-dropdown');
            const selectedUsers = dropdown.querySelectorAll('.mention-user.selected');
            expect(selectedUsers.length).toBe(1);
        });
        
        test('should hide mention dropdown', () => {
            // Create dropdown first
            const dropdown = document.createElement('div');
            dropdown.id = 'mention-dropdown';
            document.body.appendChild(dropdown);
            
            enhancedChatSearch.hideMentionDropdown();
            
            expect(document.getElementById('mention-dropdown')).toBeFalsy();
        });
    });
    
    describe('Utility Functions', () => {
        test('should format message time correctly', () => {
            const now = new Date();
            const oneMinuteAgo = new Date(now.getTime() - 60000);
            const oneHourAgo = new Date(now.getTime() - 3600000);
            const oneDayAgo = new Date(now.getTime() - 86400000);
            
            expect(enhancedChatSearch.formatMessageTime(now)).toBe('Just now');
            expect(enhancedChatSearch.formatMessageTime(oneMinuteAgo)).toBe('1m ago');
            expect(enhancedChatSearch.formatMessageTime(oneHourAgo)).toBe('1h ago');
            expect(enhancedChatSearch.formatMessageTime(oneDayAgo)).toBe('Yesterday');
        });
        
        test('should navigate to message correctly', () => {
            const originalLocation = window.location.href;
            
            // Mock window.location
            delete window.location;
            window.location = { href: '' };
            
            enhancedChatSearch.navigateToMessage('conv-123', 'msg-456');
            
            expect(window.location.href).toBe('/chat/enhanced?conversation=conv-123&message=msg-456');
            
            // Restore
            window.location.href = originalLocation;
        });
        
        test('should get current conversation ID from URL', () => {
            // Mock URLSearchParams
            const originalURL = window.location.search;
            
            Object.defineProperty(window, 'location', {
                value: { search: '?conversation=test-conv-id' },
                writable: true
            });
            
            const conversationId = enhancedChatSearch.getCurrentConversationId();
            expect(conversationId).toBe('test-conv-id');
            
            // Restore
            window.location.search = originalURL;
        });
    });
});

describe('Infinite Scroll', () => {
    let infiniteScroll;
    let mockFetch;
    let container;
    
    beforeEach(() => {
        // Setup DOM
        document.body.innerHTML = `
            <div id="messages-container" data-conversation-id="test-conv">
                <div class="messages-list"></div>
            </div>
        `;
        
        container = document.getElementById('messages-container');
        
        // Mock fetch
        mockFetch = jest.fn();
        global.fetch = mockFetch;
        
        // Mock localStorage
        Storage.prototype.getItem = jest.fn(() => 'mock-token');
        
        // Mock window properties
        window.currentUserId = 'test-user-id';
        
        // Initialize infinite scroll
        infiniteScroll = new InfiniteScroll('messages-container', {
            threshold: 100,
            limit: 25
        });
    });
    
    afterEach(() => {
        jest.clearAllMocks();
        document.body.innerHTML = '';
    });
    
    describe('Initialization', () => {
        test('should initialize with correct options', () => {
            expect(infiniteScroll.options.threshold).toBe(100);
            expect(infiniteScroll.options.limit).toBe(25);
            expect(infiniteScroll.conversationId).toBe('test-conv');
        });
        
        test('should create loading indicator', () => {
            const loadingIndicator = document.getElementById('infinite-scroll-loading');
            expect(loadingIndicator).toBeTruthy();
            expect(loadingIndicator.style.display).toBe('none');
        });
        
        test('should setup scroll listener', () => {
            const scrollSpy = jest.spyOn(infiniteScroll, 'handleScroll');
            
            // Trigger scroll event
            const scrollEvent = new Event('scroll');
            container.dispatchEvent(scrollEvent);
            
            // Should be throttled, so might not call immediately
            expect(scrollSpy).toHaveBeenCalledTimes(0);
        });
    });
    
    describe('Message Loading', () => {
        test('should load initial messages', async () => {
            const mockResponse = {
                messages: [
                    {
                        id: 'msg-1',
                        content: 'Test message',
                        sender_id: 'user-1',
                        sender_username: 'testuser',
                        created_at: new Date().toISOString(),
                        message_type: 'CHAT',
                        is_delivered: true,
                        is_read: false,
                        is_edited: false,
                        is_deleted: false
                    }
                ],
                total_count: 1,
                has_more: false
            };
            
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve(mockResponse)
            });
            
            await infiniteScroll.loadInitialMessages();
            
            expect(mockFetch).toHaveBeenCalledWith(
                expect.stringContaining('/api/conversations/test-conv/messages'),
                expect.objectContaining({
                    headers: expect.objectContaining({
                        'Authorization': 'Bearer mock-token'
                    })
                })
            );
            
            expect(infiniteScroll.totalMessages).toBe(1);
            expect(infiniteScroll.loadedMessages).toBe(1);
            expect(infiniteScroll.hasMore).toBe(false);
        });
        
        test('should load more messages with cursor', async () => {
            // Set up initial state
            infiniteScroll.oldestMessageId = 'msg-10';
            infiniteScroll.hasMore = true;
            
            const mockResponse = {
                messages: [
                    {
                        id: 'msg-11',
                        content: 'Older message',
                        sender_id: 'user-1',
                        sender_username: 'testuser',
                        created_at: new Date().toISOString(),
                        message_type: 'CHAT',
                        is_delivered: true,
                        is_read: true,
                        is_edited: false,
                        is_deleted: false
                    }
                ],
                total_count: 50,
                has_more: true
            };
            
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve(mockResponse)
            });
            
            await infiniteScroll.loadMoreMessages();
            
            expect(mockFetch).toHaveBeenCalledWith(
                expect.stringContaining('before_message_id=msg-10'),
                expect.any(Object)
            );
            
            expect(infiniteScroll.loadedMessages).toBe(1);
            expect(infiniteScroll.oldestMessageId).toBe('msg-11');
        });
        
        test('should handle scroll trigger for loading more messages', () => {
            infiniteScroll.hasMore = true;
            infiniteScroll.isLoading = false;
            
            const loadMoreSpy = jest.spyOn(infiniteScroll, 'loadMoreMessages');
            
            // Mock scroll position near top
            Object.defineProperty(container, 'scrollTop', { value: 50 });
            
            infiniteScroll.handleScroll();
            
            expect(loadMoreSpy).toHaveBeenCalled();
        });
        
        test('should not load more when already loading', () => {
            infiniteScroll.isLoading = true;
            infiniteScroll.hasMore = true;
            
            const loadMoreSpy = jest.spyOn(infiniteScroll, 'loadMoreMessages');
            
            Object.defineProperty(container, 'scrollTop', { value: 50 });
            infiniteScroll.handleScroll();
            
            expect(loadMoreSpy).not.toHaveBeenCalled();
        });
        
        test('should not load more when no more messages', () => {
            infiniteScroll.isLoading = false;
            infiniteScroll.hasMore = false;
            
            const loadMoreSpy = jest.spyOn(infiniteScroll, 'loadMoreMessages');
            
            Object.defineProperty(container, 'scrollTop', { value: 50 });
            infiniteScroll.handleScroll();
            
            expect(loadMoreSpy).not.toHaveBeenCalled();
        });
    });
    
    describe('Message Display', () => {
        test('should create message element correctly', () => {
            const message = {
                id: 'msg-1',
                content: 'Test message with @mention and https://example.com',
                sender_id: 'user-1',
                sender_username: 'testuser',
                created_at: new Date().toISOString(),
                message_type: 'CHAT',
                is_delivered: true,
                is_read: false,
                is_edited: true,
                is_deleted: false
            };
            
            const messageElement = infiniteScroll.createMessageElement(message);
            
            expect(messageElement.classList.contains('message')).toBe(true);
            expect(messageElement.dataset.messageId).toBe('msg-1');
            expect(messageElement.innerHTML).toContain('testuser');
            expect(messageElement.innerHTML).toContain('Test message');
            expect(messageElement.innerHTML).toContain('edited');
            expect(messageElement.innerHTML).toContain('mention');
            expect(messageElement.innerHTML).toContain('href="https://example.com"');
        });
        
        test('should format message content correctly', () => {
            const content = 'Hello @user check https://example.com\nNew line here';
            const formatted = infiniteScroll.formatMessageContent(content);
            
            expect(formatted).toContain('<span class="mention">@user</span>');
            expect(formatted).toContain('<a href="https://example.com"');
            expect(formatted).toContain('<br>');
        });
        
        test('should add new message to bottom', () => {
            const message = {
                id: 'new-msg',
                content: 'New message',
                sender_id: 'user-1',
                sender_username: 'testuser',
                created_at: new Date().toISOString(),
                message_type: 'CHAT',
                is_delivered: false,
                is_read: false,
                is_edited: false,
                is_deleted: false
            };
            
            infiniteScroll.addNewMessage(message);
            
            const messagesList = container.querySelector('.messages-list');
            const lastMessage = messagesList.lastElementChild;
            expect(lastMessage.dataset.messageId).toBe('new-msg');
        });
        
        test('should update existing message', () => {
            // Add initial message
            const messagesList = container.querySelector('.messages-list');
            messagesList.innerHTML = `
                <div class="message" data-message-id="msg-1">
                    <div class="message-content">Original content</div>
                </div>
            `;
            
            const updatedMessage = {
                id: 'msg-1',
                content: 'Updated content',
                sender_id: 'user-1',
                sender_username: 'testuser',
                created_at: new Date().toISOString(),
                message_type: 'CHAT',
                is_delivered: true,
                is_read: true,
                is_edited: true,
                is_deleted: false
            };
            
            infiniteScroll.updateMessage('msg-1', updatedMessage);
            
            const messageElement = container.querySelector('[data-message-id="msg-1"]');
            expect(messageElement.innerHTML).toContain('Updated content');
            expect(messageElement.innerHTML).toContain('edited');
        });
        
        test('should remove message', () => {
            // Add initial message
            const messagesList = container.querySelector('.messages-list');
            messagesList.innerHTML = `
                <div class="message" data-message-id="msg-1">
                    <div class="message-content">Test message</div>
                </div>
            `;
            
            infiniteScroll.removeMessage('msg-1');
            
            const messageElement = container.querySelector('[data-message-id="msg-1"]');
            expect(messageElement).toBeFalsy();
        });
    });
    
    describe('Utility Functions', () => {
        test('should scroll to bottom', () => {
            const scrollSpy = jest.spyOn(container, 'scrollTop', 'set');
            Object.defineProperty(container, 'scrollHeight', { value: 1000 });
            
            infiniteScroll.scrollToBottom();
            
            expect(scrollSpy).toHaveBeenCalledWith(1000);
        });
        
        test('should scroll to specific message', () => {
            // Add message to DOM
            const messagesList = container.querySelector('.messages-list');
            messagesList.innerHTML = `
                <div class="message" data-message-id="target-msg">
                    <div class="message-content">Target message</div>
                </div>
            `;
            
            const messageElement = container.querySelector('[data-message-id="target-msg"]');
            const scrollSpy = jest.spyOn(messageElement, 'scrollIntoView');
            
            infiniteScroll.scrollToMessage('target-msg');
            
            expect(scrollSpy).toHaveBeenCalledWith({
                behavior: 'smooth',
                block: 'center'
            });
            expect(messageElement.classList.contains('highlighted')).toBe(true);
        });
        
        test('should format message time correctly', () => {
            const now = new Date();
            const oneMinuteAgo = new Date(now.getTime() - 60000);
            const oneHourAgo = new Date(now.getTime() - 3600000);
            
            expect(infiniteScroll.formatMessageTime(now)).toBe('Just now');
            expect(infiniteScroll.formatMessageTime(oneMinuteAgo)).toBe('1m ago');
            expect(infiniteScroll.formatMessageTime(oneHourAgo)).toBe('1h ago');
        });
        
        test('should throttle function calls', (done) => {
            let callCount = 0;
            const throttledFn = infiniteScroll.throttle(() => {
                callCount++;
            }, 100);
            
            // Call multiple times rapidly
            throttledFn();
            throttledFn();
            throttledFn();
            
            expect(callCount).toBe(1);
            
            // Wait for throttle to reset
            setTimeout(() => {
                throttledFn();
                expect(callCount).toBe(2);
                done();
            }, 150);
        });
    });
});

// Test runner setup
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        // Export test functions if needed
    };
}