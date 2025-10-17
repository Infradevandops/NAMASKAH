// Wallet & Payment Module
let hasShownPricingOffer = localStorage.getItem('hasShownPricingOffer') === 'true';

function showFundWallet() {
    document.getElementById('fund-wallet-modal').classList.remove('hidden');
    document.getElementById('payment-methods').classList.add('hidden');
    document.getElementById('crypto-options').classList.add('hidden');
    document.getElementById('fund-amount').value = '';
}

function closeFundWallet() {
    document.getElementById('fund-wallet-modal').classList.add('hidden');
}

function showPaymentMethods() {
    const amount = parseFloat(document.getElementById('fund-amount').value);
    
    if (!amount || amount < 5) {
        showNotification('⚠️ Minimum funding amount is $5.00', 'error');
        return;
    }
    
    document.getElementById('payment-methods').classList.remove('hidden');
}

function toggleCrypto() {
    const cryptoOptions = document.getElementById('crypto-options');
    cryptoOptions.classList.toggle('hidden');
}

async function selectPayment(method) {
    const amount = parseFloat(document.getElementById('fund-amount').value);
    
    if (!amount || amount < 5) {
        showNotification('⚠️ Please enter amount first', 'error');
        return;
    }
    
    showLoading(true);
    
    try {
        if (method === 'paystack') {
            const res = await fetch(`${API_BASE}/wallet/paystack/initialize`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ amount, payment_method: method })
            });
            
            if (res.ok) {
                const data = await res.json();
                showLoading(false);
                
                if (data.payment_details) {
                    showNotification(
                        `💰 Pay ₦${data.payment_details.ngn_amount.toLocaleString()} ($${data.payment_details.usd_amount})`,
                        'success'
                    );
                }
                
                setTimeout(() => {
                    window.location.href = data.authorization_url;
                }, 1500);
            } else {
                const error = await res.json();
                throw new Error(error.detail || 'Paystack initialization failed');
            }
        } else {
            showLoading(false);
            showNotification('❌ Crypto payments are not available. Please use Paystack.', 'error');
        }
    } catch (err) {
        showLoading(false);
        showNotification('❌ Payment initialization failed', 'error');
    }
}

async function verifyPayment(reference) {
    try {
        const response = await fetch(`${API_BASE}/wallet/paystack/verify/${reference}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await response.json();
        if (response.ok && data.status === 'success') {
            showNotification(`✅ Payment successful! Added ₵${data.amount} to wallet`, 'success');
            checkAuth();
        } else {
            showNotification(data.message || 'Payment verification failed', 'error');
        }
    } catch (error) {
        showNotification('Failed to verify payment', 'error');
    }
}

function showPricingOffer() {
    document.getElementById('pricing-offer-modal').classList.remove('hidden');
    hasShownPricingOffer = true;
    localStorage.setItem('hasShownPricingOffer', 'true');
}

function closePricingOffer() {
    document.getElementById('pricing-offer-modal').classList.add('hidden');
}

function fundWalletWithPlan(amount) {
    closePricingOffer();
    document.getElementById('fund-amount').value = amount;
    showFundWallet();
    showPaymentMethods();
}

window.addEventListener('load', () => {
    const urlParams = new URLSearchParams(window.location.search);
    const reference = urlParams.get('reference');
    if (reference && localStorage.getItem('token')) {
        verifyPayment(reference);
        window.history.replaceState({}, document.title, window.location.pathname);
    }
});
