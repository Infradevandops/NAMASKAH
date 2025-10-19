// Offline Queue for Verifications

const QUEUE_KEY = 'offline_verification_queue';

function getQueue() {
    return JSON.parse(localStorage.getItem(QUEUE_KEY) || '[]');
}

function saveQueue(queue) {
    localStorage.setItem(QUEUE_KEY, JSON.stringify(queue));
}

function addToQueue(action, data) {
    const queue = getQueue();
    queue.push({
        id: Date.now(),
        action,
        data,
        timestamp: new Date().toISOString()
    });
    saveQueue(queue);
    showNotification('📥 Queued for when online', 'success');
}

async function processQueue() {
    if (!navigator.onLine) return;
    
    const queue = getQueue();
    if (queue.length === 0) return;
    
    const processed = [];
    
    for (const item of queue) {
        try {
            if (item.action === 'create_verification') {
                await fetch(`${API_BASE}/verify/create`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${window.token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(item.data)
                });
                processed.push(item.id);
            }
        } catch (error) {
            console.error('Queue processing error:', error);
        }
    }
    
    const remaining = queue.filter(item => !processed.includes(item.id));
    saveQueue(remaining);
    
    if (processed.length > 0) {
        showNotification(`✅ Processed ${processed.length} queued items`, 'success');
        loadHistory();
    }
}

// Process queue when coming online
window.addEventListener('online', () => {
    setTimeout(processQueue, 1000);
});

// Show queue status
function showQueueStatus() {
    const queue = getQueue();
    if (queue.length > 0) {
        const banner = document.createElement('div');
        banner.style.cssText = 'position: fixed; top: 60px; left: 50%; transform: translateX(-50%); background: #f59e0b; color: white; padding: 10px 20px; border-radius: 8px; z-index: 9999; font-size: 14px;';
        banner.textContent = `📥 ${queue.length} items queued for sync`;
        document.body.appendChild(banner);
        setTimeout(() => banner.remove(), 3000);
    }
}

if (!navigator.onLine) showQueueStatus();
