// Classic Verification Flow - Simplified and Clean
let currentVerification = null;
let verificationTimer = null;
let selectedService = null;
let selectedType = 'sms';

// Service icons mapping
const serviceIcons = {
    'whatsapp': '📱',
    'telegram': '✈️',
    'discord': '🎮',
    'google': '🔍',
    'instagram': '📷',
    'facebook': '👥',
    'twitter': '🐦',
    'tiktok': '🎵',
    'snapchat': '👻',
    'gmail': '📧',
    'paypal': '💰',
    'cashapp': '💸',
    'venmo': '💳',
    'uber': '🚗',
    'lyft': '🚕',
    'airbnb': '🏠',
    'default': '📱'
};

// Service pricing tiers
const serviceTiers = {
    'tier1': { services: ['whatsapp', 'telegram', 'discord', 'google'], price: 0.75, label: 'HIGH-DEMAND' },
    'tier2': { services: ['instagram', 'facebook', 'twitter', 'tiktok'], price: 1.00, label: 'STANDARD' },
    'tier3': { services: ['paypal', 'venmo', 'cashapp'], price: 1.50, label: 'PREMIUM' },
    'tier4': { services: [], price: 2.00, label: 'SPECIALTY' }
};

function getServiceTier(serviceName) {
    for (const [tier, data] of Object.entries(serviceTiers)) {
        if (data.services.includes(serviceName.toLowerCase())) {
            return data;
        }
    }
    return serviceTiers.tier4;
}

function getServiceIcon(serviceName) {
    return serviceIcons[serviceName.toLowerCase()] || serviceIcons.default;
}

// Initialize classic verification UI
function initClassicVerification() {
    if (document.getElementById('services-grid-classic')) {
        loadServicesClassic();
        setupEventListeners();
    }
}

// Load and render services in classic grid
async function loadServicesClassic() {
    try {
        const response = await fetch(`${API_BASE}/services/list`);
        if (!response.ok) throw new Error('Failed to load services');
        
        const data = await response.json();
        renderServicesClassic(data);
    } catch (error) {
        console.error('Error loading services:', error);
        if (typeof showNotification === 'function') {
            showNotification('Failed to load services', 'error');
        }
    }
}

function renderServicesClassic(servicesData) {
    const container = document.getElementById('services-grid-classic');
    if (!container) return;
    
    const searchInput = document.getElementById('service-search-classic');
    const categorySelect = document.getElementById('category-filter-classic');
    
    const searchTerm = searchInput ? searchInput.value.toLowerCase() : '';
    const categoryFilter = categorySelect ? categorySelect.value : '';
    
    let allServices = [];
    
    // Collect all services from categories
    if (servicesData.categories) {
        Object.entries(servicesData.categories).forEach(([category, services]) => {
            if (!categoryFilter || categoryFilter === category) {
                services.forEach(service => {
                    if (!searchTerm || service.toLowerCase().includes(searchTerm)) {
                        allServices.push({ name: service, category });
                    }
                });
            }
        });
    }
    
    // Sort services by tier (lower price first)
    allServices.sort((a, b) => {
        const tierA = getServiceTier(a.name);
        const tierB = getServiceTier(b.name);
        return tierA.price - tierB.price;
    });
    
    // Render services
    container.innerHTML = allServices.map(service => {
        const tier = getServiceTier(service.name);
        const icon = getServiceIcon(service.name);
        
        return `
            <div class="service-item-classic" onclick="selectServiceClassic('${service.name}')" data-service="${service.name}">
                <div class="service-icon">${icon}</div>
                <div class="service-name">${formatServiceName(service.name)}</div>
                <div class="service-price">N${tier.price.toFixed(2)}</div>
            </div>
        `;
    }).join('') || '<div style="grid-column: 1/-1; text-align: center; color: var(--text-secondary); padding: 20px;">No services found</div>';
}

function selectServiceClassic(serviceName) {
    selectedService = serviceName;
    selectedType = 'sms'; // Default to SMS
    
    // Update UI selection
    document.querySelectorAll('.service-item-classic').forEach(item => {
        item.classList.remove('selected');
    });
    const serviceElement = document.querySelector(`[data-service="${serviceName}"]`);
    if (serviceElement) {
        serviceElement.classList.add('selected');
    }
    
    // Show service selected info
    const serviceInfo = document.getElementById('service-selected-info');
    if (serviceInfo) {
        serviceInfo.classList.remove('hidden');
        
        // Update service name and price using local tier data
        const tier = getServiceTier(serviceName);
        const smsPrice = tier.price;
        const voicePrice = tier.price + 0.30;
        
        document.getElementById('selected-service-name').textContent = formatServiceName(serviceName);
        document.getElementById('selected-service-price').textContent = `N${smsPrice.toFixed(2)}`;
        
        // Update modal prices
        const smsModal = document.getElementById('sms-price-modal');
        const voiceModal = document.getElementById('voice-price-modal');
        if (smsModal) smsModal.textContent = `N${smsPrice.toFixed(2)}`;
        if (voiceModal) voiceModal.textContent = `N${voicePrice.toFixed(2)}`;
    }
    
    // Enable create button
    const createBtn = document.getElementById('create-verification-classic');
    if (createBtn) {
        createBtn.disabled = false;
    }
}

function showVerificationOptions() {
    const modal = document.getElementById('verification-options-modal');
    if (modal) {
        modal.classList.remove('hidden');
    }
}

function closeVerificationOptions() {
    const modal = document.getElementById('verification-options-modal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

function selectVerificationTypeAndClose(type) {
    selectedType = type;
    
    // Update the main button text and price
    const createBtn = document.getElementById('create-verification-classic');
    const priceElement = document.getElementById('selected-service-price');
    
    if (selectedService && createBtn && priceElement) {
        const tier = getServiceTier(selectedService);
        const price = type === 'voice' ? tier.price + 0.30 : tier.price;
        
        createBtn.innerHTML = type === 'voice' ? '📞 Create Voice Verification' : '📱 Create SMS Verification';
        priceElement.textContent = `N${price.toFixed(2)}`;
    }
    
    closeVerificationOptions();
}

// Create verification with classic flow
async function createVerificationClassic() {
    if (!selectedService) {
        if (typeof showNotification === 'function') {
            showNotification('Please select a service first', 'error');
        }
        return;
    }
    
    if (!window.token) {
        if (typeof showNotification === 'function') {
            showNotification('Please login first', 'error');
        }
        return;
    }
    
    const createBtn = document.getElementById('create-verification-classic');
    if (createBtn) {
        createBtn.disabled = true;
        createBtn.innerHTML = '<div class="loading-spinner"></div> Creating...';
    }
    
    try {
        const response = await fetch(`${API_BASE}/verify/create`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${window.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                service_name: selectedService,
                capability: selectedType
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentVerification = data;
            showVerificationStatusClassic(data);
            startVerificationTimerClassic();
            
            // Update user credits
            const creditsElement = document.getElementById('user-credits');
            if (creditsElement && data.remaining_credits !== undefined) {
                creditsElement.textContent = data.remaining_credits.toFixed(2);
            }
            
            if (typeof showNotification === 'function') {
                showNotification(`Verification created! Phone: ${formatPhoneNumber(data.phone_number)}`, 'success');
            }
        } else {
            throw new Error(data.detail || 'Failed to create verification');
        }
    } catch (error) {
        console.error('Error creating verification:', error);
        if (typeof showNotification === 'function') {
            showNotification(error.message, 'error');
        }
    } finally {
        if (createBtn) {
            createBtn.disabled = false;
            createBtn.innerHTML = 'Create Verification';
        }
    }
}

// Show verification status in classic layout
function showVerificationStatusClassic(verification) {
    // Hide service selection
    const serviceSelection = document.getElementById('service-selection-classic');
    if (serviceSelection) {
        serviceSelection.classList.add('hidden');
    }
    
    // Show verification status
    const statusContainer = document.getElementById('verification-status-classic');
    if (statusContainer) {
        statusContainer.classList.remove('hidden');
    }
    
    // Update status display
    const phoneElement = document.getElementById('phone-number-classic');
    const serviceElement = document.getElementById('service-name-classic');
    const statusBadge = document.getElementById('status-badge-classic');
    
    if (phoneElement) phoneElement.textContent = formatPhoneNumber(verification.phone_number);
    if (serviceElement) serviceElement.textContent = formatServiceName(verification.service_name);
    
    if (statusBadge) {
        statusBadge.textContent = verification.status;
        statusBadge.className = `status-badge-classic ${verification.status}`;
    }
    
    // Show timer for pending verifications
    if (verification.status === 'pending') {
        const timerDisplay = document.getElementById('timer-display-classic');
        if (timerDisplay) {
            timerDisplay.classList.remove('hidden');
        }
    }
}

// Start verification timer
function startVerificationTimerClassic() {
    let timeLeft = 120; // 2 minutes
    const timerElement = document.getElementById('timer-countdown-classic');
    
    function updateTimer() {
        const minutes = Math.floor(timeLeft / 60);
        const seconds = timeLeft % 60;
        if (timerElement) {
            timerElement.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        }
        
        if (timeLeft <= 0) {
            clearInterval(verificationTimer);
            checkVerificationStatusClassic();
        } else {
            timeLeft--;
        }
    }
    
    updateTimer();
    verificationTimer = setInterval(updateTimer, 1000);
    
    // Auto-check for messages every 10 seconds
    const autoCheck = setInterval(async () => {
        if (currentVerification && currentVerification.status === 'pending') {
            await checkMessagesClassic(true);
        } else {
            clearInterval(autoCheck);
        }
    }, 10000);
}

// Check for messages
async function checkMessagesClassic(silent = false) {
    if (!currentVerification) return;
    
    try {
        const response = await fetch(`${API_BASE}/verify/${currentVerification.id}/messages`, {
            headers: { 'Authorization': `Bearer ${window.token}` }
        });
        
        if (response.ok) {
            const data = await response.json();
            
            if (data.messages && data.messages.length > 0) {
                showMessagesClassic(data.messages);
                clearInterval(verificationTimer);
                const timerDisplay = document.getElementById('timer-display-classic');
                if (timerDisplay) {
                    timerDisplay.classList.add('hidden');
                }
                
                if (!silent && typeof showNotification === 'function') {
                    showNotification('SMS received!', 'success');
                }
            } else if (!silent && typeof showNotification === 'function') {
                showNotification('No messages yet', 'info');
            }
        }
    } catch (error) {
        if (!silent) {
            console.error('Error checking messages:', error);
            if (typeof showNotification === 'function') {
                showNotification('Failed to check messages', 'error');
            }
        }
    }
}

// Show messages in classic layout
function showMessagesClassic(messages) {
    const messagesContainer = document.getElementById('messages-display-classic');
    if (messagesContainer) {
        messagesContainer.classList.remove('hidden');
    }
    
    const messagesList = document.getElementById('messages-list-classic');
    if (messagesList) {
        messagesList.innerHTML = messages.map(message => {
            const codeMatch = message.match(/\b\d{4,8}\b/);
            const code = codeMatch ? codeMatch[0] : message;
            
            return `
                <div class="message-success">
                    <div style="text-align: center; margin-bottom: 16px;">
                        <div style="font-size: 18px; font-weight: 600; color: #065f46; margin-bottom: 8px;">Verification Code Received</div>
                        <div class="message-code">${code}</div>
                        <button onclick="copyToClipboard('${code}')" class="action-btn-classic action-btn-primary" style="margin-top: 12px;">
                            📋 Copy Code
                        </button>
                    </div>
                    <details style="margin-top: 12px;">
                        <summary style="cursor: pointer; color: #6b7280; font-size: 14px;">View full message</summary>
                        <div style="margin-top: 8px; padding: 12px; background: #f9fafb; border-radius: 6px; font-size: 13px; color: #374151;">
                            ${message}
                        </div>
                    </details>
                </div>
            `;
        }).join('');
    }
}

// Cancel verification
async function cancelVerificationClassic() {
    if (!currentVerification) return;
    
    if (!confirm('Cancel this verification and get a refund?')) return;
    
    try {
        const response = await fetch(`${API_BASE}/verify/${currentVerification.id}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${window.token}` }
        });
        
        if (response.ok) {
            const data = await response.json();
            if (typeof showNotification === 'function') {
                showNotification(`Verification cancelled. Refunded: N${data.refunded.toFixed(2)}`, 'success');
            }
            resetVerificationFlowClassic();
            
            // Update user credits
            const creditsElement = document.getElementById('user-credits');
            if (creditsElement && data.new_balance !== undefined) {
                creditsElement.textContent = data.new_balance.toFixed(2);
            }
        } else {
            const data = await response.json();
            throw new Error(data.detail || 'Failed to cancel verification');
        }
    } catch (error) {
        console.error('Error cancelling verification:', error);
        if (typeof showNotification === 'function') {
            showNotification(error.message, 'error');
        }
    }
}

// Reset verification flow
function resetVerificationFlowClassic() {
    currentVerification = null;
    selectedService = null;
    selectedType = 'sms';
    
    if (verificationTimer) {
        clearInterval(verificationTimer);
        verificationTimer = null;
    }
    
    // Reset UI
    const serviceSelection = document.getElementById('service-selection-classic');
    const statusContainer = document.getElementById('verification-status-classic');
    const messagesContainer = document.getElementById('messages-display-classic');
    const serviceInfo = document.getElementById('service-selected-info');
    
    if (serviceSelection) serviceSelection.classList.remove('hidden');
    if (statusContainer) statusContainer.classList.add('hidden');
    if (messagesContainer) messagesContainer.classList.add('hidden');
    if (serviceInfo) serviceInfo.classList.add('hidden');
    
    // Reset selections
    document.querySelectorAll('.service-item-classic').forEach(item => {
        item.classList.remove('selected');
    });
    
    // Reset create button
    const createBtn = document.getElementById('create-verification-classic');
    if (createBtn) {
        createBtn.innerHTML = '📱 Create SMS Verification';
    }
    
    // Disable create button
    const createBtn = document.getElementById('create-verification-classic');
    if (createBtn) createBtn.disabled = true;
}

// Setup event listeners
function setupEventListeners() {
    const searchInput = document.getElementById('service-search-classic');
    const categorySelect = document.getElementById('category-filter-classic');
    
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            clearTimeout(window.searchTimeout);
            window.searchTimeout = setTimeout(() => {
                loadServicesClassic();
            }, 300);
        });
    }
    
    if (categorySelect) {
        categorySelect.addEventListener('change', () => {
            loadServicesClassic();
        });
    }
}

// Utility functions
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        if (typeof showNotification === 'function') {
            showNotification(`Copied: ${text}`, 'success');
        }
    }).catch(() => {
        if (typeof showNotification === 'function') {
            showNotification('Failed to copy', 'error');
        }
    });
}

function formatPhoneNumber(phone) {
    if (!phone) return 'Loading...';
    return phone.replace(/^\+?1?/, '+1 ');
}

function formatServiceName(service) {
    const special = {
        'twitter': 'X (Twitter)',
        'x': 'X (Twitter)'
    };
    
    if (special[service.toLowerCase()]) {
        return special[service.toLowerCase()];
    }
    
    return service.charAt(0).toUpperCase() + service.slice(1);
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initClassicVerification);
} else {
    initClassicVerification();
}