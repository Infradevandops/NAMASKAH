// Verification Module
let currentVerificationId = null;
let autoRefreshInterval = null;
let countdownInterval = null;
let countdownSeconds = 45;
let currentServiceName = null;
let firstVerificationCompleted = false;

// Dynamic pricing function
async function getServicePrice(serviceName, capability = 'sms') {
    if (!window.token) return null;
    
    try {
        const res = await fetch(`${API_BASE}/services/price/${serviceName}`, {
            headers: {'Authorization': `Bearer ${window.token}`}
        });
        if (res.ok) {
            const data = await res.json();
            return capability === 'voice' 
                ? (data.base_price + data.voice_premium).toFixed(2)
                : data.base_price.toFixed(2);
        }
    } catch (err) {
        console.error('Price fetch error:', err);
    }
    return null;
}

// Get tier name for display
function getTierName(serviceName) {
    const tierMap = {
        'whatsapp': 'High-Demand',
        'telegram': 'High-Demand', 
        'discord': 'High-Demand',
        'google': 'High-Demand',
        'instagram': 'Standard',
        'facebook': 'Standard',
        'twitter': 'Standard',
        'tiktok': 'Standard',
        'paypal': 'Premium',
        'venmo': 'Premium',
        'cashapp': 'Premium'
    };
    return tierMap[serviceName.toLowerCase()] || 'Specialty';
}

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
    const capabilityEl = document.querySelector('input[name="capability"]:checked');
    const capability = capabilityEl ? capabilityEl.value : 'sms';
    
    if (!service) {
        showNotification('⚠️ Please select a service', 'error');
        return;
    }
    
    if (!window.token) {
        showNotification('🔒 Please login first', 'error');
        return;
    }
    
    // Get dynamic price before creating
    const price = await getServicePrice(service, capability);
    if (price === null) {
        showNotification('⚠️ Unable to get pricing. Try again.', 'error');
        return;
    }
    
    // Get carrier and area code selections
    const carrierSelect = document.getElementById('carrier-select');
    const areaCodeSelect = document.getElementById('area-code-select');
    const carrier = carrierSelect ? carrierSelect.value : null;
    const areaCode = areaCodeSelect ? areaCodeSelect.value : null;
    
    showLoading(true);
    
    // Build request body with optional carrier and area code
    const requestBody = {
        service_name: service, 
        capability: capability
    };
    
    if (carrier) requestBody.carrier = carrier;
    if (areaCode) requestBody.area_code = areaCode;
    
    try {
        const res = await fetch(`${API_BASE}/verify/create`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${window.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });
        
        const data = await res.json();
        showLoading(false);
        
        if (res.ok) {
            currentVerificationId = data.id;
            displayVerification(data);
            document.getElementById('user-credits').textContent = data.remaining_credits.toFixed(2);
            showNotification(`✅ Verification created! Cost: N${data.cost} (${getTierName(service)})`, 'success');
            startAutoRefresh();
            if (typeof loadHistory === 'function') loadHistory();
            if (typeof loadTransactions === 'function') loadTransactions(true);
            
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
    
    // Display carrier and area code info if available
    const infoContainer = document.getElementById('verification-info');
    if (infoContainer && (data.carrier_info || data.user_selections)) {
        let infoHTML = '';
        
        if (data.carrier_info && data.carrier_info.name) {
            infoHTML += `<div class="detail-row"><strong>Carrier:</strong> <span>${data.carrier_info.full_display || data.carrier_info.name}</span></div>`;
        }
        
        if (data.user_selections) {
            if (data.user_selections.requested_carrier) {
                infoHTML += `<div class="detail-row"><strong>Requested Carrier:</strong> <span class="requested-badge">${data.user_selections.requested_carrier}</span></div>`;
            }
            if (data.user_selections.requested_area_code) {
                infoHTML += `<div class="detail-row"><strong>Requested Area Code:</strong> <span class="requested-badge">${data.user_selections.requested_area_code}</span></div>`;
            }
        }
        
        infoContainer.innerHTML = infoHTML;
    }
    
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

function showRetryModal() {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.style.display = 'block';
    modal.innerHTML = `
        <div class="modal-content" style="max-width: 500px;">
            <h2>No SMS Received</h2>
            <p style="color: #6b7280; margin-bottom: 20px;">The verification code was not received. Choose an option:</p>
            
            <div style="display: flex; flex-direction: column; gap: 12px;">
                <button onclick="retryWithVoice()" style="background: #10b981; padding: 15px; font-size: 16px; font-weight: 600;">
                    📞 Try Voice Verification
                    <div style="font-size: 13px; opacity: 0.9; margin-top: 5px;">SMS refunded, voice charged after code arrives</div>
                </button>
                
                <button onclick="retryWithSame()" style="background: #667eea; padding: 15px; font-size: 16px; font-weight: 600;">
                    🔄 Retry Same Number
                    <div style="font-size: 13px; opacity: 0.9; margin-top: 5px;">Try again with current number</div>
                </button>
                
                <button onclick="retryWithNew()" style="background: #f59e0b; padding: 15px; font-size: 16px; font-weight: 600;">
                    🆕 Get New Number
                    <div style="font-size: 13px; opacity: 0.9; margin-top: 5px;">Request different number</div>
                </button>
                
                <button onclick="closeRetryModal()" style="background: #ef4444; padding: 12px;">
                    Cancel
                </button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

function closeRetryModal() {
    const modal = document.querySelector('.modal');
    if (modal) modal.remove();
}

async function retryWithVoice() {
    closeRetryModal();
    showLoading(true);
    
    try {
        const res = await fetch(`${API_BASE}/verify/${currentVerificationId}/retry`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${window.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({retry_type: 'voice'})
        });
        
        const data = await res.json();
        showLoading(false);
        
        if (res.ok) {
            displayVerification(data);
            showNotification('✅ Switched to voice verification', 'success');
            startAutoRefresh();
        } else {
            showNotification(`❌ ${data.detail || 'Failed to switch to voice'}`, 'error');
        }
    } catch (err) {
        showLoading(false);
        showNotification('🌐 Network error', 'error');
    }
}

async function retryWithSame() {
    closeRetryModal();
    showLoading(true);
    
    try {
        const res = await fetch(`${API_BASE}/verify/${currentVerificationId}/retry`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${window.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({retry_type: 'same'})
        });
        
        const data = await res.json();
        showLoading(false);
        
        if (res.ok) {
            displayVerification(data);
            showNotification('✅ Retrying with same number', 'success');
            startAutoRefresh();
        } else {
            showNotification(`❌ ${data.detail || 'Failed to retry'}`, 'error');
        }
    } catch (err) {
        showLoading(false);
        showNotification('🌐 Network error', 'error');
    }
}

async function retryWithNew() {
    closeRetryModal();
    showLoading(true);
    
    try {
        const res = await fetch(`${API_BASE}/verify/${currentVerificationId}/retry`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${window.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({retry_type: 'new'})
        });
        
        const data = await res.json();
        showLoading(false);
        
        if (res.ok) {
            currentVerificationId = data.id;
            displayVerification(data);
            showNotification('✅ New number assigned', 'success');
            startAutoRefresh();
        } else {
            showNotification(`❌ ${data.detail || 'Failed to get new number'}`, 'error');
        }
    } catch (err) {
        showLoading(false);
        showNotification('🌐 Network error', 'error');
    }
}

async function autoCancel() {
    if (!currentVerificationId) return;
    
    try {
        const res = await fetch(`${API_BASE}/verify/${currentVerificationId}/messages`, {
            headers: {'Authorization': `Bearer ${window.token}`}
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
    
    stopAutoRefresh();
    stopCountdown();
    showRetryModal();
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
                'Authorization': `Bearer ${window.token}`,
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
            headers: {'Authorization': `Bearer ${window.token}`}
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
            headers: {'Authorization': `Bearer ${window.token}`}
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
            
            const extractedCodes = data.messages.map(msg => {
                const codeMatch = msg.match(/\b\d{4,8}\b/);
                return codeMatch ? codeMatch[0] : msg;
            });
            
            messagesList.innerHTML = `
                <div style="background: #10b981; color: white; padding: 20px; border-radius: 12px; margin-bottom: 20px;">
                    <h2 style="margin: 0 0 8px 0; font-size: 20px;">Verification Code Received</h2>
                    <p style="margin: 0; opacity: 0.9;">Your verification code has arrived successfully</p>
                </div>
                <div style="background: #f0fdf4; padding: 15px; border-radius: 8px; border: 2px solid #10b981; margin-bottom: 15px;">
                    <h4 style="color: #166534; margin: 0 0 10px 0;">SMS Messages:</h4>
                    ${data.messages.map((msg, idx) => {
                        const code = extractedCodes[idx];
                        return `<div style="background: white; padding: 12px; margin: 8px 0; border-radius: 6px; border: 1px solid #d1fae5;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                <strong style="color: #166534;">Code:</strong>
                                <button onclick="copyCode('${code}')" style="background: #10b981; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: 600;">Copy Code</button>
                            </div>
                            <code style="font-family: monospace; font-size: 18px; color: #166534; display: block; background: #f0fdf4; padding: 10px; border-radius: 4px; text-align: center; font-weight: bold;">${code}</code>
                            <details style="margin-top: 8px;">
                                <summary style="cursor: pointer; color: #6b7280; font-size: 13px;">Full message</summary>
                                <div style="margin-top: 8px; font-size: 13px; color: #6b7280;">${msg}</div>
                            </details>
                        </div>`;
                    }).join('')}
                </div>
                <button onclick="tryAnotherService()" style="margin-top: 15px; width: 100%; background: #667eea; color: white; padding: 14px; font-size: 16px; font-weight: 600; border: none; border-radius: 8px; cursor: pointer;">Try Another Service</button>
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

function copyCode(code) {
    navigator.clipboard.writeText(code).then(() => {
        showNotification(`Code ${code} copied to clipboard`, 'success');
    }).catch(() => {
        showNotification('Failed to copy code', 'error');
    });
}

function tryAnotherService() {
    clearSession();
    document.getElementById('service-select').scrollIntoView({ behavior: 'smooth' });
    document.getElementById('service-select').focus();
    showNotification('Select a new service to verify', 'success');
}

async function cancelVerification() {
    if (!currentVerificationId) {
        showNotification('⚠️ No active verification to cancel', 'error');
        return;
    }
    
    if (!confirm('Cancel this verification and get refund?')) return;
    
    showLoading(true);
    stopCountdown();
    stopAutoRefresh();
    
    try {
        const res = await fetch(`${API_BASE}/verify/${currentVerificationId}`, {
            method: 'DELETE',
            headers: {'Authorization': `Bearer ${window.token}`}
        });
        
        const data = await res.json();
        showLoading(false);
        
        if (res.ok) {
            if (typeof updateUserCredits === 'function') {
                updateUserCredits(data.new_balance);
            } else {
                document.getElementById('user-credits').textContent = data.new_balance.toFixed(2);
            }
            showNotification(`✅ Cancelled! Refunded N${data.refunded.toFixed(2)}`, 'success');
            clearSession();
            if (typeof loadHistory === 'function') loadHistory();
            if (typeof loadTransactions === 'function') loadTransactions(true);
        } else {
            if (res.status === 404) {
                showNotification('❌ Verification not found or already cancelled', 'error');
            } else if (res.status === 401) {
                showNotification('🔒 Session expired. Please login again', 'error');
                setTimeout(() => logout(), 2000);
            } else {
                showNotification(`❌ ${data.detail || 'Failed to cancel verification'}`, 'error');
            }
        }
    } catch (err) {
        showLoading(false);
        showNotification('🌐 Network error. Please try again', 'error');
        console.error('Cancel verification error:', err);
    }
}

async function checkVoiceCall() {
    if (!currentVerificationId) return;
    
    showLoading(true);
    
    try {
        const res = await fetch(`${API_BASE}/verify/${currentVerificationId}/voice`, {
            headers: { 'Authorization': `Bearer ${window.token}` }
        });
        
        showLoading(false);
        
        if (res.ok) {
            const data = await res.json();
            const messagesList = document.getElementById('messages-list');
            
            const transcriptionCode = data.transcription ? data.transcription.match(/\b\d{4,8}\b/)?.[0] : null;
            
            messagesList.innerHTML = `
                <div style="background: #10b981; color: white; padding: 20px; border-radius: 12px; margin-bottom: 20px;">
                    <h2 style="margin: 0 0 8px 0; font-size: 20px;">Voice Call Details</h2>
                    <p style="margin: 0; opacity: 0.9;">Your voice verification has been received</p>
                </div>
                <div style="background: #f0fdf4; padding: 15px; border-radius: 8px; border: 2px solid #10b981; margin-bottom: 15px;">
                    <div style="margin-bottom: 10px;"><strong>Phone:</strong> ${formatPhoneNumber(data.phone_number)}</div>
                    <div style="margin-bottom: 10px;"><strong>Duration:</strong> ${data.call_duration || 'N/A'}</div>
                    ${data.transcription ? `
                        <div style="background: white; padding: 12px; margin: 8px 0; border-radius: 6px; border: 1px solid #d1fae5;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                <strong style="color: #166534;">Code:</strong>
                                <button onclick="copyCode('${transcriptionCode || data.transcription}')" style="background: #10b981; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: 600;">Copy Code</button>
                            </div>
                            <code style="font-family: monospace; font-size: 18px; color: #166534; display: block; background: #f0fdf4; padding: 10px; border-radius: 4px; text-align: center; font-weight: bold;">${transcriptionCode || data.transcription}</code>
                            <details style="margin-top: 8px;">
                                <summary style="cursor: pointer; color: #6b7280; font-size: 13px;">Full transcription</summary>
                                <div style="margin-top: 8px; font-size: 13px; color: #6b7280;">${data.transcription}</div>
                            </details>
                        </div>
                    ` : ''}
                    ${data.audio_url ? `<div style="margin-top: 10px;"><audio controls src="${data.audio_url}" style="width: 100%;"></audio></div>` : ''}
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
