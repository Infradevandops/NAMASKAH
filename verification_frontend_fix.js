// Enhanced createVerification function with better error handling and debugging
async function createVerification() {
    const service = document.getElementById('service-select').value;
    const capabilityEl = document.querySelector('input[name="capability"]:checked');
    const capability = capabilityEl ? capabilityEl.value : 'sms';
    
    console.log('🚀 Starting verification creation...', { service, capability });
    
    if (!service) {
        showNotification('⚠️ Please select a service', 'error');
        return;
    }
    
    if (!window.token) {
        showNotification('🔒 Please login first', 'error');
        return;
    }
    
    // Store current verification details
    currentServiceName = service;
    currentCapability = capability;
    verificationStartTime = Date.now();
    currentRetryCount = 0;
    
    // Get dynamic price before creating
    const price = await getServicePrice(service, capability);
    console.log(`💰 Service: ${service}, Capability: ${capability}, Price: N${price}`);
    
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
    
    console.log('📤 Request body:', requestBody);
    console.log('🔑 Token:', window.token ? `${window.token.substring(0, 20)}...` : 'None');
    
    try {
        const startTime = Date.now();
        
        const res = await fetch(`${API_BASE}/verify/create`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${window.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });
        
        const responseTime = Date.now() - startTime;
        console.log(`⏱️ Request completed in ${responseTime}ms`);
        console.log('📥 Response status:', res.status);
        console.log('📥 Response headers:', Object.fromEntries(res.headers.entries()));
        
        let data;
        try {
            data = await res.json();
            console.log('📥 Response data:', data);
        } catch (parseError) {
            console.error('❌ Failed to parse response JSON:', parseError);
            showLoading(false);
            showNotification('❌ Invalid response from server', 'error');
            return;
        }
        
        showLoading(false);
        
        if (res.ok) {
            console.log('✅ Verification created successfully!');
            currentVerificationId = data.id;
            displayVerification(data);
            
            // Update credits display
            const creditsElement = document.getElementById('user-credits');
            if (creditsElement && data.remaining_credits !== undefined) {
                creditsElement.textContent = data.remaining_credits.toFixed(2);
            }
            
            const capabilityText = capability === 'voice' ? '📞 Voice' : '📱 SMS';
            showNotification(`✅ ${capabilityText} verification created! Cost: N${data.cost} (${getTierName(service)})`, 'success');
            
            startAutoRefresh();
            startSmartCountdown(service, capability);
            
            // Reload history and transactions if functions exist
            if (typeof loadHistory === 'function') loadHistory();
            if (typeof loadTransactions === 'function') loadTransactions(true);
            
            if (!firstVerificationCompleted) {
                firstVerificationCompleted = true;
            }
        } else {
            console.error('❌ Verification creation failed:', res.status, data);
            
            // Enhanced error handling with specific messages
            if (res.status === 402) {
                showNotification(`💳 Insufficient funds. ${data.detail}`, 'error');
            } else if (res.status === 401) {
                showNotification('🔒 Session expired. Please login again', 'error');
                setTimeout(() => {
                    if (typeof logout === 'function') logout();
                }, 2000);
            } else if (res.status === 503) {
                // Service unavailable - likely TextVerified API issue
                console.error('🔧 Service unavailable error details:', data);
                
                if (data.detail && data.detail.includes('authentication failed')) {
                    showNotification('⚠️ SMS provider authentication failed. Please contact support.', 'error');
                } else if (data.detail && data.detail.includes('unavailable')) {
                    showNotification(`⚠️ ${service} verification temporarily unavailable. Try another service.`, 'error');
                } else {
                    showNotification(`⚠️ Service unavailable: ${service}. Try another service or contact support.`, 'error');
                }
            } else if (res.status === 400) {
                // Bad request - validation error
                showNotification(`❌ Invalid request: ${data.detail || 'Please check your input'}`, 'error');
            } else if (res.status === 500) {
                // Internal server error
                showNotification('❌ Server error. Please try again or contact support.', 'error');
            } else {
                // Generic error
                showNotification(`❌ ${data.detail || 'Failed to create verification'}`, 'error');
            }
        }
    } catch (err) {
        showLoading(false);
        console.error('❌ Network/Request error:', err);
        
        if (err.name === 'TypeError' && err.message.includes('fetch')) {
            showNotification('🌐 Network error. Check your internet connection.', 'error');
        } else if (err.name === 'AbortError') {
            showNotification('⏱️ Request timeout. Please try again.', 'error');
        } else {
            showNotification('🌐 Network error. Check your connection and try again.', 'error');
        }
    }
}

// Enhanced service selection with validation
async function selectService(service) {
    try {
        console.log('🎯 Selecting service:', service);
        
        const serviceSelect = document.getElementById('service-select');
        if (serviceSelect) {
            serviceSelect.value = service;
        }
        
        // Get dynamic price for selected service
        const capability = document.querySelector('input[name="capability"]:checked')?.value || 'sms';
        const price = await getServicePrice(service, capability);
        const priceText = `N${price}`;
        
        console.log('💰 Service price:', priceText);
        
        const serviceInfo = document.getElementById('service-info');
        if (serviceInfo) {
            serviceInfo.innerHTML = `✅ Selected: <strong>${formatServiceName(service)}</strong> • ${capability === 'voice' ? '📞' : '📱'} ${capability.toUpperCase()} (${priceText})`;
            serviceInfo.style.color = '#10b981';
        }
        
        // Show capability selection and create button
        const capabilitySection = document.getElementById('capability-selection');
        const createBtn = document.getElementById('create-verification-btn');
        
        if (capabilitySection) capabilitySection.classList.remove('hidden');
        if (createBtn) createBtn.classList.remove('hidden');
        
        // Update visual selection
        document.querySelectorAll('#categories-container > div > div[onclick]').forEach(el => {
            el.style.fontWeight = 'normal';
        });
        
        console.log(`✅ Selected service: ${service}`);
        
    } catch (error) {
        console.error('❌ Error selecting service:', error);
        if (typeof showNotification === 'function') {
            showNotification('⚠️ Error selecting service', 'error');
        }
    }
}

// Debug function to test verification creation
window.debugVerification = async function() {
    console.log('🐛 Debug verification creation...');
    console.log('Token:', window.token ? 'Present' : 'Missing');
    console.log('API_BASE:', API_BASE);
    
    if (!window.token) {
        console.log('❌ No authentication token');
        return;
    }
    
    // Test with a simple service
    const testData = {
        service_name: 'telegram',
        capability: 'sms'
    };
    
    try {
        const response = await fetch(`${API_BASE}/verify/create`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${window.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(testData)
        });
        
        console.log('Response status:', response.status);
        console.log('Response headers:', Object.fromEntries(response.headers.entries()));
        
        const data = await response.json();
        console.log('Response data:', data);
        
        if (response.ok) {
            console.log('✅ Debug verification successful!');
        } else {
            console.log('❌ Debug verification failed:', data.detail);
        }
        
    } catch (error) {
        console.error('❌ Debug verification error:', error);
    }
};

// Add this to the global scope for debugging
window.createVerification = createVerification;
window.selectService = selectService;

console.log('🔧 Enhanced verification module loaded with debugging');