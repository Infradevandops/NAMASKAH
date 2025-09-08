/**
 * Test setup for frontend JavaScript tests
 */

// Mock PhoneMarketplace class for testing
class PhoneMarketplace {
    constructor() {
        this.currentUser = null;
        this.availableNumbers = [];
        this.ownedNumbers = [];
        this.countries = [];
        this.currentView = 'grid';
        this.currentSort = 'country';
        this.selectedNumber = null;
        this.selectedNumberId = null;
    }

    async init() {
        await this.loadUserInfo();
        await this.loadCountries();
        await this.loadSubscriptionInfo();
    }

    async loadUserInfo() {
        try {
            const response = await fetch('/api/auth/me', {
                headers: { 'Authorization': `Bearer ${this.getAuthToken()}` }
            });
            if (response.ok) {
                this.currentUser = await response.json();
                document.getElementById('current-user').textContent = this.currentUser.username;
            } else {
                throw new Error('Failed to get user info');
            }
        } catch (error) {
            this.currentUser = { id: 'demo_user', username: 'Demo User', subscription_plan: 'BASIC' };
            document.getElementById('current-user').textContent = this.currentUser.username;
        }
    }

    async loadCountries() {
        try {
            const response = await fetch('/api/numbers/countries', {
                headers: { 'Authorization': `Bearer ${this.getAuthToken()}` }
            });
            if (response.ok) {
                const data = await response.json();
                this.countries = data.countries;
                this.populateCountrySelect();
            }
        } catch (error) {
            console.error('Error loading countries:', error);
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
            const subscriptionInfo = {
                plan: this.currentUser?.subscription_plan || 'BASIC',
                numbers_used: 0,
                numbers_limit: this.getNumberLimitForPlan(this.currentUser?.subscription_plan || 'BASIC'),
                monthly_cost: 0,
                usage_percentage: 0
            };

            const ownedResponse = await fetch('/api/numbers/owned', {
                headers: { 'Authorization': `Bearer ${this.getAuthToken()}` }
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

    async searchNumbers() {
        const country = document.getElementById('country-select').value;
        if (!country) {
            this.showError('Please select a country first');
            return;
        }

        const capabilities = [];
        if (document.getElementById('cap-sms').checked) capabilities.push('sms');
        if (document.getElementById('cap-voice').checked) capabilities.push('voice');
        if (document.getElementById('cap-mms').checked) capabilities.push('mms');

        const areaCode = document.getElementById('area-code').value;
        const limit = document.getElementById('limit-select').value;

        this.showLoading(true);

        try {
            const params = new URLSearchParams({
                capabilities: capabilities.join(','),
                limit: limit
            });
            if (areaCode) params.append('area_code', areaCode);

            const response = await fetch(`/api/numbers/available/${country}?${params}`, {
                headers: { 'Authorization': `Bearer ${this.getAuthToken()}` }
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
            this.showError('Failed to search for available numbers');
        } finally {
            this.showLoading(false);
        }
    }

    sortNumbers(sortBy) {
        this.currentSort = sortBy;
        this.availableNumbers.sort((a, b) => {
            switch (sortBy) {
                case 'country': return a.country_code.localeCompare(b.country_code);
                case 'area_code': return (a.area_code || '').localeCompare(b.area_code || '');
                case 'provider': return a.provider.localeCompare(b.provider);
                case 'price_low': return parseFloat(a.monthly_cost) - parseFloat(b.monthly_cost);
                case 'price_high': return parseFloat(b.monthly_cost) - parseFloat(a.monthly_cost);
                default: return 0;
            }
        });
        this.displaySearchResults();
    }

    displaySearchResults() {
        // Mock implementation for testing
        const container = document.getElementById('search-results');
        if (this.availableNumbers.length === 0) {
            container.innerHTML = '<div class="text-center">No numbers found</div>';
        } else {
            container.innerHTML = this.availableNumbers.map(n => `<div>${n.phone_number}</div>`).join('');
        }
    }

    setViewMode(mode) {
        this.currentView = mode;
        document.getElementById('grid-view-btn').classList.toggle('active', mode === 'grid');
        document.getElementById('list-view-btn').classList.toggle('active', mode === 'list');
        this.displaySearchResults();
    }

    showPurchaseModal(phoneNumber) {
        const number = this.availableNumbers.find(n => n.phone_number === phoneNumber);
        if (!number) return;
        
        this.selectedNumber = number;
        document.getElementById('purchase-details').innerHTML = `
            <h4>${number.phone_number}</h4>
            <p>$${number.monthly_cost}/month</p>
        `;
    }

    async confirmPurchase() {
        if (!this.selectedNumber) return;

        const confirmBtn = document.getElementById('confirm-purchase-btn');
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
                this.showSuccess(`Successfully purchased ${this.selectedNumber.phone_number}!`);
                await this.loadSubscriptionInfo();
                this.availableNumbers = this.availableNumbers.filter(
                    n => n.phone_number !== this.selectedNumber.phone_number
                );
                this.displaySearchResults();
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Purchase failed');
            }
        } catch (error) {
            this.showError(`Purchase failed: ${error.message}`);
        } finally {
            confirmBtn.disabled = false;
        }
    }

    async showMyNumbers() {
        try {
            const response = await fetch('/api/numbers/owned', {
                headers: { 'Authorization': `Bearer ${this.getAuthToken()}` }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.ownedNumbers = data.numbers;
                this.displayOwnedNumbers();
            }
        } catch (error) {
            this.showError('Failed to load your numbers');
        }
    }

    displayOwnedNumbers() {
        const container = document.getElementById('owned-numbers-list');
        if (this.ownedNumbers.length === 0) {
            container.innerHTML = '<div class="text-center">No Numbers Owned</div>';
        } else {
            container.innerHTML = this.ownedNumbers.map(number => `
                <div class="owned-number-card">
                    <h6>${number.phone_number}</h6>
                    <span class="number-status status-${number.status}">${number.status}</span>
                    ${number.expires_at ? this.getExpiryWarning(number.expires_at) : ''}
                </div>
            `).join('');
        }
    }

    getExpiryWarning(expiresAt) {
        const expiryDate = new Date(expiresAt);
        const now = new Date();
        const daysUntilExpiry = Math.ceil((expiryDate - now) / (1000 * 60 * 60 * 24));
        
        if (daysUntilExpiry <= 7 && daysUntilExpiry > 0) {
            return `<div class="expiry-warning">Expires in ${daysUntilExpiry} days</div>`;
        } else if (daysUntilExpiry <= 0) {
            return `<div class="expiry-warning expiry-critical">Expired ${Math.abs(daysUntilExpiry)} days ago</div>`;
        }
        return '';
    }

    async showNumberDetails(numberId) {
        try {
            const response = await fetch(`/api/numbers/${numberId}/usage`, {
                headers: { 'Authorization': `Bearer ${this.getAuthToken()}` }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.displayNumberDetails(data);
            }
        } catch (error) {
            this.showError('Failed to load number details');
        }
    }

    displayNumberDetails(data) {
        document.getElementById('number-details-content').innerHTML = `
            <h4>${data.phone_number}</h4>
            <div class="usage-stats">
                <div class="usage-stat">
                    <div class="usage-stat-value">${data.usage.sms_sent}</div>
                    <div class="usage-stat-label">SMS Sent</div>
                </div>
            </div>
            <div class="cost-breakdown">
                <div class="cost-item cost-total">
                    <span>Total:</span>
                    <span>$${data.costs.total_cost}</span>
                </div>
            </div>
        `;
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
                body: JSON.stringify({ renewal_months: 1 })
            });

            if (response.ok) {
                const data = await response.json();
                this.showSuccess(`Number renewed successfully! New expiry: ${this.formatDate(data.new_expires_at)}`);
                await this.showMyNumbers();
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Renewal failed');
            }
        } catch (error) {
            this.showError(`Renewal failed: ${error.message}`);
        }
    }

    async cancelNumber(numberId) {
        if (!confirm('Are you sure you want to cancel this number? This action cannot be undone.')) return;

        try {
            const response = await fetch(`/api/numbers/${numberId}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${this.getAuthToken()}` }
            });

            if (response.ok) {
                this.showSuccess('Number cancelled successfully');
                await this.showMyNumbers();
                await this.loadSubscriptionInfo();
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Cancellation failed');
            }
        } catch (error) {
            this.showError(`Cancellation failed: ${error.message}`);
        }
    }

    updateResultsCount(count, country) {
        document.getElementById('results-count').textContent = `Found ${count} available numbers in ${country}`;
    }

    showLoading(show) {
        document.getElementById('loading-state').style.display = show ? 'block' : 'none';
        document.getElementById('search-results').style.display = show ? 'none' : 'block';
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'success' ? 'success' : 'danger'}`;
        notification.textContent = message;
        document.body.appendChild(notification);
    }

    getAuthToken() {
        return 'mock_token';
    }

    getNumberLimitForPlan(plan) {
        const limits = { 'FREE': 1, 'BASIC': 3, 'PREMIUM': 10, 'ENTERPRISE': 50 };
        return limits[plan] || 1;
    }

    capitalizeFirst(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }

    formatDate(dateString) {
        return new Date(dateString).toLocaleDateString();
    }
}

// Make PhoneMarketplace available globally for tests
global.PhoneMarketplace = PhoneMarketplace;

// Mock console methods to avoid noise in tests
global.console = {
    ...console,
    log: jest.fn(),
    error: jest.fn(),
    warn: jest.fn(),
    info: jest.fn(),
};