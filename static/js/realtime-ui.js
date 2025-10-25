// Real-time UI Updates
class RealtimeUI {
    constructor() {
        this.updateInterval = null;
        this.init();
    }

    init() {
        this.startRealtimeUpdates();
        this.setupVisibilityHandling();
    }

    startRealtimeUpdates() {
        // Update UI every 5 seconds
        this.updateInterval = setInterval(() => {
            this.updateVerificationStatus();
            this.updatePerformanceMetrics();
        }, 5000);
    }

    async updateVerificationStatus() {
        const activeVerifications = document.querySelectorAll('[data-verification-id]');
        
        for (const element of activeVerifications) {
            const verificationId = element.dataset.verificationId;
            try {
                const response = await fetch(`/verify/${verificationId}`);
                if (response.ok) {
                    const data = await response.json();
                    this.updateVerificationUI(element, data);
                }
            } catch (error) {
                console.error('Failed to update verification:', error);
            }
        }
    }

    updateVerificationUI(element, data) {
        const statusElement = element.querySelector('.status-badge');
        if (statusElement) {
            statusElement.textContent = data.status;
            statusElement.className = `status-badge ${data.status}`;
        }

        // Show success animation for completed verifications
        if (data.status === 'completed') {
            this.showSuccessAnimation(element);
        }
    }

    updatePerformanceMetrics() {
        if (window.performanceMonitor) {
            window.performanceMonitor.updateDashboard();
        }
    }

    showSuccessAnimation(element) {
        element.style.animation = 'pulse 0.5s ease-in-out';
        setTimeout(() => {
            element.style.animation = '';
        }, 500);
    }

    setupVisibilityHandling() {
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseUpdates();
            } else {
                this.resumeUpdates();
            }
        });
    }

    pauseUpdates() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }

    resumeUpdates() {
        if (!this.updateInterval) {
            this.startRealtimeUpdates();
        }
    }
}

// Initialize real-time UI
window.realtimeUI = new RealtimeUI();