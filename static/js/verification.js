// Verification Module
let currentVerificationId = null;
let autoRefreshInterval = null;
let countdownInterval = null;
let countdownSeconds = 45;
let currentServiceName = null;
let firstVerificationCompleted = false;

const serviceTimers = {
    'google': 60, 'discord': 60, 'whatsapp': 90, 'telegram': 90,
    'instagram': 120, 'facebook': 90, 'twitter': 75, 'tiktok': 90,
    'snapchat': 75, 'default': 60
};

function getServiceTimer(serviceName) {
    return serviceTimers[serviceName.toLowerCase()] || serviceTimers['default'];
}

async function createVerification() {
    const service = document.getElementById('service-select').value;
    const capability = document.querySelector('input[name="capability"]:checked').value;
    
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
            body: JSON.stringify({service_name: service, capability: capability})
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
    
    const isVoice = data.capability === 'voice';
    document.getElementById('check-messages-btn').classList.toggle('hidden', isVoice);
    document.getElementById('check-voice-btn').classList.toggle('hidden', !isVoice);
    
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
    }, 10000);
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
    
    try {
        const res = await fetch(`${API_BASE}/verify/${currentVerificationId}/messages`, {
            headers: {'Authorization': `Bearer ${token}`}
        });
        
        if (res.ok) {
            const data = await res.json();
            if (data.messages && data.messages.length > 0) {
                stopCountdown();
                showNotification('SMS received!', 'success');
                checkMessages(true);
                return;
            }
        }
    } catch (err) {}
    
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
    
    document.getElementById('retry-btn').classList.add('hidden');
    document.getElementById('verification-details').classList.add('hidden');
    
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
    } catch (err) {}
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
    clearSession();
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
            clearSession();
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

async function checkVoiceCall() {
    if (!currentVerificationId) return;
    
    showLoading(true);
    
    try {
        const res = await fetch(`${API_BASE}/verify/${currentVerificationId}/voice`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        showLoading(false);
        
        if (res.ok) {
            const data = await res.json();
            const messagesList = document.getElementById('messages-list');
            
            messagesList.innerHTML = `
                <div style="background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); padding: 25px; border-radius: 12px; margin-bottom: 20px; border: 3px solid #10b981;">
                    <h2 style="color: #065f46; margin: 0 0 12px 0; font-size: 24px; text-align: center;">📞 Voice Call Details</h2>
                </div>
                <div style="background: #f0fdf4; padding: 15px; border-radius: 8px; border-left: 4px solid #22c55e; margin-bottom: 15px;">
                    <div style="margin-bottom: 10px;"><strong>Phone:</strong> ${formatPhoneNumber(data.phone_number)}</div>
                    <div style="margin-bottom: 10px;"><strong>Duration:</strong> ${data.call_duration || 'N/A'}</div>
                    ${data.transcription ? `<div style="margin-bottom: 10px;"><strong>Transcription:</strong> ${data.transcription}</div>` : ''}
                    ${data.audio_url ? `<div><audio controls src="${data.audio_url}" style="width: 100%;"></audio></div>` : ''}
                </div>
            `;
            
            document.getElementById('messages-section').classList.remove('hidden');
            stopAutoRefresh();
            stopCountdown();
            showNotification('📞 Voice call retrieved!', 'success');
        } else {
            const data = await res.json();
            showNotification(data.detail || 'Failed to get voice call', 'error');
        }
    } catch (error) {
        showLoading(false);
        showNotification('Network error', 'error');
    }
}

function clearSession() {
    currentVerificationId = null;
    currentServiceName = null;
    stopAutoRefresh();
    stopCountdown();
    
    document.getElementById('verification-details').classList.add('hidden');
    document.getElementById('messages-section').classList.add('hidden');
}
