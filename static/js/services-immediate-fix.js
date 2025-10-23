// Immediate services fix - loads services instantly
console.log('🚀 Immediate services fix loaded');

// Load services immediately when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Fix the main categories container
    const container = document.getElementById('categories-container');
    if (container) {
        const services = {
            "Social": [
                {name: "WhatsApp", id: "whatsapp", price: "N0.75"},
                {name: "Telegram", id: "telegram", price: "N0.75"},
                {name: "Discord", id: "discord", price: "N0.75"},
                {name: "Instagram", id: "instagram", price: "N1.00"},
                {name: "Facebook", id: "facebook", price: "N1.00"},
                {name: "Twitter", id: "twitter", price: "N1.00"},
                {name: "TikTok", id: "tiktok", price: "N1.00"}
            ],
            "Finance": [
                {name: "PayPal", id: "paypal", price: "N1.50"},
                {name: "Cash App", id: "cashapp", price: "N1.50"},
                {name: "Venmo", id: "venmo", price: "N1.50"},
                {name: "Coinbase", id: "coinbase", price: "N2.00"}
            ],
            "Other": [
                {name: "Google", id: "google", price: "N0.75"},
                {name: "Amazon", id: "amazon", price: "N2.00"},
                {name: "Uber", id: "uber", price: "N2.00"},
                {name: "Apple", id: "apple", price: "N2.00"}
            ]
        };
        
        let html = '';
        Object.entries(services).forEach(([category, serviceList]) => {
            html += `<div style="min-width: 85px;">`;
            html += `<div style="font-weight: bold; font-size: 0.7rem; color: var(--accent); margin-bottom: 6px; border-bottom: 1px solid var(--accent); padding-bottom: 2px;">${category}</div>`;
            serviceList.forEach(service => {
                html += `<div onclick="selectService('${service.id}')" style="font-size: 0.65rem; padding: 3px; cursor: pointer; border-radius: 3px; transition: all 0.2s; display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;" onmouseover="this.style.background='var(--accent)'; this.style.color='white'" onmouseout="this.style.background=''; this.style.color=''">
                    <span>${service.name}</span>
                    <span style="font-size: 0.55rem; background: #10b981; color: white; padding: 1px 3px; border-radius: 2px; font-weight: bold;">${service.price}</span>
                </div>`;
            });
            html += `</div>`;
        });
        
        container.innerHTML = html;
        console.log('✅ Services loaded immediately!');
    }
});

// Add selectServiceClassic function if it doesn't exist
window.selectServiceClassic = function(serviceId) {
    const serviceNames = {
        'whatsapp': 'WhatsApp',
        'telegram': 'Telegram', 
        'discord': 'Discord',
        'google': 'Google',
        'instagram': 'Instagram',
        'facebook': 'Facebook',
        'twitter': 'X (Twitter)',
        'tiktok': 'TikTok',
        'paypal': 'PayPal',
        'cashapp': 'Cash App',
        'amazon': 'Amazon',
        'uber': 'Uber'
    };
    
    const servicePrices = {
        'whatsapp': 'N0.75', 'telegram': 'N0.75', 'discord': 'N0.75', 'google': 'N0.75',
        'instagram': 'N1.00', 'facebook': 'N1.00', 'twitter': 'N1.00', 'tiktok': 'N1.00',
        'paypal': 'N1.50', 'cashapp': 'N1.50', 'venmo': 'N1.50',
        'amazon': 'N2.00', 'uber': 'N2.00', 'apple': 'N2.00'
    };
    
    // Update selected service info
    const nameEl = document.getElementById('selected-service-name');
    const priceEl = document.getElementById('selected-service-price');
    const infoEl = document.getElementById('service-selected-info');
    const btnEl = document.getElementById('create-verification-classic');
    
    if (nameEl) nameEl.textContent = serviceNames[serviceId] || serviceId;
    if (priceEl) priceEl.textContent = servicePrices[serviceId] || 'N2.00';
    if (infoEl) infoEl.classList.remove('hidden');
    if (btnEl) {
        btnEl.disabled = false;
        btnEl.style.opacity = '1';
        btnEl.style.cursor = 'pointer';
    }
    
    // Store selected service
    window.selectedService = serviceId;
    
    console.log(`Selected service: ${serviceNames[serviceId]} (${servicePrices[serviceId]})`);
};

// Add createVerificationClassic function if it doesn't exist
window.createVerificationClassic = function() {
    if (!window.selectedService) {
        alert('Please select a service first');
        return;
    }
    
    if (typeof createVerification === 'function') {
        // Set the service in the main form
        const serviceSelect = document.getElementById('service-select');
        if (serviceSelect) {
            serviceSelect.value = window.selectedService;
        }
        createVerification();
    } else {
        alert('Verification system not loaded. Please refresh the page.');
    }
};