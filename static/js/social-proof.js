// Social Proof System - Live Stats, Activity Feed, Trust Indicators

const CITIES = ['New York', 'London', 'Tokyo', 'Singapore', 'Dubai', 'Toronto', 'Sydney', 'Mumbai', 'Berlin', 'Paris'];
const FIELDS = ['Software Dev', 'Digital Marketing', 'Fintech', 'E-commerce', 'Crypto Trading'];
const SERVICES = ['WhatsApp', 'Telegram', 'Binance', 'Instagram', 'Tinder', 'Facebook', 'Discord', 'Coinbase'];
const NAMES = ['John Davidson', 'Sarah Mitchell', 'Michael Kumar', 'Emma Chen', 'David Rodriguez', 'Lisa Anderson', 'James Wilson', 'Maria Garcia', 'Robert Taylor', 'Jennifer Lee'];

// Live Stats Counter
class LiveStatsCounter {
    constructor() {
        this.baseUsers = 5247;
        this.baseVerifications = 15234;
        this.startTime = Date.now();
    }

    getActiveUsers() {
        const elapsed = Math.floor((Date.now() - this.startTime) / 1000);
        return this.baseUsers + Math.floor(elapsed / 10) + Math.floor(Math.random() * 5);
    }

    getTodayVerifications() {
        const elapsed = Math.floor((Date.now() - this.startTime) / 1000);
        return this.baseVerifications + Math.floor(elapsed / 3) + Math.floor(Math.random() * 3);
    }

    updateDisplay() {
        const activeUsers = this.getActiveUsers().toLocaleString();
        const verifications = this.getTodayVerifications().toLocaleString();
        
        const activeEl = document.getElementById('active-users-count');
        const verifEl = document.getElementById('verifications-count');
        
        if (activeEl) activeEl.textContent = activeUsers;
        if (verifEl) verifEl.textContent = verifications;
    }

    start() {
        this.updateDisplay();
        setInterval(() => this.updateDisplay(), 5000);
    }
}

// Real-time Activity Feed
class ActivityFeed {
    constructor() {
        this.activities = [];
        this.container = null;
    }

    generateActivity() {
        const name = NAMES[Math.floor(Math.random() * NAMES.length)];
        const city = CITIES[Math.floor(Math.random() * CITIES.length)];
        const service = SERVICES[Math.floor(Math.random() * SERVICES.length)];
        const field = FIELDS[Math.floor(Math.random() * FIELDS.length)];
        const timeAgo = Math.floor(Math.random() * 60) + 1;
        
        return {
            name,
            city,
            service,
            field,
            timeAgo: timeAgo < 60 ? `${timeAgo}s ago` : `${Math.floor(timeAgo/60)}m ago`,
            timestamp: Date.now()
        };
    }

    addActivity() {
        const activity = this.generateActivity();
        this.activities.unshift(activity);
        if (this.activities.length > 5) this.activities.pop();
        this.render();
    }

    render() {
        this.container = document.getElementById('activity-feed');
        if (!this.container) return;

        this.container.innerHTML = this.activities.map(a => `
            <div class="activity-item" style="padding: 8px 12px; background: rgba(16, 185, 129, 0.1); border-left: 3px solid #10b981; border-radius: 6px; margin-bottom: 8px; animation: slideIn 0.3s ease-out;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="flex: 1;">
                        <strong style="color: var(--text-primary);">${a.name}</strong>
                        <span style="color: var(--text-secondary); font-size: 13px;"> from ${a.city}</span>
                    </div>
                    <span style="color: var(--text-secondary); font-size: 12px;">${a.timeAgo}</span>
                </div>
                <div style="font-size: 13px; color: var(--text-secondary); margin-top: 2px;">
                    Verified <strong style="color: #667eea;">${a.service}</strong> • ${a.field}
                </div>
            </div>
        `).join('');
    }

    start() {
        // Add initial activities
        for (let i = 0; i < 3; i++) {
            this.addActivity();
        }
        // Add new activity every 8-15 seconds
        setInterval(() => {
            this.addActivity();
        }, Math.random() * 7000 + 8000);
    }
}

// Urgency Indicators
class UrgencyIndicators {
    constructor() {
        this.viewersBase = 23;
        this.lastVerificationTime = Date.now();
    }

    getCurrentViewers() {
        return this.viewersBase + Math.floor(Math.random() * 10);
    }

    getLastVerificationSeconds() {
        return Math.floor((Date.now() - this.lastVerificationTime) / 1000);
    }

    updateLastVerification() {
        this.lastVerificationTime = Date.now();
    }

    updateDisplay() {
        const viewers = this.getCurrentViewers();
        const lastVerif = this.getLastVerificationSeconds();
        
        const viewersEl = document.getElementById('current-viewers');
        const lastVerifEl = document.getElementById('last-verification');
        
        if (viewersEl) {
            viewersEl.textContent = `${viewers} people viewing this page`;
        }
        
        if (lastVerifEl) {
            lastVerifEl.textContent = `Last verification: ${lastVerif}s ago`;
        }
    }

    start() {
        this.updateDisplay();
        setInterval(() => {
            this.updateDisplay();
            // Reset last verification randomly
            if (Math.random() > 0.7) {
                this.updateLastVerification();
            }
        }, 1000);
    }
}

// Initialize all social proof elements
function initSocialProof() {
    // Live Stats
    const statsCounter = new LiveStatsCounter();
    statsCounter.start();

    // Activity Feed
    const activityFeed = new ActivityFeed();
    activityFeed.start();

    // Urgency Indicators
    const urgency = new UrgencyIndicators();
    urgency.start();
}

// Auto-initialize on DOM load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSocialProof);
} else {
    initSocialProof();
}

// Export for manual initialization
window.initSocialProof = initSocialProof;
