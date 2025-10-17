// Developer Tools Module (API Keys, Webhooks, Analytics)

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

async function loadAnalytics() {
    if (!token) return;
    
    try {
        const res = await fetch(`${API_BASE}/analytics/dashboard`, {
            headers: {'Authorization': `Bearer ${token}`}
        });
        
        if (res.ok) {
            const data = await res.json();
            
            document.getElementById('stat-total').textContent = data.total_verifications;
            document.getElementById('stat-success').textContent = `${data.success_rate}%`;
            document.getElementById('stat-spent').textContent = `₵${data.total_spent.toFixed(2)}`;
            document.getElementById('stat-recent').textContent = data.recent_verifications;
            
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
