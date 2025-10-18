// Rentals Module
let rentalMessagesCache = {};

const RENTAL_SERVICE_SPECIFIC = {
    168: 5.0, 336: 9.0, 720: 16.0, 1440: 28.0, 2160: 38.0, 8760: 50.0
};

const RENTAL_GENERAL_USE = {
    168: 6.0, 336: 11.0, 720: 20.0, 1440: 35.0, 2160: 48.0, 8760: 80.0
};

function showRentalModal() {
    document.getElementById('rental-modal').classList.remove('hidden');
    updateRentalPrice();
}

function closeRentalModal() {
    document.getElementById('rental-modal').classList.add('hidden');
}

function updateRentalPrice() {
    const service = document.getElementById('rental-service')?.value || 'telegram';
    const modeChecked = document.querySelector('input[name="rental-mode"]:checked');
    const durationChecked = document.querySelector('input[name="rental-duration"]:checked');
    
    if (!modeChecked || !durationChecked) return;
    
    const mode = modeChecked.value;
    const duration = parseInt(durationChecked.value);
    
    const isGeneral = service.toLowerCase() === 'general';
    const pricingTable = isGeneral ? RENTAL_GENERAL_USE : RENTAL_SERVICE_SPECIFIC;
    
    const basePrice = pricingTable[duration];
    const modeMultiplier = mode === 'manual' ? 0.7 : 1.0;
    
    const totalPrice = (basePrice || 5.0) * modeMultiplier;
    
    Object.keys(pricingTable).forEach(hours => {
        const price = pricingTable[hours] * modeMultiplier;
        const days = hours / 24;
        const priceElement = document.getElementById(`price-${days}`);
        if (priceElement) {
            priceElement.textContent = `$${(price * 2).toFixed(2)}`;
        }
    });
    
    const totalElement = document.getElementById('rental-total');
    if (totalElement) {
        totalElement.textContent = `$${(totalPrice * 2).toFixed(2)}`;
    }
    
    const days = duration / 24;
    const expiryDate = new Date();
    expiryDate.setDate(expiryDate.getDate() + days);
    document.getElementById('rental-expiry').textContent = expiryDate.toLocaleDateString();
}

function toggleCustomRentalService() {
    const service = document.getElementById('rental-service').value;
    const customInput = document.getElementById('custom-rental-service');
    if (service === 'custom') {
        customInput.style.display = 'block';
    } else {
        customInput.style.display = 'none';
    }
}

async function createRentalNumber() {
    let service = document.getElementById('rental-service').value;
    
    if (service === 'custom') {
        service = document.getElementById('custom-rental-service').value.trim().toLowerCase();
        if (!service) {
            showNotification('⚠️ Please enter a service name', 'error');
            return;
        }
    }
    
    const mode = document.querySelector('input[name="rental-mode"]:checked').value;
    const duration = parseInt(document.querySelector('input[name="rental-duration"]:checked').value);
    
    showLoading(true);
    
    try {
        const res = await fetch(`${API_BASE}/rentals/create`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                service_name: service,
                duration_hours: duration,
                mode: mode,
                auto_extend: false
            })
        });
        
        const data = await res.json();
        showLoading(false);
        
        if (res.ok) {
            showNotification(`✅ Number rented! ${data.phone_number}`, 'success');
            document.getElementById('user-credits').textContent = data.remaining_credits.toFixed(2);
            closeRentalModal();
            loadActiveRentals();
            loadTransactions(true);
        } else {
            showNotification(`❌ ${data.detail}`, 'error');
        }
    } catch (err) {
        showLoading(false);
        showNotification('🌐 Network error', 'error');
    }
}

async function loadActiveRentals() {
    if (!token) return;
    
    try {
        const res = await fetch(`${API_BASE}/rentals/active`, {
            headers: {'Authorization': `Bearer ${token}`}
        });
        
        if (res.ok) {
            const data = await res.json();
            const section = document.getElementById('active-rentals-section');
            const list = document.getElementById('active-rentals-list');
            
            if (data.rentals.length === 0) {
                section.style.display = 'none';
            } else {
                section.style.display = 'block';
                list.innerHTML = data.rentals.map(r => {
                    const timeRemaining = r.time_remaining_seconds;
                    const days = Math.floor(timeRemaining / 86400);
                    const hours = Math.floor((timeRemaining % 86400) / 3600);
                    
                    return `
                        <div style="background: var(--bg-secondary); padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #8b5cf6;">
                            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 10px;">
                                <div>
                                    <div style="font-size: 1.2rem; font-weight: bold; color: var(--text-primary);">${r.phone_number}</div>
                                    <div style="font-size: 0.9rem; color: var(--text-secondary); text-transform: capitalize;">${r.service_name} • ${r.auto_extend ? 'Auto-extend' : 'Manual'}</div>
                                </div>
                                <span style="background: #10b981; color: white; padding: 4px 12px; border-radius: 12px; font-size: 0.85rem;">Active</span>
                            </div>
                            <div style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 10px;">
                                ⏰ Expires in: <strong>${days}d ${hours}h</strong>
                            </div>
                            <div id="rental-messages-${r.id}" style="background: var(--bg); padding: 10px; border-radius: 6px; margin-bottom: 10px; max-height: 200px; overflow-y: auto; display: none;">
                                <div style="font-weight: 600; margin-bottom: 8px; color: var(--text-primary);">📨 Messages:</div>
                                <div id="rental-messages-content-${r.id}" style="font-size: 0.85rem;">Loading...</div>
                            </div>
                            <div style="display: flex; gap: 8px;">
                                <button onclick="toggleRentalMessages('${r.id}')" class="btn-small" style="flex: 1;">📨 View SMS</button>
                                <button onclick="extendRental('${r.id}')" class="btn-small" style="flex: 1;">🔄 Extend</button>
                                <button onclick="releaseRental('${r.id}')" class="btn-small btn-danger" style="flex: 1;">🚫 Release</button>
                            </div>
                        </div>
                    `;
                }).join('');
            }
        }
    } catch (err) {
        console.error('Failed to load rentals:', err);
    }
}

async function toggleRentalMessages(rentalId) {
    const container = document.getElementById(`rental-messages-${rentalId}`);
    const content = document.getElementById(`rental-messages-content-${rentalId}`);
    
    if (container.style.display === 'none') {
        container.style.display = 'block';
        
        if (!rentalMessagesCache[rentalId]) {
            try {
                const res = await fetch(`${API_BASE}/rentals/${rentalId}/messages`, {
                    headers: {'Authorization': `Bearer ${token}`}
                });
                
                if (res.ok) {
                    const data = await res.json();
                    rentalMessagesCache[rentalId] = data.messages;
                    
                    if (data.messages.length === 0) {
                        content.innerHTML = '<div style="color: var(--text-secondary); font-style: italic;">No messages yet</div>';
                    } else {
                        content.innerHTML = data.messages.map(msg => {
                            const codeMatch = msg.match(/\b\d{4,8}\b/);
                            const code = codeMatch ? codeMatch[0] : msg;
                            return `<div style="padding: 8px; background: var(--bg-secondary); border-radius: 4px; margin-bottom: 6px; border-left: 3px solid #667eea;">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                                    <strong style="font-size: 16px; color: var(--text-primary);">${code}</strong>
                                    <button onclick="copyCode('${code}')" style="background: #10b981; color: white; border: none; padding: 4px 12px; border-radius: 4px; cursor: pointer; font-size: 12px; font-weight: 600;">Copy</button>
                                </div>
                                <details style="font-size: 12px; color: var(--text-secondary);">
                                    <summary style="cursor: pointer;">Full message</summary>
                                    <div style="margin-top: 4px;">${msg}</div>
                                </details>
                            </div>`;
                        }).join('');
                    }
                } else {
                    content.innerHTML = '<div style="color: #ef4444;">Failed to load messages</div>';
                }
            } catch (error) {
                content.innerHTML = '<div style="color: #ef4444;">Error loading messages</div>';
            }
        } else {
            if (rentalMessagesCache[rentalId].length === 0) {
                content.innerHTML = '<div style="color: var(--text-secondary); font-style: italic;">No messages yet</div>';
            } else {
                content.innerHTML = rentalMessagesCache[rentalId].map(msg => {
                    const codeMatch = msg.match(/\b\d{4,8}\b/);
                    const code = codeMatch ? codeMatch[0] : msg;
                    return `<div style="padding: 8px; background: var(--bg-secondary); border-radius: 4px; margin-bottom: 6px; border-left: 3px solid #667eea;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                            <strong style="font-size: 16px; color: var(--text-primary);">${code}</strong>
                            <button onclick="copyCode('${code}')" style="background: #10b981; color: white; border: none; padding: 4px 12px; border-radius: 4px; cursor: pointer; font-size: 12px; font-weight: 600;">Copy</button>
                        </div>
                        <details style="font-size: 12px; color: var(--text-secondary);">
                            <summary style="cursor: pointer;">Full message</summary>
                            <div style="margin-top: 4px;">${msg}</div>
                        </details>
                    </div>`;
                }).join('');
            }
        }
    } else {
        container.style.display = 'none';
    }
}

async function extendRental(rentalId) {
    const hours = prompt('How many hours to extend? (168 = 7 days)', '168');
    if (!hours) return;
    
    showLoading(true);
    
    try {
        const res = await fetch(`${API_BASE}/rentals/${rentalId}/extend`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ additional_hours: parseFloat(hours) })
        });
        
        const data = await res.json();
        showLoading(false);
        
        if (res.ok) {
            showNotification(`✅ Extended! Cost: $${data.cost}`, 'success');
            document.getElementById('user-credits').textContent = data.remaining_credits.toFixed(2);
            loadActiveRentals();
        } else {
            showNotification(`❌ ${data.detail}`, 'error');
        }
    } catch (err) {
        showLoading(false);
        showNotification('🌐 Network error', 'error');
    }
}

async function releaseRental(rentalId) {
    if (!confirm('Release this rental early? You\'ll get 50% refund for unused time.')) return;
    
    showLoading(true);
    
    try {
        const res = await fetch(`${API_BASE}/rentals/${rentalId}/release`, {
            method: 'POST',
            headers: {'Authorization': `Bearer ${token}`}
        });
        
        const data = await res.json();
        showLoading(false);
        
        if (res.ok) {
            showNotification(`✅ ${data.message}`, 'success');
            document.getElementById('user-credits').textContent = data.remaining_credits.toFixed(2);
            loadActiveRentals();
        } else {
            showNotification(`❌ ${data.detail}`, 'error');
        }
    } catch (err) {
        showLoading(false);
        showNotification('🌐 Network error', 'error');
    }
}

function selectMode(mode) {
    document.getElementById('mode-always').checked = (mode === 'always');
    document.getElementById('mode-manual').checked = (mode === 'manual');
    
    document.getElementById('mode-always-label').style.borderColor = (mode === 'always') ? '#667eea' : 'transparent';
    document.getElementById('mode-manual-label').style.borderColor = (mode === 'manual') ? '#667eea' : 'transparent';
    
    updateRentalPrice();
}

function selectDuration(days) {
    [7, 14, 30, 60, 90].forEach(d => {
        const radio = document.getElementById(`duration-${d}`);
        const label = document.getElementById(`duration-${d}-label`);
        if (d === days) {
            radio.checked = true;
            label.style.borderColor = '#667eea';
        } else {
            radio.checked = false;
            label.style.borderColor = 'transparent';
        }
    });
    
    updateRentalPrice();
}
