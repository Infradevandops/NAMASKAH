// Social Proof and Live Activity JavaScript

// Live stats animation
function updateLiveStats() {
    const activeUsers = document.getElementById('active-users-count');
    const verifications = document.getElementById('verifications-count');
    const lastVerification = document.getElementById('last-verification');
    const currentViewers = document.getElementById('current-viewers');
    
    if (activeUsers) {
        // Simulate live user count (5000-5500 range)
        const baseUsers = 5000;
        const variance = Math.floor(Math.random() * 500);
        activeUsers.textContent = (baseUsers + variance).toLocaleString();
    }
    
    if (verifications) {
        // Simulate daily verifications (15000-16000 range)
        const baseVerifications = 15000;
        const variance = Math.floor(Math.random() * 1000);
        verifications.textContent = (baseVerifications + variance).toLocaleString();
    }
    
    if (lastVerification) {
        // Simulate last verification time (1-60 seconds ago)
        const seconds = Math.floor(Math.random() * 60) + 1;
        lastVerification.textContent = `Last: ${seconds}s ago`;
    }
    
    if (currentViewers) {
        // Simulate current page viewers (15-35 range)
        const viewers = Math.floor(Math.random() * 20) + 15;
        currentViewers.textContent = `${viewers} people viewing this page`;
    }
}

// Activity feed simulation
function generateActivityFeed() {
    const activities = [
        { user: 'John D.', service: 'WhatsApp', time: '2s ago', flag: '🇺🇸' },
        { user: 'Sarah M.', service: 'Telegram', time: '5s ago', flag: '🇬🇧' },
        { user: 'Mike K.', service: 'Instagram', time: '8s ago', flag: '🇨🇦' },
        { user: 'Lisa P.', service: 'Discord', time: '12s ago', flag: '🇦🇺' },
        { user: 'Alex R.', service: 'Binance', time: '15s ago', flag: '🇩🇪' },
        { user: 'Emma W.', service: 'Google', time: '18s ago', flag: '🇫🇷' },
        { user: 'David L.', service: 'Facebook', time: '22s ago', flag: '🇮🇹' },
        { user: 'Anna S.', service: 'Tinder', time: '25s ago', flag: '🇪🇸' }
    ];
    
    const feed = document.getElementById('activity-feed');
    if (!feed) return;
    
    // Shuffle activities and take first 5
    const shuffled = activities.sort(() => 0.5 - Math.random()).slice(0, 5);
    
    feed.innerHTML = shuffled.map(activity => `
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid var(--border); font-size: 0.85rem;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <span>${activity.flag}</span>
                <span style="font-weight: 600; color: var(--text-primary);">${activity.user}</span>
                <span style="color: var(--text-secondary);">verified</span>
                <span style="color: var(--accent); font-weight: 600;">${activity.service}</span>
            </div>
            <span style="color: var(--text-secondary); font-size: 0.75rem;">${activity.time}</span>
        </div>
    `).join('');
}

// Initialize social proof features
document.addEventListener('DOMContentLoaded', function() {
    // Update stats immediately
    updateLiveStats();
    generateActivityFeed();
    
    // Update stats every 10 seconds
    setInterval(updateLiveStats, 10000);
    
    // Update activity feed every 15 seconds
    setInterval(generateActivityFeed, 15000);
    
    // Add subtle animations to stats
    const statsElements = document.querySelectorAll('#active-users-count, #verifications-count');
    statsElements.forEach(el => {
        if (el) {
            el.style.transition = 'all 0.3s ease';
        }
    });
});

// Pulse animation for CTA buttons
function addPulseAnimation() {
    const ctaButtons = document.querySelectorAll('.pulse-btn');
    ctaButtons.forEach(btn => {
        btn.addEventListener('mouseenter', function() {
            this.style.animation = 'pulse 1s infinite';
        });
        btn.addEventListener('mouseleave', function() {
            this.style.animation = 'pulse 2s infinite';
        });
    });
}

// Initialize pulse animations
document.addEventListener('DOMContentLoaded', addPulseAnimation);