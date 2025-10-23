// Main Dashboard Entry Point - Simplified and Focused
const API_BASE = '';

// Core navigation function
function navigateToSection(section) {
    const sections = ['receipts-section', 'notifications-section', 'verifications-list', 'transactions-list', 'active-rentals-section'];
    
    // Hide all sections
    sections.forEach(id => {
        const element = document.getElementById(id);
        if (element) element.style.display = 'none';
    });
    
    // Update nav items
    document.querySelectorAll('.bottom-nav-item').forEach(item => {
        item.classList.remove('active');
    });
    
    const navItem = document.querySelector(`[data-section="${section}"]`);
    if (navItem) navItem.classList.add('active');
    
    switch (section) {
        case 'home':
            window.scrollTo({ top: 0, behavior: 'smooth' });
            break;
        case 'verify':
            const verifySection = document.querySelector('.card h2');
            if (verifySection) verifySection.scrollIntoView({ behavior: 'smooth' });
            break;
        case 'rentals':
            const rentalsSection = document.getElementById('active-rentals-section');
            if (rentalsSection) {
                rentalsSection.style.display = 'block';
                if (typeof loadActiveRentals === 'function') loadActiveRentals();
            }
            break;
        case 'receipts':
            const receiptsSection = document.getElementById('receipts-section');
            if (receiptsSection) {
                receiptsSection.style.display = 'block';
                if (window.receiptManager) receiptManager.loadReceipts();
            }
            break;
        case 'settings':
            const settingsSection = document.querySelector('.card:has(#advanced-section)');
            if (settingsSection) settingsSection.scrollIntoView({ behavior: 'smooth' });
            break;
    }
}

// Simple notification settings update
async function updateNotificationSettings() {
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
        
        if (response.ok && typeof showNotification === 'function') {
            showNotification('Settings updated', 'success');
        }
    } catch (error) {
        console.error('Settings update failed:', error);
    }
}

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('token');
    if (token && typeof checkAuth === 'function') {
        checkAuth();
    }
});

// Export core functions
window.navigateToSection = navigateToSection;
window.updateNotificationSettings = updateNotificationSettings;

console.log('✅ Dashboard loaded - core functionality active');