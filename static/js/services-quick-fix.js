// Quick fix for services loading - loads fallback immediately
console.log('🔧 Quick services fix loaded');

// Load fallback services immediately
window.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        const container = document.getElementById('categories-container');
        if (container && container.innerHTML.includes('Loading services...')) {
            console.log('📦 Loading fallback services immediately...');
            
            const fallbackServices = {
                "Social": ["whatsapp", "telegram", "discord", "instagram", "facebook", "twitter", "snapchat", "tiktok"],
                "Finance": ["paypal", "cashapp", "venmo", "coinbase", "robinhood"],
                "Shopping": ["amazon", "ebay", "etsy", "mercari", "poshmark"],
                "Gaming": ["steam", "epic", "xbox", "playstation"],
                "Other": ["google", "microsoft", "apple", "uber", "lyft"]
            };
            
            const tierPrices = {
                'whatsapp': 'N0.75', 'telegram': 'N0.75', 'discord': 'N0.75', 'google': 'N0.75',
                'instagram': 'N1.00', 'facebook': 'N1.00', 'twitter': 'N1.00', 'tiktok': 'N1.00',
                'paypal': 'N1.50', 'venmo': 'N1.50', 'cashapp': 'N1.50'
            };
            
            let html = '';
            Object.entries(fallbackServices).forEach(([category, services]) => {
                html += `<div style="min-width: 85px;">`;
                html += `<div style="font-weight: bold; font-size: 0.7rem; color: var(--accent); margin-bottom: 6px; border-bottom: 1px solid var(--accent); padding-bottom: 2px;">${category}</div>`;
                services.forEach(service => {
                    const price = tierPrices[service] || 'N2.00';
                    const serviceName = service.charAt(0).toUpperCase() + service.slice(1);
                    html += `<div onclick="selectService('${service}')" style="font-size: 0.65rem; padding: 3px; cursor: pointer; border-radius: 3px; transition: all 0.2s; display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;" onmouseover="this.style.background='var(--accent)'; this.style.color='white'" onmouseout="this.style.background=''; this.style.color=''">
                        <span>${serviceName}</span>
                        <span style="font-size: 0.55rem; background: #10b981; color: white; padding: 1px 3px; border-radius: 2px; font-weight: bold;">${price}</span>
                    </div>`;
                });
                html += `</div>`;
            });
            
            container.innerHTML = html;
            console.log('✅ Fallback services loaded successfully!');
        }
    }, 1000);
});