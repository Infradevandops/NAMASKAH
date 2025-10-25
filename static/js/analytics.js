// Google Analytics 4 Event Tracking for Namaskah SMS
// Track key business events for revenue optimization

// Initialize GA4 tracking
function initAnalytics() {
    if (typeof gtag === 'undefined') {
        console.log('Google Analytics not loaded');
        return;
    }
    
    // Track page view
    gtag('config', 'G-M15PBV1P55', {
        page_title: 'Namaskah SMS Dashboard',
        page_location: window.location.href
    });
}

// Track verification purchases (main revenue event)
function trackVerificationPurchase(verificationId, serviceName, cost, currency = 'NGN') {
    if (typeof gtag === 'undefined') return;
    
    gtag('event', 'purchase', {
        transaction_id: verificationId,
        value: parseFloat(cost),
        currency: currency,
        items: [{
            item_id: verificationId,
            item_name: serviceName + ' Verification',
            category: 'sms_verification',
            quantity: 1,
            price: parseFloat(cost)
        }]
    });
    
    console.log('📊 Tracked verification purchase:', serviceName, cost);
}

// Track wallet top-ups (revenue event)
function trackWalletTopup(paymentId, amount, currency = 'NGN') {
    if (typeof gtag === 'undefined') return;
    
    gtag('event', 'purchase', {
        transaction_id: paymentId,
        value: parseFloat(amount),
        currency: currency,
        items: [{
            item_id: 'wallet_topup',
            item_name: 'Wallet Credit',
            category: 'credits',
            quantity: 1,
            price: parseFloat(amount)
        }]
    });
    
    console.log('📊 Tracked wallet topup:', amount);
}

// Track user registration (conversion funnel)
function trackUserRegistration(method = 'email') {
    if (typeof gtag === 'undefined') return;
    
    gtag('event', 'sign_up', {
        method: method
    });
    
    console.log('📊 Tracked user registration:', method);
}

// Track user login
function trackUserLogin(method = 'email') {
    if (typeof gtag === 'undefined') return;
    
    gtag('event', 'login', {
        method: method
    });
}

// Track verification attempts (conversion funnel)
function trackVerificationStart(serviceName) {
    if (typeof gtag === 'undefined') return;
    
    gtag('event', 'begin_checkout', {
        currency: 'NGN',
        value: 0.50, // Default verification cost
        items: [{
            item_name: serviceName + ' Verification',
            category: 'sms_verification'
        }]
    });
    
    console.log('📊 Tracked verification start:', serviceName);
}

// Track successful verifications (conversion completion)
function trackVerificationSuccess(serviceName, cost) {
    if (typeof gtag === 'undefined') return;
    
    gtag('event', 'conversion', {
        send_to: 'G-M15PBV1P55/verification_success',
        value: parseFloat(cost),
        currency: 'NGN'
    });
    
    console.log('📊 Tracked verification success:', serviceName);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', initAnalytics);

// Export functions for use in other scripts
window.trackVerificationPurchase = trackVerificationPurchase;
window.trackWalletTopup = trackWalletTopup;
window.trackUserRegistration = trackUserRegistration;
window.trackUserLogin = trackUserLogin;
window.trackVerificationStart = trackVerificationStart;
window.trackVerificationSuccess = trackVerificationSuccess;