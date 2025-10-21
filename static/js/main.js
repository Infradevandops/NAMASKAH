// Main Entry Point - Imports all modules
// This file serves as the orchestrator that loads all modular components

// Global variables shared across modules
const API_BASE = '';

// Load order matters - config first, then utilities, then feature modules
// All modules are loaded via script tags in HTML in this order:
// 1. config.js
// 2. utils.js
// 3. auth.js
// 4. services.js
// 5. verification.js
// 6. history.js
// 7. wallet.js
// 8. rentals.js
// 9. developer.js
// 10. settings.js
// 11. mobile.js (if exists)
// 12. receipts.js
// 13. main.js (this file)

// Receipt and Notification Functions
function toggleReceipts() {
    const section = document.getElementById('receipts-section');
    const btn = document.getElementById('toggle-receipts-btn');
    
    if (section.style.display === 'none') {
        section.style.display = 'block';
        btn.textContent = '🧾 Hide Receipts';
        btn.style.background = '#ef4444';
        
        // Load receipts if not already loaded
        if (window.receiptManager) {
            receiptManager.loadReceipts();
        }
    } else {
        section.style.display = 'none';
        btn.textContent = '🧾 Show Receipts';
        btn.style.background = '#667eea';
    }
}

function toggleNotifications() {
    const section = document.getElementById('notifications-section');
    const btn = document.getElementById('toggle-notifications-btn');
    
    if (section.style.display === 'none') {
        section.style.display = 'block';
        btn.textContent = '🔔 Hide Notifications';
        btn.style.background = '#ef4444';
        
        // Load notifications if not already loaded
        if (window.receiptManager) {
            receiptManager.loadNotifications();
        }
    } else {
        section.style.display = 'none';
        btn.textContent = '🔔 Show Notifications';
        btn.style.background = '#667eea';
    }
}

// Navigation function for bottom nav
function navigateToSection(section) {
    // Hide all sections first
    document.getElementById('receipts-section').style.display = 'none';
    document.getElementById('notifications-section').style.display = 'none';
    document.getElementById('verifications-list').style.display = 'none';
    document.getElementById('transactions-list').style.display = 'none';
    document.getElementById('active-rentals-section').style.display = 'none';
    
    // Update nav items
    document.querySelectorAll('.bottom-nav-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // Show selected section and activate nav item
    const navItem = document.querySelector(`[data-section="${section}"]`);
    if (navItem) {
        navItem.classList.add('active');
    }
    
    switch (section) {
        case 'home':
            // Home is always visible, just scroll to top
            window.scrollTo({ top: 0, behavior: 'smooth' });
            break;
        case 'verify':
            // Scroll to verification section
            document.querySelector('.card h2').scrollIntoView({ behavior: 'smooth' });
            break;
        case 'rentals':
            document.getElementById('active-rentals-section').style.display = 'block';
            loadActiveRentals();
            break;
        case 'receipts':
            toggleReceipts();
            break;
        case 'settings':
            // Scroll to settings section
            document.querySelector('.card:has(#advanced-section)').scrollIntoView({ behavior: 'smooth' });
            break;
    }
}

// Update notification settings (enhanced version)
async function updateNotificationSettings() {
    if (!window.receiptManager) {
        // Fallback to legacy settings
        const emailOnSms = document.getElementById('email-on-sms')?.checked || false;
        const emailOnLowBalance = document.getElementById('email-on-low-balance')?.checked || false;
        const lowBalanceThreshold = parseFloat(document.getElementById('low-balance-threshold')?.value || 1.0);
        
        try {
            const response = await fetch('/notifications/settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({
                    email_on_sms: emailOnSms,
                    email_on_low_balance: emailOnLowBalance,
                    low_balance_threshold: lowBalanceThreshold
                })
            });
            
            if (response.ok) {
                showNotification('Notification settings updated', 'success');
            }
        } catch (error) {
            console.error('Failed to update notification settings:', error);
        }
    } else {
        // Use new receipt manager
        receiptManager.updateNotificationSettings();
    }
}

// Load notification settings on page load
async function loadNotificationSettings() {
    try {
        const response = await fetch('/notifications/settings', {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        
        if (response.ok) {
            const settings = await response.json();
            
            // Update legacy checkboxes if they exist
            const emailOnSms = document.getElementById('email-on-sms');
            const emailOnLowBalance = document.getElementById('email-on-low-balance');
            const lowBalanceThreshold = document.getElementById('low-balance-threshold');
            
            if (emailOnSms) emailOnSms.checked = settings.email_on_sms;
            if (emailOnLowBalance) emailOnLowBalance.checked = settings.email_on_low_balance;
            if (lowBalanceThreshold) lowBalanceThreshold.value = settings.low_balance_threshold;
        }
    } catch (error) {
        console.error('Failed to load notification settings:', error);
    }
}

// Initialize receipt system when page loads
document.addEventListener('DOMContentLoaded', () => {
    // Load notification settings
    const token = localStorage.getItem('token');
    if (token) {
        loadNotificationSettings();
    }
    
    // Initialize receipt manager if available
    if (window.receiptManager) {
        console.log('📧 Receipt system initialized');
    }
});

console.log('✅ Namaskah SMS Platform Loaded');
console.log('📦 Modular architecture active');
console.log('🧾 Receipt and notification system ready');

// Export functions for global access
window.toggleReceipts = toggleReceipts;
window.toggleNotifications = toggleNotifications;
window.navigateToSection = navigateToSection;
window.updateNotificationSettings = updateNotificationSettings;
window.loadNotificationSettings = loadNotificationSettings;
