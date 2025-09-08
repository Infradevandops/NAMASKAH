/**
 * Phone Number Marketplace JavaScript
 * Handles marketplace functionality, purchasing, and number management
 */

class PhoneMarketplace {
    constructor() {
        this.currentUser = null;
        this.availableNumbers = [];
        this.ownedNumbers = [];
        this.countries = [];
        this.currentView = 'grid';
        this.currentSort = 'country';
        this.selectedNumber = null;
        this.currentPage = 1;
        this.itemsPerPage = 20;
        
        this.init();
    }

    async init() {
        try {
            // Load user info
            await this.loadUserInfo();
            
            // Load supported countries
            await this.loadCountries();
            
            // Load subscription info
            await this.loadSubscriptionInfo();
            
            // Setup event listeners
            this.setupEventListeners();
            
            console.log('Phone marketplace initialized successfully');
        } catch (error) {
            console.error('Failed to initialize phone marketplace:', error);
            this.showError('Failed to initialize marketplace');
        }
    }

    async loadUserInfo() {
        try {
            // Get current user from JWT token or session
            const response = await fetch('/api/auth/me', {
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`
                }
            });
            
            if (response.ok) {
                this.currentUser = await response.json();
                document.getElementById('current-user').textContent = this.currentUser.username;
            } else {
                throw new Error('Failed to get user info');
            }
        } catch (error) {
            console.error('Error loading user info:', error);
            // Fallback to demo user
            this.currentUser = { id: 'demo_user', username: 'Demo User', subscription_plan: 'BASIC' };
            document.getElementById('current-user').textContent = this.currentUser.username;
        }
    }

    async loadCountries() {
        try {
            const response = await fetch('/api/numbers/countries', {
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.countries = data.countries;
                this.populateCountrySelect();
            } else {
                throw new Error('Failed to load countries');
            }
        } catch (error) {
            console.error('Error loading countries:', error);
            this.showError('Failed to load supported countries');
        }
    }

    populateCountrySelect() {
        const select = document.getElementById('country-select');
        select.innerHTML = '<option value="">Select Country</option>';
        
        this.countries.forEach(country => {
            const option = document.createElement('option');
            option.value = country.code;
            option.textContent = `${country.flag} ${country.name}`;
            select.appendChild(option);
        });
    }

    async loadSubscriptionInfo() {
        try {
            // Mock subscription info for demo
            const subscriptionInfo = {
                plan: this.currentUser.subscription_plan || 'BASIC',
                numbers_used: 0,
                numbers_limit: this.getNumberLimitForPlan(this.currentUser.subscription_plan || 'BASIC'),
                monthly_cost: 0,
                usage_percentage: 0
            };
            
            // Load actual owned numbers count
            const ownedResponse = await fetch('/api/numbers/owned', {
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`
                }
            });
            
            if (ownedResponse.ok) {
                const ownedData = await ownedResponse.json();
                subscriptionInfo.numbers_used = ownedData.active_count;
                subscriptionInfo.monthly_cost = parseFloat(ownedData.total_monthly_cost);
                subscriptionInfo.usage_percentage = (subscriptionInfo.numbers_used / subscriptionInfo.numbers_limit) * 100;
            }
            
            this.displaySubscriptionInfo(subscriptionInfo);
        } catch (error) {
            console.error('Error loading subscription info:', error);
        }
    }

    displaySubscriptionInfo(info) {
        const container = document.getElementById('subscription-info');
        
        container.innerHTML = `
            <div class="subscription-info">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <span class="fw-bold">Current Plan</span>
                    <span class="plan-badge ${info.plan.toLowerCase()}">${info.plan}</span>
                </div>
                
                <div class="mb-2">
                    <small class="text-muted">Numbers Used</small>
                    <div class="d-flex justify-content-between">
                        <span>${info.numbers_used} / ${info.numbers_limit}</span>
                        <span class="text-success">$${info.monthly_cost.toFixed(2)}/mo</span>
                    </div>
                    <div class="usage-bar">
                        <div class="usage-fill" style="width: ${Math.min(info.usage_percentage, 100)}%"></div>
                    </div>
                </div>
                
                ${info.usage_percentage > 80 ? `
                    <div class="alert alert-warning alert-sm p-2 mb-0">
                        <small><i class="fas fa-exclamation-triangle me-1"></i>
                        Approaching limit. Consider upgrading your plan.</small>
                    </div>
                ` : ''}
            </div>
        `;
    }

    setupEventListeners() {
        // Sort dropdown
        const sortSelect = document.createElement('select');
        sortSelect.className = 'form-select form-select-sm';
        sortSelect.innerHTML = `
            <option value="country">Sort by Country</option>
            <option value="area_code">Sort by Area Code</option>
            <option value="provider">Sort by Provider</option>
            <option value="price_low">Price: Low to High</option>
            <option value="price_high">Price: High to Low</option>
        `;
        sortSelect.onchange = (e) => this.sortNumbers(e.target.value);
        
        // Add sort dropdown to results header
        const resultsHeader = document.querySelector('.d-flex.justify-content-between.align-items-center.mb-3');
        if (resultsHeader) {
            const sortContainer = document.createElement('div');
            sortContainer.className = 'd-flex align-items-center gap-2';
            sortContainer.innerHTML = '<small class="text-muted">Sort:</small>';
            sortContainer.appendChild(sortSelect);
            
            const viewButtons = resultsHeader.querySelector('.btn-group');
            resultsHeader.insertBefore(sortContainer, viewButtons);
        }
    }

    async searchNumbers() {
        const country = document.getElementById('country-select').value;
        const areaCode = document.getElementById('area-code').value;
        const limit = document.getElementById('limit-select').value;
        
        if (!country) {
            this.showError('Please select a country first');
            return;
        }
        
        // Get selected capabilities
        const capabilities = [];
        if (document.getElementById('cap-sms').checked) capabilities.push('sms');
        if (document.getElementById('cap-voice').checked) capabilities.push('voice');
        if (document.getElementById('cap-mms').checked) capabilities.push('mms');
        
        this.showLoading(true);
        
        try {
            const params = new URLSearchParams({
                capabilities: capabilities.join(','),
                limit: limit
            });
            
            if (areaCode) params.append('area_code', areaCode);
            
            const response = await fetch(`/api/numbers/available/${country}?${params}`, {
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.availableNumbers = data.numbers;
                this.displaySearchResults();
                this.updateResultsCount(data.total_count, country);
            } else {
                throw new Error('Failed to search numbers');
            }
        } catch (error) {
            console.error('Error searching numbers:', error);
            this.showError('Failed to search for available numbers');
        } finally {
            this.showLoading(false);
        }
    }

    sortNumbers(sortBy) {
        this.currentSort = sortBy;
        
        this.availableNumbers.sort((a, b) => {
            switch (sortBy) {
                case 'country':
                    return a.country_code.localeCompare(b.country_code);
                case 'area_code':
                    return (a.area_code || '').localeCompare(b.area_code || '');
                case 'provider':
                    return a.provider.localeCompare(b.provider);
                case 'price_low':
                    return parseFloat(a.monthly_cost) - parseFloat(b.monthly_cost);
                case 'price_high':
                    return parseFloat(b.monthly_cost) - parseFloat(a.monthly_cost);
                default:
                    return 0;
            }
        });
        
        this.displaySearchResults();
    }

    displaySearchResults() {
        const container = document.getElementById('search-results');
        
        if (this.availableNumbers.length === 0) {
            container.innerHTML = `
                <div class="text-center py-5">
                    <i class="fas fa-search fa-3x text-muted mb-3"></i>
                    <h5>No Numbers Found</h5>
                    <p class="text-muted">Try adjusting your search criteria</p>
                </div>
            `;
            return;
        }
        
        const isGridView = this.currentView === 'grid';
        const containerClass = isGridView ? 'row' : '';
        const cardClass = isGridView ? 'col-md-6 col-lg-4 mb-3' : '';
        
        container.innerHTML = `
            <div class="${containerClass}">
                ${this.availableNumbers.map(number => this.createNumberCard(number, isGridView, cardClass)).join('')}
            </div>
        `;
    }

    createNumberCard(number, isGridView, cardClass) {
        const country = this.countries.find(c => c.code === number.country_code);
        const flag = country ? country.flag : '🏳️';
        
        return `
            <div class="${cardClass}">
                <div class="number-card ${isGridView ? 'grid-view' : 'list-view'}" onclick="phoneMarketplace.selectNumber('${number.phone_number}')">
                    ${isGridView ? this.createGridCard(number, flag) : this.createListCard(number, flag)}
                </div>
            </div>
        `;
    }

    createGridCard(number, flag) {
        return `
            <div class="number-header">
                <div class="number-display">${number.phone_number}</div>
                <span class="country-flag">${flag}</span>
            </div>
            
            <div class="number-details">
                <div class="detail-row">
                    <span class="detail-label">Country:</span>
                    <span class="detail-value">${number.country_code}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Area Code:</span>
                    <span class="detail-value">${number.area_code || 'N/A'}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Provider:</span>
                    <span class="detail-value">${this.capitalizeFirst(number.provider)}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Region:</span>
                    <span class="detail-value">${number.region}</span>
                </div>
                
                <div class="capabilities">
                    ${number.capabilities.map(cap => 
                        `<span class="capability-badge ${cap}">${cap.toUpperCase()}</span>`
                    ).join('')}
                </div>
            </div>
            
            <div class="pricing-section">
                <div class="monthly-cost">$${number.monthly_cost}/mo</div>
                <div class="usage-costs">
                    SMS: $${number.sms_cost_per_message}/msg
                    ${number.voice_cost_per_minute ? ` • Voice: $${number.voice_cost_per_minute}/min` : ''}
                </div>
            </div>
            
            <button class="purchase-button" onclick="event.stopPropagation(); phoneMarketplace.showPurchaseModal('${number.phone_number}')">
                <i class="fas fa-shopping-cart me-1"></i>Purchase Number
            </button>
        `;
    }

    createListCard(number, flag) {
        return `
            <div class="number-info">
                <div>
                    <div class="number-display">${number.phone_number} ${flag}</div>
                    <small class="text-muted">${number.region} • ${this.capitalizeFirst(number.provider)}</small>
                </div>
                
                <div class="capabilities">
                    ${number.capabilities.map(cap => 
                        `<span class="capability-badge ${cap}">${cap.toUpperCase()}</span>`
                    ).join('')}
                </div>
                
                <div class="pricing-section">
                    <div class="monthly-cost">$${number.monthly_cost}/mo</div>
                    <div class="usage-costs">SMS: $${number.sms_cost_per_message}/msg</div>
                </div>
            </div>
            
            <button class="purchase-button" onclick="event.stopPropagation(); phoneMarketplace.showPurchaseModal('${number.phone_number}')">
                <i class="fas fa-shopping-cart me-1"></i>Purchase
            </button>
        `;
    }

    selectNumber(phoneNumber) {
        this.selectedNumber = this.availableNumbers.find(n => n.phone_number === phoneNumber);
        // Could show detailed view or highlight selection
        console.log('Selected number:', this.selectedNumber);
    }

    showPurchaseModal(phoneNumber) {
        const number = this.availableNumbers.find(n => n.phone_number === phoneNumber);
        if (!number) return;
        
        const country = this.countries.find(c => c.code === number.country_code);
        const flag = country ? country.flag : '🏳️';
        
        document.getElementById('purchase-details').innerHTML = `
            <div class="text-center mb-3">
                <h4 class="text-primary">${number.phone_number} ${flag}</h4>
                <p class="text-muted">${number.region} • ${this.capitalizeFirst(number.provider)}</p>
            </div>
            
            <div class="row">
                <div class="col-md-6">
                    <h6>Capabilities</h6>
                    <div class="capabilities mb-3">
                        ${number.capabilities.map(cap => 
                            `<span class="capability-badge ${cap}">${cap.toUpperCase()}</span>`
                        ).join('')}
                    </div>
                </div>
                <div class="col-md-6">
                    <h6>Pricing</h6>
                    <div class="pricing-section">
                        <div class="monthly-cost">$${number.monthly_cost}/month</div>
                        <div class="usage-costs">
                            SMS: $${number.sms_cost_per_message} per message<br>
                            ${number.voice_cost_per_minute ? `Voice: $${number.voice_cost_per_minute} per minute<br>` : ''}
                            Setup Fee: $${number.setup_fee}
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Store selected number for purchase
        this.selectedNumber = number;
        
        const modal = new bootstrap.Modal(document.getElementById('purchaseModal'));
        modal.show();
    }

    async confirmPurchase() {
        if (!this.selectedNumber) return;
        
        const confirmBtn = document.getElementById('confirm-purchase-btn');
        const originalText = confirmBtn.innerHTML;
        confirmBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Processing...';
        confirmBtn.disabled = true;
        
        try {
            const autoRenew = document.getElementById('auto-renew').checked;
            
            const response = await fetch('/api/numbers/purchase', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getAuthToken()}`
                },
                body: JSON.stringify({
                    phone_number: this.selectedNumber.phone_number,
                    auto_renew: autoRenew
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                this.showSuccess(`Successfully purchased ${this.selectedNumber.phone_number}!`);
                
                // Close modal
                bootstrap.Modal.getInstance(document.getElementById('purchaseModal')).hide();
                
                // Refresh subscription info
                await this.loadSubscriptionInfo();
                
                // Remove purchased number from available list
                this.availableNumbers = this.availableNumbers.filter(
                    n => n.phone_number !== this.selectedNumber.phone_number
                );
                this.displaySearchResults();
                
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Purchase failed');
            }
        } catch (error) {
            console.error('Error purchasing number:', error);
            this.showError(`Purchase failed: ${error.message}`);
        } finally {
            confirmBtn.innerHTML = originalText;
            confirmBtn.disabled = false;
        }
    }

    async showMyNumbers() {
        try {
            const response = await fetch('/api/numbers/owned', {
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.ownedNumbers = data.numbers;
                this.displayOwnedNumbers();
                
                const modal = new bootstrap.Modal(document.getElementById('myNumbersModal'));
                modal.show();
            } else {
                throw new Error('Failed to load owned numbers');
            }
        } catch (error) {
            console.error('Error loading owned numbers:', error);
            this.showError('Failed to load your numbers');
        }
    }

    displayOwnedNumbers() {
        const container = document.getElementById('owned-numbers-list');
        
        if (this.ownedNumbers.length === 0) {
            container.innerHTML = `
                <div class="text-center py-4">
                    <i class="fas fa-phone fa-3x text-muted mb-3"></i>
                    <h5>No Numbers Owned</h5>
                    <p class="text-muted">Purchase your first number to get started</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = this.ownedNumbers.map(number => this.createOwnedNumberCard(number)).join('');
    }

    createOwnedNumberCard(number) {
        const expiryDate = new Date(number.expires_at);
        const now = new Date();
        const daysUntilExpiry = Math.ceil((expiryDate - now) / (1000 * 60 * 60 * 24));
        
        let expiryWarning = '';
        if (daysUntilExpiry <= 7 && daysUntilExpiry > 0) {
            expiryWarning = `<div class="expiry-warning">Expires in ${daysUntilExpiry} days</div>`;
        } else if (daysUntilExpiry <= 0) {
            expiryWarning = `<div class="expiry-warning expiry-critical">Expired ${Math.abs(daysUntilExpiry)} days ago</div>`;
        }
        
        return `
            <div class="owned-number-card">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <div>
                        <h6 class="mb-1">${number.phone_number}</h6>
                        <small class="text-muted">${number.country_code} • ${this.capitalizeFirst(number.provider)}</small>
                    </div>
                    <span class="number-status status-${number.status}">${number.status}</span>
                </div>
                
                <div class="usage-stats">
                    <div class="usage-stat">
                        <div class="usage-stat-value">${number.monthly_sms_sent}</div>
                        <div class="usage-stat-label">SMS Sent</div>
                    </div>
                    <div class="usage-stat">
                        <div class="usage-stat-value">${number.total_sms_received}</div>
                        <div class="usage-stat-label">SMS Received</div>
                    </div>
                    <div class="usage-stat">
                        <div class="usage-stat-value">$${number.monthly_cost}</div>
                        <div class="usage-stat-label">Monthly Cost</div>
                    </div>
                </div>
                
                ${expiryWarning}
                
                <div class="d-flex gap-2 mt-3">
                    <button class="btn btn-outline-primary btn-sm flex-fill" 
                            onclick="phoneMarketplace.showNumberDetails('${number.id}')">
                        <i class="fas fa-chart-bar me-1"></i>View Details
                    </button>
                    ${number.status === 'active' ? `
                        <button class="btn btn-outline-warning btn-sm" 
                                onclick="phoneMarketplace.renewNumber('${number.id}')">
                            <i class="fas fa-sync me-1"></i>Renew
                        </button>
                        <button class="btn btn-outline-danger btn-sm" 
                                onclick="phoneMarketplace.cancelNumber('${number.id}')">
                            <i class="fas fa-times me-1"></i>Cancel
                        </button>
                    ` : ''}
                </div>
            </div>
        `;
    }

    async showNumberDetails(numberId) {
        try {
            const response = await fetch(`/api/numbers/${numberId}/usage`, {
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.displayNumberDetails(data);
                
                const modal = new bootstrap.Modal(document.getElementById('numberDetailsModal'));
                modal.show();
            } else {
                throw new Error('Failed to load number details');
            }
        } catch (error) {
            console.error('Error loading number details:', error);
            this.showError('Failed to load number details');
        }
    }

    displayNumberDetails(data) {
        document.getElementById('number-details-content').innerHTML = `
            <div class="text-center mb-3">
                <h4 class="text-primary">${data.phone_number}</h4>
                <p class="text-muted">Usage Period: ${this.formatDate(data.period_start)} - ${this.formatDate(data.period_end)}</p>
            </div>
            
            <div class="usage-stats">
                <div class="usage-stat">
                    <div class="usage-stat-value">${data.usage.sms_sent}</div>
                    <div class="usage-stat-label">SMS Sent</div>
                </div>
                <div class="usage-stat">
                    <div class="usage-stat-value">${data.usage.sms_received}</div>
                    <div class="usage-stat-label">SMS Received</div>
                </div>
                <div class="usage-stat">
                    <div class="usage-stat-value">${data.usage.voice_minutes}</div>
                    <div class="usage-stat-label">Voice Minutes</div>
                </div>
            </div>
            
            <div class="cost-breakdown">
                <h6>Cost Breakdown</h6>
                <div class="cost-item">
                    <span>Monthly Fee:</span>
                    <span>$${data.costs.monthly_fee}</span>
                </div>
                <div class="cost-item">
                    <span>SMS Costs:</span>
                    <span>$${data.costs.sms_cost}</span>
                </div>
                <div class="cost-item">
                    <span>Voice Costs:</span>
                    <span>$${data.costs.voice_cost}</span>
                </div>
                <div class="cost-item cost-total">
                    <span>Total:</span>
                    <span>$${data.costs.total_cost}</span>
                </div>
            </div>
            
            <div class="subscription-details mt-3">
                <h6>Subscription Details</h6>
                <div class="detail-row">
                    <span class="detail-label">Status:</span>
                    <span class="detail-value">
                        <span class="number-status status-${data.subscription.status}">${data.subscription.status}</span>
                    </span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Expires:</span>
                    <span class="detail-value">${this.formatDate(data.subscription.expires_at)}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Auto Renew:</span>
                    <span class="detail-value">${data.subscription.auto_renew ? 'Yes' : 'No'}</span>
                </div>
            </div>
        `;
        
        // Show action buttons if number is active
        if (data.subscription.status === 'active') {
            document.getElementById('renew-btn').style.display = 'inline-block';
            document.getElementById('cancel-btn').style.display = 'inline-block';
        } else {
            document.getElementById('renew-btn').style.display = 'none';
            document.getElementById('cancel-btn').style.display = 'none';
        }
    }

    async renewNumber(numberId) {
        if (!confirm('Are you sure you want to renew this number for another month?')) return;
        
        try {
            const response = await fetch(`/api/numbers/${numberId}/renew`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getAuthToken()}`
                },
                body: JSON.stringify({
                    renewal_months: 1
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                this.showSuccess(`Number renewed successfully! New expiry: ${this.formatDate(data.new_expires_at)}`);
                
                // Refresh owned numbers
                await this.showMyNumbers();
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Renewal failed');
            }
        } catch (error) {
            console.error('Error renewing number:', error);
            this.showError(`Renewal failed: ${error.message}`);
        }
    }

    async cancelNumber(numberId) {
        if (!confirm('Are you sure you want to cancel this number? This action cannot be undone.')) return;
        
        try {
            const response = await fetch(`/api/numbers/${numberId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`
                }
            });
            
            if (response.ok) {
                this.showSuccess('Number cancelled successfully');
                
                // Refresh owned numbers
                await this.showMyNumbers();
                
                // Refresh subscription info
                await this.loadSubscriptionInfo();
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Cancellation failed');
            }
        } catch (error) {
            console.error('Error cancelling number:', error);
            this.showError(`Cancellation failed: ${error.message}`);
        }
    }

    setViewMode(mode) {
        this.currentView = mode;
        
        // Update button states
        document.getElementById('grid-view-btn').classList.toggle('active', mode === 'grid');
        document.getElementById('list-view-btn').classList.toggle('active', mode === 'list');
        
        // Re-render results
        this.displaySearchResults();
    }

    updateSearch() {
        // Auto-search when filters change
        const country = document.getElementById('country-select').value;
        if (country) {
            this.searchNumbers();
        }
    }

    updateResultsCount(count, country) {
        const countryName = this.countries.find(c => c.code === country)?.name || country;
        document.getElementById('results-count').textContent = 
            `Found ${count} available numbers in ${countryName}`;
    }

    showLoading(show) {
        document.getElementById('loading-state').style.display = show ? 'block' : 'none';
        document.getElementById('search-results').style.display = show ? 'none' : 'block';
    }

    showSuccess(message) {
        // Create and show success toast/notification
        this.showNotification(message, 'success');
    }

    showError(message) {
        // Create and show error toast/notification
        this.showNotification(message, 'error');
    }

    showNotification(message, type) {
        // Simple notification implementation
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'success' ? 'success' : 'danger'} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }

    // Utility methods
    getAuthToken() {
        return localStorage.getItem('auth_token') || 'demo_token';
    }

    getNumberLimitForPlan(plan) {
        const limits = {
            'FREE': 1,
            'BASIC': 3,
            'PREMIUM': 10,
            'ENTERPRISE': 50
        };
        return limits[plan] || 1;
    }

    capitalizeFirst(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }

    formatDate(dateString) {
        return new Date(dateString).toLocaleDateString();
    }
}

// Global functions for HTML event handlers
let phoneMarketplace;

document.addEventListener('DOMContentLoaded', function() {
    phoneMarketplace = new PhoneMarketplace();
});

function searchNumbers() {
    phoneMarketplace.searchNumbers();
}

function updateSearch() {
    phoneMarketplace.updateSearch();
}

function setViewMode(mode) {
    phoneMarketplace.setViewMode(mode);
}

function showMyNumbers() {
    phoneMarketplace.showMyNumbers();
}

function confirmPurchase() {
    phoneMarketplace.confirmPurchase();
}

function renewNumber() {
    // This will be called from the number details modal
    const numberId = phoneMarketplace.selectedNumberId;
    if (numberId) {
        phoneMarketplace.renewNumber(numberId);
    }
}

function cancelNumber() {
    // This will be called from the number details modal
    const numberId = phoneMarketplace.selectedNumberId;
    if (numberId) {
        phoneMarketplace.cancelNumber(numberId);
    }
}