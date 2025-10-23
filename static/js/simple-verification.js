// Simplified Direct Verification Flow
let selectedService = null;
let selectedCapability = 'sms';

// Popular services with direct pricing
const popularServices = [
    { id: 'whatsapp', name: 'WhatsApp', icon: '💬', price: 0.75 },
    { id: 'telegram', name: 'Telegram', icon: '✈️', price: 0.75 },
    { id: 'discord', name: 'Discord', icon: '🎮', price: 0.75 },
    { id: 'google', name: 'Google', icon: '🔍', price: 0.75 },
    { id: 'instagram', name: 'Instagram', icon: '📷', price: 1.00 },
    { id: 'facebook', name: 'Facebook', icon: '👥', price: 1.00 },
    { id: 'twitter', name: 'Twitter/X', icon: '🐦', price: 1.00 },
    { id: 'tiktok', name: 'TikTok', icon: '🎵', price: 1.00 },
    { id: 'snapchat', name: 'Snapchat', icon: '👻', price: 1.00 },
    { id: 'linkedin', name: 'LinkedIn', icon: '💼', price: 1.25 },
    { id: 'uber', name: 'Uber', icon: '🚗', price: 1.25 },
    { id: 'paypal', name: 'PayPal', icon: '💳', price: 1.50 }
];

// Initialize services grid
function initServicesGrid() {
    const grid = document.getElementById('services-grid');
    if (!grid) return;
    
    grid.innerHTML = popularServices.map(service => `
        <div class="service-card" onclick="selectServiceDirect('${service.id}')" style="
            background: var(--bg-secondary);
            border: 2px solid var(--border);
            border-radius: 8px;
            padding: 15px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
        ">
            <div style="font-size: 2rem; margin-bottom: 8px;">${service.icon}</div>
            <div style="font-weight: 600; margin-bottom: 4px;">${service.name}</div>
            <div style="font-size: 12px; color: #10b981; font-weight: 600;">N${service.price.toFixed(2)}</div>
        </div>
    `).join('');
}

// Direct service selection
function selectServiceDirect(serviceId) {
    selectedService = serviceId;
    const service = popularServices.find(s => s.id === serviceId);
    
    // Update modal content
    document.getElementById('selected-service-name').textContent = `${service.name} Verification`;
    document.getElementById('sms-price-display').textContent = `N${service.price.toFixed(2)}`;
    document.getElementById('voice-price-display').textContent = `N${(service.price + 0.30).toFixed(2)}`;
    
    // Show capability modal
    document.getElementById('capability-modal').classList.remove('hidden');
}

// Select capability
function selectCapability(capability) {
    selectedCapability = capability;
    
    // Update UI
    const smsOption = document.getElementById('sms-option');
    const voiceOption = document.getElementById('voice-option');
    
    if (capability === 'sms') {
        smsOption.style.borderColor = '#10b981';
        voiceOption.style.borderColor = 'transparent';
    } else {
        smsOption.style.borderColor = 'transparent';
        voiceOption.style.borderColor = '#10b981';
    }
}

// Create verification directly
async function createDirectVerification() {
    if (!selectedService || !window.token) {
        showNotification('Please login first', 'error');
        return;
    }
    
    showLoading(true);
    closeCapabilityModal();
    
    try {
        const response = await fetch(`${API_BASE}/verify/create`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${window.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                service_name: selectedService,
                capability: selectedCapability
            })
        });
        
        const data = await response.json();
        showLoading(false);
        
        if (response.ok) {
            currentVerificationId = data.id;
            displayVerification(data);
            document.getElementById('user-credits').textContent = data.remaining_credits.toFixed(2);
            
            const capabilityText = selectedCapability === 'voice' ? '📞 Voice' : '📱 SMS';
            showNotification(`✅ ${capabilityText} verification created!`, 'success');
            
            startAutoRefresh();
            if (typeof loadHistory === 'function') loadHistory();
            if (typeof loadTransactions === 'function') loadTransactions(true);
        } else {
            if (response.status === 402) {
                showNotification(`💳 Insufficient funds. ${data.detail}`, 'error');
            } else {
                showNotification(`❌ ${data.detail || 'Failed to create verification'}`, 'error');
            }
        }
    } catch (error) {
        showLoading(false);
        showNotification('🌐 Network error. Check your connection', 'error');
    }
}

// Close capability modal
function closeCapabilityModal() {
    document.getElementById('capability-modal').classList.add('hidden');
    selectedService = null;
    selectedCapability = 'sms';
}

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    initServicesGrid();
    
    // Set default SMS selection
    setTimeout(() => {
        selectCapability('sms');
    }, 100);
});