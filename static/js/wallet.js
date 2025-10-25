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
                    'Authorization': `Bearer ${window.token}`,
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
        } else if (method === 'bitcoin' || method === 'ethereum' || method === 'solana' || method === 'usdt') {
            showLoading(false);
            showCryptoPayment(method, amount);
        } else {
            showLoading(false);
            showNotification('❌ Invalid payment method selected.', 'error');
        }
    } catch (err) {
        showLoading(false);
        showNotification('❌ Payment initialization failed', 'error');
    }
}

async function verifyPayment(reference) {
    try {
        const response = await fetch(`${API_BASE}/wallet/paystack/verify/${reference}`, {
            headers: { 'Authorization': `Bearer ${window.token}` }
        });
        const data = await response.json();
        if (response.ok && data.status === 'success') {
            // Track wallet top-up
            if (typeof trackWalletTopup === 'function') {
                trackWalletTopup(reference, data.amount);
            }
            
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

// Crypto payment addresses (loaded from backend)
let cryptoAddresses = {
    bitcoin: 'bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh',
    ethereum: '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb',
    solana: '7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU',
    usdt: '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb'
};

function showCryptoPayment(method, amount) {
    const cryptoNames = {
        bitcoin: 'Bitcoin (BTC)',
        ethereum: 'Ethereum (ETH)',
        solana: 'Solana (SOL)',
        usdt: 'USDT (Tether)'
    };
    
    const address = cryptoAddresses[method];
    const cryptoName = cryptoNames[method];
    
    if (!address) {
        showNotification('❌ Crypto address not configured', 'error');
        return;
    }
    
    // Create crypto payment modal
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.style.display = 'flex';
    modal.innerHTML = `
        <div class="modal-content" style="max-width: 500px;">
            <span class="close" onclick="this.parentElement.parentElement.remove()">&times;</span>
            <h2>💰 ${cryptoName} Payment</h2>
            <p style="color: #6b7280; margin-bottom: 20px;">Send exactly <strong>$${amount} USD</strong> worth of ${cryptoName} to the address below:</p>
            
            <div style="background: #f9fafb; border: 2px solid #e5e7eb; border-radius: 8px; padding: 20px; margin-bottom: 20px; text-align: center;">
                <div style="font-weight: bold; margin-bottom: 10px; color: #374151;">Payment Address:</div>
                <div style="font-family: monospace; font-size: 14px; word-break: break-all; background: white; padding: 15px; border-radius: 6px; border: 1px solid #d1d5db; margin-bottom: 15px;">${address}</div>
                <button onclick="copyToClipboard('${address}')" style="padding: 8px 16px; background: #10b981; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 600;">📋 Copy Address</button>
            </div>
            
            <div style="background: #fef3c7; border: 2px solid #f59e0b; border-radius: 8px; padding: 15px; margin-bottom: 20px;">
                <div style="font-weight: bold; color: #92400e; margin-bottom: 8px;">⚠️ Important Instructions:</div>
                <ul style="color: #92400e; margin: 0; padding-left: 20px; font-size: 14px;">
                    <li>Send exactly $${amount} USD worth of ${cryptoName}</li>
                    <li>Use the exact address above</li>
                    <li>Credits will be added within 10-30 minutes</li>
                    <li>Contact support if payment is not credited within 1 hour</li>
                </ul>
            </div>
            
            <div style="display: flex; gap: 10px;">
                <button onclick="this.parentElement.parentElement.parentElement.remove(); showNotification('✅ Payment instructions copied. Send ${cryptoName} to complete payment.', 'success');" style="flex: 1; background: #10b981;">✅ I've Sent Payment</button>
                <button onclick="this.parentElement.parentElement.parentElement.remove();" style="flex: 1; background: #ef4444;">❌ Cancel</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification('📋 Address copied to clipboard!', 'success');
    }).catch(() => {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        showNotification('📋 Address copied to clipboard!', 'success');
    });
}

window.addEventListener('load', () => {
    const urlParams = new URLSearchParams(window.location.search);
    const reference = urlParams.get('reference');
    if (reference && localStorage.getItem('token')) {
        verifyPayment(reference);
        window.history.replaceState({}, document.title, window.location.pathname);
    }
});
