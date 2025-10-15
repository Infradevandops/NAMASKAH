const API_BASE = '';
let token = localStorage.getItem('token');
let currentVerificationId = null;
let autoRefreshInterval = null;
let historyRefreshInterval = null;
let countdownInterval = null;
let countdownSeconds = 45;
let currentServiceName = null;
let allServices = [];
let filteredServices = [];
let isOnline = navigator.onLine;
let searchDebounceTimer = null;
let serviceCache = null;
let hasShownPricingOffer = localStorage.getItem('hasShownPricingOffer') === 'true';
let firstVerificationCompleted = false;

// Monitor connection status
window.addEventListener('online', () => {
    isOnline = true;
    showNotification('✅ Connection restored', 'success');
    if (token) checkAuth();
});

window.addEventListener('offline', () => {
    isOnline = false;
    showNotification('⚠️ Connection lost. Working offline...', 'error');
});

// Service-specific timers (in seconds)
const serviceTimers = {
    'google': 60,
    'discord': 60,
    'whatsapp': 90,
    'telegram': 90,
    'instagram': 120,
    'facebook': 90,
    'twitter': 75,
    'tiktok': 90,
    'snapchat': 75,
    'default': 60
};

function getServiceTimer(serviceName) {
    const service = serviceName.toLowerCase();
    return serviceTimers[service] || serviceTimers['default'];
}

function formatPhoneNumber(phone) {
    if (!phone) return 'N/A';
    
    // Remove any existing formatting
    const cleaned = phone.replace(/\D/g, '');
    
    // US/Canada format: +1-XXX-XXX-XXXX
    if (cleaned.length === 10) {
        return `+1-${cleaned.slice(0,3)}-${cleaned.slice(3,6)}-${cleaned.slice(6)}`;
    }
    // Already has country code
    else if (cleaned.length === 11 && cleaned[0] === '1') {
        return `+${cleaned[0]}-${cleaned.slice(1,4)}-${cleaned.slice(4,7)}-${cleaned.slice(7)}`;
    }
    // International format
    else if (cleaned.length > 10) {
        const countryCode = cleaned.slice(0, cleaned.length - 10);
        const rest = cleaned.slice(-10);
        return `+${countryCode}-${rest.slice(0,3)}-${rest.slice(3,6)}-${rest.slice(6)}`;
    }
    
    return phone;
}

// Check auth on load
if (token) {
    checkAuth();
}

function showTab(tab) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    event.target.classList.add('active');
    
    if (tab === 'login') {
        document.getElementById('login-form').classList.remove('hidden');
        document.getElementById('register-form').classList.add('hidden');
    } else {
        document.getElementById('login-form').classList.add('hidden');
        document.getElementById('register-form').classList.remove('hidden');
    }
}

async function register() {
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    
    if (!email || !password) {
        showNotification('⚠️ Please enter email and password', 'error');
        return;
    }
    
    if (password.length < 6) {
        showNotification('⚠️ Password must be at least 6 characters', 'error');
        return;
    }
    
    showLoading(true);
    
    // Check for referral code in URL
    const urlParams = new URLSearchParams(window.location.search);
    const refCode = urlParams.get('ref');
    const url = refCode ? `${API_BASE}/auth/register?referral_code=${refCode}` : `${API_BASE}/auth/register`;
    
    try {
        const res = await fetch(url, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({email, password})
        });
        
        const data = await res.json();
        showLoading(false);
        
        if (res.ok) {
            token = data.token;
            localStorage.setItem('token', token);
            showNotification(`✅ Welcome! You got ₵${data.credits} free credits`, 'success');
            showApp();
        } else {
            showNotification(`❌ ${data.detail || 'Registration failed'}`, 'error');
        }
    } catch (err) {
        showLoading(false);
        showNotification('🌐 Network error. Check your connection', 'error');
    }
}

async function login() {
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    
    if (!email || !password) {
        showNotification('⚠️ Please enter email and password', 'error');
        return;
    }
    
    showLoading(true);
    
    try {
        const res = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({email, password})
        });
        
        const data = await res.json();
        showLoading(false);
        
        if (res.ok) {
            // Clear previous session
            currentVerificationId = null;
            stopAutoRefresh();
            stopHistoryRefresh();
            
            token = data.token;
            localStorage.setItem('token', token);
            showNotification('✅ Login successful!', 'success');
            showApp();
        } else {
            showNotification(`❌ ${data.detail || 'Invalid credentials'}`, 'error');
        }
    } catch (err) {
        showLoading(false);
        showNotification('🌐 Network error. Check your connection', 'error');
    }
}

async function checkAuth() {
    try {
        const res = await fetch(`${API_BASE}/auth/me`, {
            headers: {'Authorization': `Bearer ${token}`}
        });
        
        if (res.ok) {
            const user = await res.json();
            document.getElementById('user-email').textContent = user.email;
            document.getElementById('user-credits').textContent = user.credits.toFixed(2);
            showApp();
        } else {
            logout();
        }
    } catch (err) {
        logout();
    }
}

function clearSession() {
    currentVerificationId = null;
    currentServiceName = null;
    stopAutoRefresh();
    stopCountdown();
    
    // Clear UI
    document.getElementById('verification-details').classList.add('hidden');
    document.getElementById('messages-section').classList.add('hidden');
    
    showNotification('Session cleared', 'success');
    loadHistory();
}

function logout() {
    token = null;
    currentVerificationId = null;
    localStorage.removeItem('token');
    stopAutoRefresh();
    stopHistoryRefresh();
    
    // Clear UI
    document.getElementById('verification-details').classList.add('hidden');
    document.getElementById('messages-section').classList.add('hidden');
    document.getElementById('verifications').innerHTML = '';
    
    document.getElementById('auth-section').classList.remove('hidden');
    document.getElementById('app-section').classList.add('hidden');
}

function showApp() {
    document.getElementById('auth-section').classList.add('hidden');
    document.getElementById('app-section').classList.remove('hidden');
    loadServices();
    loadHistory();
    loadTransactions();
    loadAPIKeys();
    loadWebhooks();
    loadAnalytics();
    loadNotificationSettings();
    loadReferralStats();
    startHistoryRefresh();
}

let servicesData = null;

async function loadServices() {
    if (servicesData) {
        renderServices();
        return;
    }
    
    try {
        const res = await fetch(`${API_BASE}/services/list`);
        if (res.ok) {
            servicesData = await res.json();
            renderServices();
            const total = Object.values(servicesData.categories).reduce((sum, arr) => sum + arr.length, 0) + servicesData.uncategorized.length;
            showNotification(`✅ ${total} services loaded!`, 'success');
        }
    } catch (err) {
        console.error('Failed to load services:', err);
        showNotification('⚠️ Failed to load services', 'error');
    }
}

function formatServiceName(service) {
    const special = {
        'twitter': 'X (Twitter)',
        'x': 'X (Twitter)'
    };
    
    if (special[service.toLowerCase()]) {
        return special[service.toLowerCase()];
    }
    
    return service.charAt(0).toUpperCase() + service.slice(1);
}

function renderServices() {
    if (!servicesData) {
        document.getElementById('categories-container').innerHTML = 'Loading services...';
        return;
    }
    
    const container = document.getElementById('categories-container');
    const search = document.getElementById('service-search').value.toLowerCase();
    let html = '';
    
    const categoryOrder = ['Social', 'Messaging', 'Dating', 'Finance', 'Shopping', 'Food', 'Gaming', 'Crypto'];
    
    categoryOrder.forEach(category => {
        if (servicesData.categories && servicesData.categories[category]) {
            let services = servicesData.categories[category];
            if (search) {
                services = services.filter(s => s.toLowerCase().includes(search));
            }
            if (services.length > 0) {
                html += `<div style="min-width: 100px;">`;
                html += `<div style="font-weight: bold; font-size: 0.75rem; color: var(--accent); margin-bottom: 8px; border-bottom: 2px solid var(--accent); padding-bottom: 4px;">${category}</div>`;
                services.slice(0, 10).forEach(service => {
                    html += `<div onclick="selectService('${service}')" style="font-size: 0.7rem; padding: 4px; cursor: pointer; border-radius: 4px; transition: all 0.2s;" onmouseover="this.style.background='var(--accent)'; this.style.color='white'" onmouseout="this.style.background=''; this.style.color=''">${formatServiceName(service)}</div>`;
                });
                if (services.length > 10) {
                    html += `<div style="font-size: 0.65rem; color: var(--text-secondary); padding: 4px;">+${services.length - 10} more</div>`;
                }
                html += `</div>`;
            }
        }
    });
    
    container.innerHTML = html || 'No services found';
}

function selectService(service) {
    document.getElementById('service-select').value = service;
    document.getElementById('service-info').innerHTML = `✅ Selected: <strong>${formatServiceName(service)}</strong>`;
    document.getElementById('service-info').style.color = '#10b981';
    
    // Highlight selected
    document.querySelectorAll('#categories-container > div > div[onclick]').forEach(el => {
        el.style.fontWeight = 'normal';
    });
    event.target.style.fontWeight = 'bold';
}

function filterServices() {
    if (searchDebounceTimer) clearTimeout(searchDebounceTimer);
    searchDebounceTimer = setTimeout(() => renderServices(), 200);
}

function showLoading(show = true) {
    document.getElementById('loading').classList.toggle('hidden', !show);
}

function startHistoryRefresh() {
    if (historyRefreshInterval) clearInterval(historyRefreshInterval);
    historyRefreshInterval = setInterval(() => {
        loadHistory(true);
    }, 30000); // Refresh every 30 seconds
}

function stopHistoryRefresh() {
    if (historyRefreshInterval) {
        clearInterval(historyRefreshInterval);
        historyRefreshInterval = null;
    }
}

async function createVerification() {
    const service = document.getElementById('service-select').value;
    
    if (!service) {
        showNotification('⚠️ Please select a service', 'error');
        return;
    }
    
    showLoading(true);
    
    try {
        const res = await fetch(`${API_BASE}/verify/create`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({service_name: service})
        });
        
        const data = await res.json();
        showLoading(false);
        
        if (res.ok) {
            currentVerificationId = data.id;
            displayVerification(data);
            document.getElementById('user-credits').textContent = data.remaining_credits.toFixed(2);
            showNotification(`✅ Verification created! Cost: ₵${data.cost}`, 'success');
            startAutoRefresh();
            loadHistory();
            loadTransactions(true);
            
            // Mark that user has completed first verification
            if (!firstVerificationCompleted) {
                firstVerificationCompleted = true;
            }
        } else {
            if (res.status === 402) {
                showNotification(`💳 Insufficient funds. ${data.detail}`, 'error');
            } else if (res.status === 401) {
                showNotification('🔒 Session expired. Please login again', 'error');
                setTimeout(() => logout(), 2000);
            } else if (res.status === 503) {
                showNotification(`⚠️ Service unavailable: ${service}. Try another service`, 'error');
            } else {
                showNotification(`❌ ${data.detail || 'Failed to create verification'}`, 'error');
            }
        }
    } catch (err) {
        showLoading(false);
        showNotification('🌐 Network error. Check your connection', 'error');
    }
}

function displayVerification(data) {
    const formattedPhone = formatPhoneNumber(data.phone_number);
    document.getElementById('phone-number').textContent = formattedPhone || 'Loading...';
    document.getElementById('service-name').textContent = formatServiceName(data.service_name);
    currentServiceName = data.service_name;
    
    const statusBadge = document.getElementById('status');
    statusBadge.textContent = data.status;
    statusBadge.className = `badge ${data.status}`;
    
    document.getElementById('verification-details').classList.remove('hidden');
    document.getElementById('messages-section').classList.add('hidden');
    document.getElementById('retry-btn').classList.add('hidden');
    
    // Start countdown timer with service-specific duration
    if (data.status === 'pending') {
        const timerDuration = getServiceTimer(data.service_name);
        startCountdown(timerDuration);
    }
}

function startAutoRefresh() {
    if (autoRefreshInterval) clearInterval(autoRefreshInterval);
    
    autoRefreshInterval = setInterval(async () => {
        if (currentVerificationId) {
            await checkMessages(true);
            await updateVerificationStatus();
        }
    }, 10000); // Check every 10 seconds
}

function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }
}

function startCountdown(duration = 60) {
    countdownSeconds = duration;
    document.getElementById('timer-row').style.display = 'flex';
    document.getElementById('countdown').textContent = `${countdownSeconds}s`;
    
    if (countdownInterval) clearInterval(countdownInterval);
    
    countdownInterval = setInterval(() => {
        countdownSeconds--;
        document.getElementById('countdown').textContent = `${countdownSeconds}s`;
        
        if (countdownSeconds <= 0) {
            clearInterval(countdownInterval);
            autoCancel();
        }
    }, 1000);
}

function stopCountdown() {
    if (countdownInterval) {
        clearInterval(countdownInterval);
        countdownInterval = null;
    }
    document.getElementById('timer-row').style.display = 'none';
}

async function autoCancel() {
    if (!currentVerificationId) return;
    
    // Check if messages arrived
    try {
        const res = await fetch(`${API_BASE}/verify/${currentVerificationId}/messages`, {
            headers: {'Authorization': `Bearer ${token}`}
        });
        
        if (res.ok) {
            const data = await res.json();
            
            // If messages exist, don't cancel
            if (data.messages && data.messages.length > 0) {
                stopCountdown();
                showNotification('SMS received!', 'success');
                checkMessages(true);
                return;
            }
        }
    } catch (err) {
        // Continue to cancel
    }
    
    // No messages - auto cancel
    showNotification('No SMS in 45s - Auto-cancelling...', 'error');
    
    try {
        const res = await fetch(`${API_BASE}/verify/${currentVerificationId}`, {
            method: 'DELETE',
            headers: {'Authorization': `Bearer ${token}`}
        });
        
        if (res.ok) {
            const data = await res.json();
            document.getElementById('user-credits').textContent = data.new_balance.toFixed(2);
            showNotification(`Auto-cancelled! Refunded ₵${data.refunded.toFixed(2)}`, 'success');
            
            // Show retry button
            document.getElementById('retry-btn').classList.remove('hidden');
            stopAutoRefresh();
            stopCountdown();
            loadTransactions(true);
        }
    } catch (err) {
        showNotification('Auto-cancel failed', 'error');
    }
}

async function retryVerification() {
    if (!currentServiceName) return;
    
    // Hide retry button and old verification
    document.getElementById('retry-btn').classList.add('hidden');
    document.getElementById('verification-details').classList.add('hidden');
    
    // Create new verification with same service
    showLoading(true);
    
    try {
        const res = await fetch(`${API_BASE}/verify/create`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({service_name: currentServiceName})
        });
        
        const data = await res.json();
        showLoading(false);
        
        if (res.ok) {
            currentVerificationId = data.id;
            displayVerification(data);
            document.getElementById('user-credits').textContent = data.remaining_credits.toFixed(2);
            showNotification(`New number! Cost: ₵${data.cost}`, 'success');
            startAutoRefresh();
            loadHistory();
            loadTransactions(true);
        } else {
            showNotification(data.detail || 'Failed to retry', 'error');
        }
    } catch (err) {
        showLoading(false);
        showNotification('Network error', 'error');
    }
}

async function updateVerificationStatus() {
    if (!currentVerificationId) return;
    
    try {
        const res = await fetch(`${API_BASE}/verify/${currentVerificationId}`, {
            headers: {'Authorization': `Bearer ${token}`}
        });
        
        if (res.ok) {
            const data = await res.json();
            const statusBadge = document.getElementById('status');
            statusBadge.textContent = data.status;
            statusBadge.className = `badge ${data.status}`;
            
            if (data.status === 'completed') {
                stopAutoRefresh();
                stopCountdown();
                showNotification('Verification completed!', 'success');
            }
        }
    } catch (err) {
        // Silent fail for background updates
    }
}

function copyPhone() {
    const phone = document.getElementById('phone-number').textContent;
    navigator.clipboard.writeText(phone);
    showNotification('Phone number copied!', 'success');
}

async function checkMessages(silent = false) {
    if (!currentVerificationId) return;
    
    try {
        const res = await fetch(`${API_BASE}/verify/${currentVerificationId}/messages`, {
            headers: {'Authorization': `Bearer ${token}`}
        });
        
        if (!res.ok) {
            if (!silent) {
                if (res.status === 404) {
                    showNotification('❌ Verification not found or expired', 'error');
                } else if (res.status === 401) {
                    showNotification('🔒 Session expired', 'error');
                    setTimeout(() => logout(), 2000);
                } else {
                    showNotification('⚠️ Failed to get messages', 'error');
                }
            }
            return;
        }
        
        const data = await res.json();
        const messagesList = document.getElementById('messages-list');
        
        if (data.messages.length === 0) {
            messagesList.innerHTML = '<p>No messages yet. Auto-checking... <span class="auto-refresh">🔄 Auto-refresh ON</span></p>';
        } else {
                // Success! Show messages with celebration
                stopCountdown();
                stopAutoRefresh();
                
                messagesList.innerHTML = `
                    <div style="background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); padding: 25px; border-radius: 12px; margin-bottom: 20px; border: 3px solid #10b981; box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3); animation: pulse 2s infinite;">
                        <h2 style="color: #065f46; margin: 0 0 12px 0; font-size: 24px; text-align: center;">🎉🎊 VERIFICATION SUCCESS! 🎊🎉</h2>
                        <p style="color: #047857; margin: 0; font-size: 18px; text-align: center; font-weight: 600;">✨ SMS code received! ✨</p>
                        <p style="color: #059669; margin: 10px 0 0 0; text-align: center; font-size: 16px;">🔥 Wanna try another service? 🔥</p>
                    </div>
                    <div style="background: #f0fdf4; padding: 15px; border-radius: 8px; border-left: 4px solid #22c55e; margin-bottom: 15px;">
                        <h4 style="color: #166534; margin: 0 0 10px 0;">📱 Your SMS Messages:</h4>
                        ${data.messages.map(msg => 
                            `<div class="message-item" style="background: white; padding: 12px; margin: 8px 0; border-radius: 6px; border: 1px solid #bbf7d0; font-family: monospace; font-size: 15px; color: #166534;">${msg}</div>`
                        ).join('')}
                    </div>
                    <button onclick="tryAnotherService()" style="margin-top: 15px; width: 100%; background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%); color: white; padding: 14px; font-size: 16px; font-weight: 600; border: none; border-radius: 8px; cursor: pointer; box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4); transition: all 0.3s;">🚀 Try Another Service</button>
                `;
                
            if (!silent) {
                showNotification('🎉 Verification successful!', 'success');
                
                // Show pricing offer after first successful verification
                if (firstVerificationCompleted && !hasShownPricingOffer) {
                    setTimeout(() => showPricingOffer(), 2000);
                }
            }
        }
        
        document.getElementById('messages-section').classList.remove('hidden');
    } catch (err) {
        if (!silent) showNotification('🌐 Network error checking messages', 'error');
    }
}

function tryAnotherService() {
    // Clear current verification
    currentVerificationId = null;
    currentServiceName = null;
    stopAutoRefresh();
    stopCountdown();
    
    // Hide details
    document.getElementById('verification-details').classList.add('hidden');
    document.getElementById('messages-section').classList.add('hidden');
    
    // Scroll to service selector
    document.getElementById('service-select').scrollIntoView({ behavior: 'smooth' });
    document.getElementById('service-select').focus();
    
    showNotification('Select a new service to verify!', 'success');
}

async function cancelVerification() {
    if (!currentVerificationId) return;
    
    if (!confirm('Cancel this verification?')) return;
    
    showLoading(true);
    stopCountdown();
    
    try {
        const res = await fetch(`${API_BASE}/verify/${currentVerificationId}`, {
            method: 'DELETE',
            headers: {'Authorization': `Bearer ${token}`}
        });
        
        showLoading(false);
        
        if (res.ok) {
            const data = await res.json();
            document.getElementById('user-credits').textContent = data.new_balance.toFixed(2);
            showNotification(`Cancelled! Refunded ₵${data.refunded.toFixed(2)}`, 'success');
            document.getElementById('verification-details').classList.add('hidden');
            document.getElementById('messages-section').classList.add('hidden');
            stopAutoRefresh();
            currentVerificationId = null;
            currentServiceName = null;
            loadHistory();
            loadTransactions(true);
        } else {
            const data = await res.json();
            showNotification(data.detail || 'Failed to cancel', 'error');
        }
    } catch (err) {
        showLoading(false);
        showNotification('Network error', 'error');
    }
}

async function loadHistory(silent = false) {
    if (!token) return;
    
    try {
        const res = await fetch(`${API_BASE}/verifications/history`, {
            headers: {'Authorization': `Bearer ${token}`}
        });
        
        if (res.ok) {
            const data = await res.json();
            const list = document.getElementById('verifications');
            
            if (data.verifications.length === 0) {
                list.innerHTML = '<p style="color: #6b7280;">No verifications yet. Create one above!</p>';
            } else {
                list.innerHTML = data.verifications.map(v => `
                    <div class="verification-item" onclick="loadVerification('${v.id}')">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <strong>${formatServiceName(v.service_name)}</strong>
                                <div style="font-size: 14px; color: #6b7280;">${formatPhoneNumber(v.phone_number)}</div>
                            </div>
                            <span class="badge ${v.status}">${v.status}</span>
                        </div>
                        <div style="font-size: 12px; color: #9ca3af; margin-top: 5px;">
                            ${new Date(v.created_at).toLocaleString()}
                        </div>
                    </div>
                `).join('');
            }
            
            if (!silent) showNotification('History loaded', 'success');
        }
    } catch (err) {
        if (!silent) showNotification('Failed to load history', 'error');
    }
}

async function loadTransactions(silent = false) {
    if (!token) return;
    
    try {
        const res = await fetch(`${API_BASE}/transactions/history`, {
            headers: {'Authorization': `Bearer ${token}`}
        });
        
        if (res.ok) {
            const data = await res.json();
            const list = document.getElementById('transactions');
            
            if (data.transactions.length === 0) {
                list.innerHTML = '<p style="color: #6b7280;">No transactions yet.</p>';
            } else {
                list.innerHTML = data.transactions.map(t => {
                    const isCredit = t.type === 'credit';
                    const color = isCredit ? '#10b981' : '#ef4444';
                    const sign = isCredit ? '+' : '';
                    return `
                        <div style="background: #f9fafb; padding: 12px; border-radius: 8px; margin-bottom: 8px; border-left: 4px solid ${color};">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <div style="font-size: 14px; color: #374151;">${t.description}</div>
                                    <div style="font-size: 12px; color: #9ca3af; margin-top: 3px;">
                                        ${new Date(t.created_at).toLocaleString()}
                                    </div>
                                </div>
                                <div style="font-weight: bold; font-size: 16px; color: ${color};">
                                    ${sign}₵${Math.abs(t.amount).toFixed(2)}
                                </div>
                            </div>
                        </div>
                    `;
                }).join('');
            }
            
            if (!silent) showNotification('Transactions loaded', 'success');
        }
    } catch (err) {
        if (!silent) showNotification('Failed to load transactions', 'error');
    }
}

async function loadVerification(id) {
    showLoading(true);
    
    try {
        const res = await fetch(`${API_BASE}/verify/${id}`, {
            headers: {'Authorization': `Bearer ${token}`}
        });
        
        showLoading(false);
        
        if (res.ok) {
            const data = await res.json();
            currentVerificationId = id;
            displayVerification(data);
            
            if (data.status === 'pending') {
                startAutoRefresh();
            }
            
            checkMessages(true);
        }
    } catch (err) {
        showLoading(false);
        showNotification('Failed to load verification', 'error');
    }
}

function updateServiceInfo() {
    const service = document.getElementById('service-select').value;
    const timer = getServiceTimer(service);
    const info = document.getElementById('service-info');
    const popular = ['google', 'discord', 'whatsapp', 'telegram', 'instagram', 'facebook', 'twitter', 'tiktok', 'snapchat'];
    const isPopular = popular.includes(service.toLowerCase());
    
    if (timer <= 60) {
        info.innerHTML = `⚡ <strong>Fast service</strong> - ${timer}s wait time ${isPopular ? '✅ Verified' : ''}`;
        info.style.color = '#10b981';
    } else if (timer <= 90) {
        info.innerHTML = `⏱️ <strong>Standard service</strong> - ${timer}s wait time ${isPopular ? '✅ Verified' : ''}`;
        info.style.color = '#f59e0b';
    } else {
        info.innerHTML = `🐌 <strong>Slow service</strong> - ${timer}s wait time (be patient) ${isPopular ? '✅ Verified' : ''}`;
        info.style.color = '#ef4444';
    }
}

function showNotification(message, type) {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `notification ${type}`;
    notification.classList.remove('hidden');
    
    setTimeout(() => {
        notification.classList.add('hidden');
    }, 3000);
}

function showFundWallet() {
    document.getElementById('fund-wallet-modal').classList.remove('hidden');
    document.getElementById('payment-methods').classList.add('hidden');
    document.getElementById('crypto-options').classList.add('hidden');
    document.getElementById('fund-amount').value = '';
}

function closeFundWallet() {
    document.getElementById('fund-wallet-modal').classList.add('hidden');
}

function showForgotPassword() {
    document.getElementById('forgot-password-modal').style.display = 'block';
}

function closeForgotPassword() {
    document.getElementById('forgot-password-modal').style.display = 'none';
    document.getElementById('reset-email').value = '';
}

async function sendResetEmail() {
    const email = document.getElementById('reset-email').value;
    if (!email) {
        showNotification('Please enter your email', 'error');
        return;
    }
    try {
        const response = await fetch('/auth/forgot-password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email })
        });
        const data = await response.json();
        if (response.ok) {
            showNotification('Password reset link sent to your email', 'success');
            closeForgotPassword();
        } else {
            showNotification(data.detail || 'Failed to send reset link', 'error');
        }
    } catch (error) {
        showNotification('Network error', 'error');
    }
}

function showCryptoPayment(data, method, amount) {
    const modal = document.getElementById('fund-wallet-modal');
    const content = modal.querySelector('.modal-content');
    
    content.innerHTML = `
        <span class="close" onclick="closeFundWallet()">&times;</span>
        <h2>💳 ${data.currency} Payment</h2>
        <p style="color: #6b7280; margin-bottom: 20px;">Send exactly $${amount} USD worth of ${data.currency}</p>
        
        <div style="text-align: center; margin: 20px 0;">
            <img src="${data.qr_code}" alt="QR Code" style="max-width: 300px; border: 2px solid #e5e7eb; border-radius: 8px;">
        </div>
        
        <div style="background: #f9fafb; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <label style="font-weight: bold; display: block; margin-bottom: 5px;">Payment Address:</label>
            <div style="display: flex; gap: 10px; align-items: center;">
                <input type="text" value="${data.address}" readonly 
                       style="flex: 1; padding: 10px; border: 2px solid #e5e7eb; border-radius: 6px; font-family: monospace; font-size: 12px;">
                <button onclick="copyToClipboard('${data.address}')" class="btn-small">Copy</button>
            </div>
        </div>
        
        <div style="background: #fef3c7; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #f59e0b;">
            <p style="margin: 0; font-size: 14px; color: #92400e;">
                ⚠️ After sending payment, click "I've Sent Payment" below. Your wallet will be credited within 10-30 minutes.
            </p>
        </div>
        
        <button onclick="confirmCryptoPayment('${method}', ${amount})" style="width: 100%; margin-bottom: 10px;">✅ I've Sent Payment</button>
        <button onclick="showFundWallet()" style="width: 100%; background: #6b7280;">← Back</button>
    `;
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text);
    showNotification('✅ Address copied to clipboard!', 'success');
}

function confirmCryptoPayment(method, amount) {
    showNotification('🕒 Payment confirmation received. Processing...', 'success');
    setTimeout(() => processPayment(method, amount), 1000);
}

async function createAPIKey() {
    const name = document.getElementById('api-key-name').value;
    if (!name) {
        showNotification('⚠️ Please enter a key name', 'error');
        return;
    }
    
    try {
        const res = await fetch(`${API_BASE}/api-keys/create`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name })
        });
        
        if (res.ok) {
            const data = await res.json();
            showNotification(`✅ API key created: ${data.key}`, 'success');
            document.getElementById('api-key-name').value = '';
            loadAPIKeys();
        } else {
            showNotification('❌ Failed to create API key', 'error');
        }
    } catch (err) {
        showNotification('🌐 Network error', 'error');
    }
}

async function loadAPIKeys() {
    if (!token) return;
    
    try {
        const res = await fetch(`${API_BASE}/api-keys/list`, {
            headers: {'Authorization': `Bearer ${token}`}
        });
        
        if (res.ok) {
            const data = await res.json();
            const list = document.getElementById('api-keys-list');
            
            if (data.keys.length === 0) {
                list.innerHTML = '<p style="color: #6b7280;">No API keys yet.</p>';
            } else {
                list.innerHTML = data.keys.map(k => `
                    <div style="background: #f9fafb; padding: 12px; border-radius: 8px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong>${k.name}</strong>
                            <div style="font-size: 12px; color: #6b7280; font-family: monospace;">${k.key}</div>
                        </div>
                        <button onclick="deleteAPIKey('${k.id}')" class="btn-small btn-danger">Delete</button>
                    </div>
                `).join('');
            }
        }
    } catch (err) {
        console.error('Failed to load API keys:', err);
    }
}

async function deleteAPIKey(keyId) {
    if (!confirm('Delete this API key?')) return;
    
    try {
        const res = await fetch(`${API_BASE}/api-keys/${keyId}`, {
            method: 'DELETE',
            headers: {'Authorization': `Bearer ${token}`}
        });
        
        if (res.ok) {
            showNotification('✅ API key deleted', 'success');
            loadAPIKeys();
        }
    } catch (err) {
        showNotification('❌ Failed to delete API key', 'error');
    }
}

async function createWebhook() {
    const url = document.getElementById('webhook-url').value;
    if (!url || !url.startsWith('http')) {
        showNotification('⚠️ Please enter a valid URL', 'error');
        return;
    }
    
    try {
        const res = await fetch(`${API_BASE}/webhooks/create`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ url })
        });
        
        if (res.ok) {
            showNotification('✅ Webhook created', 'success');
            document.getElementById('webhook-url').value = '';
            loadWebhooks();
        } else {
            showNotification('❌ Failed to create webhook', 'error');
        }
    } catch (err) {
        showNotification('🌐 Network error', 'error');
    }
}

async function loadWebhooks() {
    if (!token) return;
    
    try {
        const res = await fetch(`${API_BASE}/webhooks/list`, {
            headers: {'Authorization': `Bearer ${token}`}
        });
        
        if (res.ok) {
            const data = await res.json();
            const list = document.getElementById('webhooks-list');
            
            if (data.webhooks.length === 0) {
                list.innerHTML = '<p style="color: #6b7280;">No webhooks configured.</p>';
            } else {
                list.innerHTML = data.webhooks.map(w => `
                    <div style="background: #f9fafb; padding: 12px; border-radius: 8px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-size: 14px; color: #374151; word-break: break-all;">${w.url}</div>
                            <div style="font-size: 12px; color: #6b7280; margin-top: 3px;">
                                ${w.is_active ? '✅ Active' : '❌ Inactive'} • ${new Date(w.created_at).toLocaleDateString()}
                            </div>
                        </div>
                        <button onclick="deleteWebhook('${w.id}')" class="btn-small btn-danger">Delete</button>
                    </div>
                `).join('');
            }
        }
    } catch (err) {
        console.error('Failed to load webhooks:', err);
    }
}

async function deleteWebhook(webhookId) {
    if (!confirm('Delete this webhook?')) return;
    
    try {
        const res = await fetch(`${API_BASE}/webhooks/${webhookId}`, {
            method: 'DELETE',
            headers: {'Authorization': `Bearer ${token}`}
        });
        
        if (res.ok) {
            showNotification('✅ Webhook deleted', 'success');
            loadWebhooks();
        }
    } catch (err) {
        showNotification('❌ Failed to delete webhook', 'error');
    }
}

async function loadNotificationSettings() {
    if (!token) return;
    
    try {
        const res = await fetch(`${API_BASE}/notifications/settings`, {
            headers: {'Authorization': `Bearer ${token}`}
        });
        
        if (res.ok) {
            const data = await res.json();
            document.getElementById('email-on-sms').checked = data.email_on_sms;
            document.getElementById('email-on-low-balance').checked = data.email_on_low_balance;
            document.getElementById('low-balance-threshold').value = data.low_balance_threshold;
        }
    } catch (err) {
        console.error('Failed to load notification settings:', err);
    }
}

async function updateNotificationSettings() {
    if (!token) return;
    
    const emailOnSms = document.getElementById('email-on-sms').checked;
    const emailOnLowBalance = document.getElementById('email-on-low-balance').checked;
    const threshold = parseFloat(document.getElementById('low-balance-threshold').value);
    
    try {
        const res = await fetch(`${API_BASE}/notifications/settings?email_on_sms=${emailOnSms}&email_on_low_balance=${emailOnLowBalance}&low_balance_threshold=${threshold}`, {
            method: 'POST',
            headers: {'Authorization': `Bearer ${token}`}
        });
        
        if (res.ok) {
            showNotification('✅ Notification settings updated', 'success');
        }
    } catch (err) {
        showNotification('❌ Failed to update settings', 'error');
    }
}

async function loadReferralStats() {
    if (!token) return;
    
    try {
        const res = await fetch(`${API_BASE}/referrals/stats`, {
            headers: {'Authorization': `Bearer ${token}`}
        });
        
        if (res.ok) {
            const data = await res.json();
            
            document.getElementById('referral-code').textContent = data.referral_code;
            document.getElementById('referral-link').value = data.referral_link;
            document.getElementById('total-referrals').textContent = data.total_referrals;
            document.getElementById('referral-earnings').textContent = `₵${data.total_earnings.toFixed(2)}`;
            
            const usersList = document.getElementById('referred-users');
            if (data.referred_users.length === 0) {
                usersList.innerHTML = '<p style="color: #6b7280; text-align: center; margin-top: 15px;">No referrals yet. Share your link to start earning!</p>';
            } else {
                usersList.innerHTML = `
                    <h4 style="margin: 15px 0 10px 0;">Referred Users</h4>
                    ${data.referred_users.map(u => `
                        <div style="background: #f9fafb; padding: 10px; border-radius: 6px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <div style="font-size: 14px; color: #374151;">${u.email}</div>
                                <div style="font-size: 12px; color: #6b7280;">${new Date(u.joined_at).toLocaleDateString()}</div>
                            </div>
                            <div style="color: #10b981; font-weight: bold;">+₵${u.reward.toFixed(2)}</div>
                        </div>
                    `).join('')}
                `;
            }
        }
    } catch (err) {
        console.error('Failed to load referral stats:', err);
    }
}

function copyReferralLink() {
    const link = document.getElementById('referral-link').value;
    navigator.clipboard.writeText(link);
    showNotification('✅ Referral link copied!', 'success');
}

async function loadAnalytics() {
    if (!token) return;
    
    try {
        const res = await fetch(`${API_BASE}/analytics/dashboard`, {
            headers: {'Authorization': `Bearer ${token}`}
        });
        
        if (res.ok) {
            const data = await res.json();
            
            // Update stats
            document.getElementById('stat-total').textContent = data.total_verifications;
            document.getElementById('stat-success').textContent = `${data.success_rate}%`;
            document.getElementById('stat-spent').textContent = `₵${data.total_spent.toFixed(2)}`;
            document.getElementById('stat-recent').textContent = data.recent_verifications;
            
            // Daily chart
            const chart = document.getElementById('daily-chart');
            const maxCount = Math.max(...data.daily_usage.map(d => d.count), 1);
            
            chart.innerHTML = data.daily_usage.map(day => {
                const height = (day.count / maxCount) * 100;
                return `
                    <div style="flex: 1; display: flex; flex-direction: column; align-items: center;">
                        <div style="width: 100%; background: #667eea; border-radius: 4px 4px 0 0; height: ${height}%; min-height: 5px; position: relative;">
                            <span style="position: absolute; top: -20px; left: 50%; transform: translateX(-50%); font-size: 12px; font-weight: bold; color: #667eea;">${day.count}</span>
                        </div>
                        <div style="font-size: 10px; color: #6b7280; margin-top: 5px; transform: rotate(-45deg); white-space: nowrap;">${new Date(day.date).toLocaleDateString('en-US', {month: 'short', day: 'numeric'})}</div>
                    </div>
                `;
            }).join('');
            
            // Popular services
            const popularList = document.getElementById('popular-services');
            if (data.popular_services.length === 0) {
                popularList.innerHTML = '<p style="color: #6b7280;">No data yet. Start verifying!</p>';
            } else {
                popularList.innerHTML = data.popular_services.map((s, i) => `
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px; background: white; border-radius: 6px; margin-bottom: 8px;">
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <span style="font-size: 20px;">${['🥇', '🥈', '🥉', '4️⃣', '5️⃣'][i]}</span>
                            <strong>${formatServiceName(s.service)}</strong>
                        </div>
                        <span style="background: #667eea; color: white; padding: 4px 12px; border-radius: 12px; font-size: 14px;">${s.count}</span>
                    </div>
                `).join('');
            }
        }
    } catch (err) {
        console.error('Failed to load analytics:', err);
    }
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
    
    const methodNames = {
        'paystack': '🏦 Paystack',
        'bitcoin': '₿ Bitcoin',
        'ethereum': 'Ξ Ethereum',
        'solana': '◎ Solana',
        'usdt': '₮ USDT'
    };
    
    showLoading(true);
    
    try {
        if (method === 'paystack') {
            // Initialize Paystack payment
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
                showNotification('🚀 Redirecting to Paystack...', 'success');
                // In production, redirect to data.authorization_url
                setTimeout(() => processPayment(method, amount), 1500);
            } else {
                throw new Error('Paystack initialization failed');
            }
        } else {
            // Get crypto address
            const res = await fetch(`${API_BASE}/wallet/crypto/address`, {
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
                showCryptoPayment(data, method, amount);
            } else {
                throw new Error('Crypto address generation failed');
            }
        }
    } catch (err) {
        showLoading(false);
        showNotification('❌ Payment initialization failed', 'error');
    }
}

async function processPayment(method, amount) {
    try {
        const res = await fetch(`${API_BASE}/wallet/fund`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ amount, payment_method: method })
        });
        
        showLoading(false);
        
        if (res.ok) {
            const data = await res.json();
            document.getElementById('user-credits').textContent = data.new_balance.toFixed(2);
            closeFundWallet();
            showNotification(`✅ ${data.message}`, 'success');
            loadTransactions(true);
        } else {
            const data = await res.json();
            showNotification(`❌ ${data.detail}`, 'error');
        }
    } catch (err) {
        showLoading(false);
        showNotification('❌ Payment processing failed', 'error');
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
