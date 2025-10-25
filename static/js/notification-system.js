/**
 * Simple Notification System
 * Lightweight notification component for user feedback
 */

class NotificationSystem {
    constructor() {
        this.container = null;
        this.init();
    }

    init() {
        this.createContainer();
    }

    createContainer() {
        // Check if container already exists
        this.container = document.getElementById('notification-container');
        
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = 'notification-container';
            this.container.className = 'notification-container';
            document.body.appendChild(this.container);
        }
    }

    show(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        
        // Create notification content
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-message">${message}</span>
                <button class="notification-close" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;

        // Add to container
        this.container.appendChild(notification);

        // Animate in
        setTimeout(() => {
            notification.classList.add('notification-show');
        }, 10);

        // Auto-remove after duration
        if (duration > 0) {
            setTimeout(() => {
                this.remove(notification);
            }, duration);
        }

        return notification;
    }

    remove(notification) {
        if (notification && notification.parentNode) {
            notification.classList.add('notification-hide');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }
    }

    success(message, duration = 5000) {
        return this.show(message, 'success', duration);
    }

    error(message, duration = 7000) {
        return this.show(message, 'error', duration);
    }

    warning(message, duration = 6000) {
        return this.show(message, 'warning', duration);
    }

    info(message, duration = 5000) {
        return this.show(message, 'info', duration);
    }

    clear() {
        if (this.container) {
            this.container.innerHTML = '';
        }
    }
}

// CSS for notifications (inject into head if not already present)
function injectNotificationCSS() {
    if (document.getElementById('notification-system-css')) return;

    const css = `
        .notification-container {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            pointer-events: none;
        }

        .notification {
            background: white;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            margin-bottom: 10px;
            max-width: 400px;
            opacity: 0;
            transform: translateX(100%);
            transition: all 0.3s ease;
            pointer-events: auto;
            border-left: 4px solid #ccc;
        }

        .notification-show {
            opacity: 1;
            transform: translateX(0);
        }

        .notification-hide {
            opacity: 0;
            transform: translateX(100%);
        }

        .notification-content {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 16px;
        }

        .notification-message {
            flex: 1;
            font-size: 14px;
            line-height: 1.4;
            color: #333;
        }

        .notification-close {
            background: none;
            border: none;
            font-size: 18px;
            cursor: pointer;
            color: #666;
            margin-left: 12px;
            padding: 0;
            width: 20px;
            height: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .notification-close:hover {
            color: #333;
        }

        .notification-success {
            border-left-color: #10b981;
        }

        .notification-error {
            border-left-color: #ef4444;
        }

        .notification-warning {
            border-left-color: #f59e0b;
        }

        .notification-info {
            border-left-color: #3b82f6;
        }

        @media (max-width: 480px) {
            .notification-container {
                top: 10px;
                right: 10px;
                left: 10px;
            }

            .notification {
                max-width: none;
            }
        }
    `;

    const style = document.createElement('style');
    style.id = 'notification-system-css';
    style.textContent = css;
    document.head.appendChild(style);
}

// Initialize notification system
let notificationSystem = null;

function initNotificationSystem() {
    if (!notificationSystem) {
        injectNotificationCSS();
        notificationSystem = new NotificationSystem();
    }
    return notificationSystem;
}

// Global notification functions
window.showNotification = function(message, type = 'info', duration = 5000) {
    const system = initNotificationSystem();
    return system.show(message, type, duration);
};

window.showSuccess = function(message, duration = 5000) {
    const system = initNotificationSystem();
    return system.success(message, duration);
};

window.showError = function(message, duration = 7000) {
    const system = initNotificationSystem();
    return system.error(message, duration);
};

window.showWarning = function(message, duration = 6000) {
    const system = initNotificationSystem();
    return system.warning(message, duration);
};

window.showInfo = function(message, duration = 5000) {
    const system = initNotificationSystem();
    return system.info(message, duration);
};

// Auto-initialize on DOM ready
document.addEventListener('DOMContentLoaded', initNotificationSystem);

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NotificationSystem;
}