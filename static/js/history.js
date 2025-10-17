// History & Transactions Module
let historyRefreshInterval = null;

function startHistoryRefresh() {
    if (historyRefreshInterval) clearInterval(historyRefreshInterval);
    historyRefreshInterval = setInterval(() => {
        loadHistory(true);
    }, 30000);
}

function stopHistoryRefresh() {
    if (historyRefreshInterval) {
        clearInterval(historyRefreshInterval);
        historyRefreshInterval = null;
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

async function exportTransactions() {
    if (!token) return;
    window.open(`${API_BASE}/transactions/export`, '_blank');
}

async function exportVerifications() {
    if (!token) return;
    window.open(`${API_BASE}/verifications/export`, '_blank');
}
