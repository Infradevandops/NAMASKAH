// Services Module
let servicesData = null;
let searchDebounceTimer = null;

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
    
    if (!search || 'general'.includes(search) || 'unlisted'.includes(search)) {
        html += `<div style="min-width: 100px;">`;
        html += `<div style="font-weight: bold; font-size: 0.75rem; color: #f59e0b; margin-bottom: 8px; border-bottom: 2px solid #f59e0b; padding-bottom: 4px;">Unlisted Services</div>`;
        html += `<div onclick="selectService('general')" style="font-size: 0.65rem; padding: 3px; cursor: pointer; border-radius: 4px; transition: all 0.2s; background: rgba(245, 158, 11, 0.1); font-weight: 600; color: #f59e0b;" onmouseover="this.style.background='#f59e0b'; this.style.color='white'" onmouseout="this.style.background='rgba(245, 158, 11, 0.1)'; this.style.color='#f59e0b'">Any Service</div>`;
        html += `</div>`;
    }
    
    container.innerHTML = html || 'No services found';
}

function selectService(service) {
    document.getElementById('service-select').value = service;
    document.getElementById('service-info').innerHTML = `✅ Selected: <strong>${formatServiceName(service)}</strong>`;
    document.getElementById('service-info').style.color = '#10b981';
    
    document.getElementById('capability-selection').classList.remove('hidden');
    document.getElementById('create-verification-btn').classList.remove('hidden');
    
    document.querySelectorAll('#categories-container > div > div[onclick]').forEach(el => {
        el.style.fontWeight = 'normal';
    });
    event.target.style.fontWeight = 'bold';
}

function filterServices() {
    if (searchDebounceTimer) clearTimeout(searchDebounceTimer);
    searchDebounceTimer = setTimeout(() => renderServices(), 200);
}

function updateCapability() {
    const capability = document.querySelector('input[name="capability"]:checked').value;
    const info = document.getElementById('service-info');
    const price = capability === 'voice' ? '₵0.75' : '₵0.50';
    info.innerHTML = `⚡ Click a service to select • ${capability === 'voice' ? '📞' : '📱'} ${capability.toUpperCase()} (${price})`;
}

function selectCapability(type) {
    document.querySelector('input[name="capability"][value="sms"]').checked = (type === 'sms');
    document.querySelector('input[name="capability"][value="voice"]').checked = (type === 'voice');
    
    document.getElementById('capability-sms-label').style.borderColor = (type === 'sms') ? '#fbbf24' : 'transparent';
    document.getElementById('capability-voice-label').style.borderColor = (type === 'voice') ? '#fbbf24' : 'transparent';
    
    updateCapability();
}
