// Rentals Module
let rentalMessagesCache = {};
let currentExtendModal = null;

const RENTAL_HOURLY = {
    1: 1.0, 2: 1.25, 3: 1.5, 6: 2.0, 12: 2.5, 24: 3.0
};

const RENTAL_SERVICE_SPECIFIC = {
    168: 10.0, 336: 18.0, 720: 32.5, 1440: 60.0, 2160: 85.0, 8760: 100.0
};

const RENTAL_GENERAL_USE = {
    168: 15.0, 336: 25.0, 720: 40.0, 1440: 70.0, 2160: 95.0, 8760: 150.0
};

const HOURLY_RENTAL_RULES = {
    minimum_duration: 1,
    maximum_duration: 24,
    auto_extend_discount: 0.10,
    manual_mode_discount: 0.30,
    bulk_discount_threshold: 5,
    bulk_discount_rate: 0.15,
    peak_hours_surcharge: 0.20,
    weekend_discount: 0.05
};

function showRentalModal() {
    document.getElementById('rental-modal').classList.remove('hidden');
    // Default to 1 hour rental
    selectHourlyDuration(1);
    updateRentalPrice();
}

function closeRentalModal() {
    document.getElementById('rental-modal').classList.add('hidden');
    
    // Clear pricing breakdown
    const breakdownElement = document.getElementById('pricing-breakdown');
    if (breakdownElement) {
        breakdownElement.remove();
    }
    
    // Reset form
    document.querySelectorAll('input[name="rental-duration"]').forEach(radio => {
        radio.checked = false;
    });
    document.querySelectorAll('[id*="duration-"][id*="-label"]').forEach(label => {
        label.style.borderColor = 'transparent';
    });
    
    const autoRenewCheckbox = document.getElementById('auto-renew-checkbox');
    if (autoRenewCheckbox) {
        autoRenewCheckbox.checked = false;
    }
}

// Add event listeners and initialization
document.addEventListener('DOMContentLoaded', function() {
    // Add change listeners for dynamic pricing
    document.addEventListener('change', function(e) {
        if (e.target.name === 'rental-mode' || e.target.name === 'rental-duration' || e.target.id === 'auto-renew-checkbox') {
            updateRentalPrice();
        }
    });
    
    // Add hourly rental support to existing modals
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList') {
                const rentalModal = document.getElementById('rental-modal');
                if (rentalModal && !rentalModal.classList.contains('hidden')) {
                    addHourlyRentalOptions();
                    addAutoRenewOption();
                }
            }
        });
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
});

// Add auto-renew checkbox to rental modal
function addAutoRenewOption() {
    const modalContent = document.querySelector('#rental-modal .modal-content');
    if (!modalContent || modalContent.querySelector('#auto-renew-checkbox')) return;
    
    const autoRenewHtml = `
        <div style="background: var(--bg-secondary); padding: 15px; border-radius: 8px; margin: 15px 0;">
            <label style="display: flex; align-items: center; gap: 10px; cursor: pointer;">
                <input type="checkbox" id="auto-renew-checkbox" style="width: 18px; height: 18px;">
                <div>
                    <div style="font-weight: 600; color: var(--text-primary);">🔄 Auto-Renewal (10% discount)</div>
                    <div style="font-size: 12px; color: var(--text-secondary); margin-top: 2px;">Automatically extend when rental expires</div>
                </div>
            </label>
        </div>
    `;
    
    const createButton = modalContent.querySelector('button[onclick*="createRentalNumber"]');
    if (createButton && createButton.parentNode) {
        createButton.parentNode.insertAdjacentHTML('beforebegin', autoRenewHtml);
    }
}

async function updateRentalPrice() {
    const service = document.getElementById('rental-service')?.value || 'telegram';
    const modeChecked = document.querySelector('input[name="rental-mode"]:checked');
    const durationChecked = document.querySelector('input[name="rental-duration"]:checked');
    
    if (!modeChecked || !durationChecked) return;
    
    const mode = modeChecked.value;
    const duration = parseFloat(durationChecked.value);
    const autoRenew = document.getElementById('auto-renew-checkbox')?.checked || false;
    
    try {
        // Get dynamic pricing from API
        const response = await fetch(`${API_BASE}/rentals/pricing?hours=${duration}&service_name=${service}&mode=${mode}&auto_renew=${autoRenew}&bulk_count=1`, {
            headers: {'Authorization': `Bearer ${window.token}`}
        });
        
        if (response.ok) {
            const pricing = await response.json();
            
            // Update total price
            const totalElement = document.getElementById('rental-total');
            if (totalElement) {
                totalElement.textContent = `N${pricing.final_price.toFixed(2)}`;
            }
            
            // Update individual hourly prices
            [1, 3, 6, 12, 24].forEach(hours => {
                const priceElement = document.getElementById(`price-${hours}h`);
                if (priceElement && duration === hours) {
                    priceElement.textContent = `N${pricing.final_price.toFixed(2)}`;
                }
            });
            
            // Show pricing breakdown if available
            showPricingBreakdown(pricing);
            
            // Update expiry date
            const expiryDate = new Date();
            if (duration < 24) {
                expiryDate.setHours(expiryDate.getHours() + duration);
                document.getElementById('rental-expiry').textContent = expiryDate.toLocaleString();
            } else {
                const days = duration / 24;
                expiryDate.setDate(expiryDate.getDate() + days);
                document.getElementById('rental-expiry').textContent = expiryDate.toLocaleDateString();
            }
        }
    } catch (error) {
        console.error('Pricing update failed:', error);
        // Fallback to static pricing
        const basePrice = duration <= 24 ? RENTAL_HOURLY[duration] || (duration * 0.5) : RENTAL_SERVICE_SPECIFIC[duration * 24] || 10;
        const modeMultiplier = mode === 'manual' ? 0.7 : 1.0;
        const totalPrice = basePrice * modeMultiplier;
        
        const totalElement = document.getElementById('rental-total');
        if (totalElement) {
            totalElement.textContent = `N${totalPrice.toFixed(2)}`;
        }
    }
}

function showPricingBreakdown(pricing) {
    // Remove existing breakdown
    const existingBreakdown = document.getElementById('pricing-breakdown');
    if (existingBreakdown) {
        existingBreakdown.remove();
    }
    
    // Create new breakdown
    if (pricing.adjustments && pricing.adjustments.length > 0) {
        const breakdownHtml = `
            <div id="pricing-breakdown" style="background: #f0fdf4; border: 2px solid #10b981; border-radius: 8px; padding: 15px; margin: 15px 0;">
                <h4 style="margin: 0 0 10px 0; color: #059669;">💰 Pricing Breakdown</h4>
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span>Base Price:</span>
                    <span>N${pricing.base_price.toFixed(2)}</span>
                </div>
                ${pricing.adjustments.map(adj => `
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px; font-size: 14px; color: #059669;">
                        <span>${adj.type} (${adj.rate}):</span>
                        <span>${adj.amount >= 0 ? '+' : ''}N${adj.amount.toFixed(2)}</span>
                    </div>
                `).join('')}
                <hr style="border: none; border-top: 1px solid #10b981; margin: 10px 0;">
                <div style="display: flex; justify-content: space-between; font-weight: bold; color: #059669;">
                    <span>Final Price:</span>
                    <span>N${pricing.final_price.toFixed(2)}</span>
                </div>
                ${pricing.savings > 0 ? `
                    <div style="text-align: center; margin-top: 8px; font-size: 14px; color: #059669;">
                        🎉 You save N${pricing.savings.toFixed(2)}!
                    </div>
                ` : ''}
            </div>
        `;
        
        const totalCostDiv = document.querySelector('#rental-modal .modal-content > div:nth-last-child(2)');
        if (totalCostDiv) {
            totalCostDiv.insertAdjacentHTML('afterend', breakdownHtml);
        }
    }
}

function selectHourlyDuration(hours) {
    // Clear all selections
    document.querySelectorAll('input[name="rental-duration"]').forEach(radio => {
        radio.checked = false;
    });
    document.querySelectorAll('[id*="duration-"][id*="-label"]').forEach(label => {
        label.style.borderColor = 'transparent';
    });
    
    // Select hourly duration
    const radio = document.getElementById(`duration-${hours}h`);
    const label = document.getElementById(`duration-${hours}h-label`);
    if (radio && label) {
        radio.checked = true;
        label.style.borderColor = '#fbbf24';
    }
    
    updateRentalPrice();
}

function selectExtendedDuration(days) {
    // Clear all selections
    document.querySelectorAll('input[name="rental-duration"]').forEach(radio => {
        radio.checked = false;
    });
    document.querySelectorAll('[id*="duration-"][id*="-label"]').forEach(label => {
        label.style.borderColor = 'transparent';
    });
    
    // Select extended duration
    const radio = document.getElementById(`duration-${days}`);
    const label = document.getElementById(`duration-${days}-label`);
    if (radio && label) {
        radio.checked = true;
        label.style.borderColor = '#667eea';
    }
    
    updateRentalPrice();
}

function selectDuration(days) {
    selectExtendedDuration(days);
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
    const duration = parseFloat(document.querySelector('input[name="rental-duration"]:checked').value);
    const autoExtend = document.getElementById('auto-renew-checkbox')?.checked || false;
    
    showLoading(true);
    
    try {
        const res = await fetch(`${API_BASE}/rentals/create`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${window.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                service_name: service,
                duration_hours: duration,
                mode: mode,
                auto_extend: autoExtend
            })
        });
        
        const data = await res.json();
        showLoading(false);
        
        if (res.ok) {
            const rentalType = duration <= 24 ? 'Hourly' : 'Extended';
            const durationText = duration < 24 ? `${duration}h` : `${duration/24}d`;
            showNotification(`✅ ${rentalType} rental created! ${data.phone_number} (${durationText})`, 'success');
            document.getElementById('user-credits').textContent = data.remaining_credits.toFixed(2);
            closeRentalModal();
            loadActiveRentals();
            loadTransactions(true);
        } else {
            showNotification(`❌ ${data.detail || data.error}`, 'error');
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
            headers: {'Authorization': `Bearer ${window.token}`}
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
                    headers: {'Authorization': `Bearer ${window.token}`}
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
    // Show extension modal with hourly options
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.style.display = 'block';
    modal.innerHTML = `
        <div class="modal-content" style="max-width: 500px;">
            <h2>🔄 Extend Rental</h2>
            <p style="color: #6b7280; margin-bottom: 20px;">Choose extension duration:</p>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(100px, 1fr)); gap: 10px; margin-bottom: 20px;">
                <button onclick="extendRentalHours('${rentalId}', 1)" style="padding: 15px; background: #10b981; color: white; border: none; border-radius: 8px; font-weight: 600;">+1h<br><small>~N1.20</small></button>
                <button onclick="extendRentalHours('${rentalId}', 3)" style="padding: 15px; background: #10b981; color: white; border: none; border-radius: 8px; font-weight: 600;">+3h<br><small>~N1.80</small></button>
                <button onclick="extendRentalHours('${rentalId}', 6)" style="padding: 15px; background: #10b981; color: white; border: none; border-radius: 8px; font-weight: 600;">+6h<br><small>~N2.40</small></button>
                <button onclick="extendRentalHours('${rentalId}', 12)" style="padding: 15px; background: #10b981; color: white; border: none; border-radius: 8px; font-weight: 600;">+12h<br><small>~N3.00</small></button>
                <button onclick="extendRentalHours('${rentalId}', 24)" style="padding: 15px; background: #10b981; color: white; border: none; border-radius: 8px; font-weight: 600;">+24h<br><small>~N3.60</small></button>
                <button onclick="extendRentalHours('${rentalId}', 168)" style="padding: 15px; background: #667eea; color: white; border: none; border-radius: 8px; font-weight: 600;">+7d<br><small>~N10.00</small></button>
            </div>
            
            <div style="display: flex; gap: 10px;">
                <input type="number" id="custom-extend-hours" placeholder="Custom hours" min="1" style="flex: 1; padding: 12px; border: 2px solid #e5e7eb; border-radius: 8px;">
                <button onclick="extendRentalCustom('${rentalId}')" style="background: #f59e0b; padding: 12px 20px;">Extend</button>
            </div>
            
            <button onclick="closeExtendModal()" style="width: 100%; margin-top: 15px; background: #6b7280;">Cancel</button>
        </div>
    `;
    document.body.appendChild(modal);
    currentExtendModal = modal;
}

async function extendRentalHours(rentalId, hours) {
    showLoading(true);
    closeExtendModal();
    
    try {
        const res = await fetch(`${API_BASE}/rentals/${rentalId}/extend`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${window.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ additional_hours: hours })
        });
        
        const data = await res.json();
        showLoading(false);
        
        if (res.ok) {
            const durationText = hours < 24 ? `${hours}h` : `${hours/24}d`;
            showNotification(`✅ Extended by ${durationText}! Cost: N${data.extension_cost.toFixed(2)}`, 'success');
            document.getElementById('user-credits').textContent = data.remaining_credits.toFixed(2);
            loadActiveRentals();
        } else {
            showNotification(`❌ ${data.detail || data.error}`, 'error');
        }
    } catch (err) {
        showLoading(false);
        showNotification('🌐 Network error', 'error');
    }
}

function extendRentalCustom(rentalId) {
    const hours = parseFloat(document.getElementById('custom-extend-hours').value);
    if (!hours || hours < 1) {
        showNotification('⚠️ Please enter valid hours (minimum 1)', 'error');
        return;
    }
    extendRentalHours(rentalId, hours);
}

function closeExtendModal() {
    if (currentExtendModal) {
        currentExtendModal.remove();
        currentExtendModal = null;
    }
}

async function releaseRental(rentalId) {
    if (!confirm('Release this rental early? You\'ll get 50% refund for unused time.')) return;
    
    showLoading(true);
    
    try {
        const res = await fetch(`${API_BASE}/rentals/${rentalId}/release`, {
            method: 'POST',
            headers: {'Authorization': `Bearer ${window.token}`}
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

function checkEmailAndShowRental() {
    // Check if user is logged in
    if (!window.token) {
        showNotification('🔒 Please login first', 'error');
        return;
    }
    
    // Get current user info to check email verification
    fetch(`${API_BASE}/auth/me`, {
        headers: {'Authorization': `Bearer ${window.token}`}
    })
    .then(res => res.json())
    .then(data => {
        if (data.email_verified) {
            showRentalModal();
        } else {
            showEmailVerificationPrompt();
        }
    })
    .catch(() => {
        showNotification('⚠️ Please verify your email for rentals', 'error');
    });
}

function showEmailVerificationPrompt() {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.style.display = 'block';
    modal.innerHTML = `
        <div class="modal-content" style="max-width: 500px;">
            <h2>📬 Email Verification Required</h2>
            <p style="color: #6b7280; margin-bottom: 20px;">Number rentals require email verification for security. Please check your email and click the verification link.</p>
            
            <div style="background: #fef3c7; border: 2px solid #f59e0b; border-radius: 8px; padding: 15px; margin-bottom: 20px;">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                    <span style="font-size: 20px;">ℹ️</span>
                    <strong style="color: #92400e;">Why Email Verification?</strong>
                </div>
                <ul style="color: #92400e; margin: 0; padding-left: 20px; font-size: 14px;">
                    <li>Secure your rented numbers</li>
                    <li>Receive important rental notifications</li>
                    <li>Enable account recovery</li>
                    <li>Prevent unauthorized access</li>
                </ul>
            </div>
            
            <div style="display: flex; gap: 10px;">
                <button onclick="resendVerificationEmail()" style="flex: 1; background: #10b981;">📬 Resend Email</button>
                <button onclick="closeEmailPrompt()" style="flex: 1; background: #6b7280;">Maybe Later</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

function closeEmailPrompt() {
    const modal = document.querySelector('.modal');
    if (modal) modal.remove();
}

async function resendVerificationEmail() {
    try {
        const res = await fetch(`${API_BASE}/auth/resend-verification`, {
            method: 'POST',
            headers: {'Authorization': `Bearer ${window.token}`}
        });
        
        if (res.ok) {
            showNotification('✅ Verification email sent! Check your inbox.', 'success');
            closeEmailPrompt();
        } else {
            showNotification('⚠️ Failed to send email. Try again later.', 'error');
        }
    } catch (err) {
        showNotification('🌐 Network error. Try again later.', 'error');
    }
}
