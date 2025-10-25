/**
 * Smart Verification Component
 * Handles enhanced verification with auto-optimization and dynamic pricing
 */

class SmartVerificationManager {
    constructor() {
        this.currentService = null;
        this.autoOptimize = true;
        this.carrierPreference = null;
        this.areaCode = null;
        this.currentPricing = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadServices();
    }

    setupEventListeners() {
        // Service selection
        const serviceSelect = document.getElementById('service-select');
        if (serviceSelect) {
            serviceSelect.addEventListener('change', (e) => {
                this.handleServiceChange(e.target.value);
            });
        }

        // Auto-optimize toggle
        const autoOptimizeToggle = document.getElementById('auto-optimize');
        if (autoOptimizeToggle) {
            autoOptimizeToggle.addEventListener('change', (e) => {
                this.autoOptimize = e.target.checked;
                this.updatePricing();
            });
        }

        // Carrier selection
        const carrierSelect = document.getElementById('carrier-select');
        if (carrierSelect) {
            carrierSelect.addEventListener('change', (e) => {
                this.carrierPreference = e.target.value || null;
                this.updatePricing();
            });
        }

        // Area code input
        const areaCodeInput = document.getElementById('area-code');
        if (areaCodeInput) {
            areaCodeInput.addEventListener('input', (e) => {
                this.areaCode = e.target.value || null;
                this.updatePricing();
            });
        }

        // Create verification button
        const createBtn = document.getElementById('create-verification-btn');
        if (createBtn) {
            createBtn.addEventListener('click', () => {
                this.createVerification();
            });
        }
    }

    async loadServices() {
        try {
            const response = await fetch('/services/list');
            const data = await response.json();
            
            this.populateServiceDropdown(data);
            this.loadCarriers();
        } catch (error) {
            console.error('Failed to load services:', error);
        }
    }

    populateServiceDropdown(data) {
        const serviceSelect = document.getElementById('service-select');
        if (!serviceSelect) return;

        // Clear existing options
        serviceSelect.innerHTML = '<option value="">Select Service</option>';

        // Add popular services first
        if (data.categories && data.categories.popular) {
            const popularGroup = document.createElement('optgroup');
            popularGroup.label = 'Popular Services';
            
            data.categories.popular.forEach(service => {
                const option = document.createElement('option');
                option.value = service;
                option.textContent = this.formatServiceName(service);
                popularGroup.appendChild(option);
            });
            
            serviceSelect.appendChild(popularGroup);
        }

        // Add other categories
        Object.entries(data.categories || {}).forEach(([category, services]) => {
            if (category === 'popular') return;
            
            const group = document.createElement('optgroup');
            group.label = this.formatCategoryName(category);
            
            services.forEach(service => {
                const option = document.createElement('option');
                option.value = service;
                option.textContent = this.formatServiceName(service);
                group.appendChild(option);
            });
            
            serviceSelect.appendChild(group);
        });
    }

    async loadCarriers() {
        try {
            const response = await fetch('/carriers/list');
            const data = await response.json();
            
            const carrierSelect = document.getElementById('carrier-select');
            if (!carrierSelect) return;

            // Add popular carriers first
            data.carriers.filter(c => c.popular).forEach(carrier => {
                const option = document.createElement('option');
                option.value = carrier.value;
                option.textContent = `${carrier.label} (+$0.25)`;
                carrierSelect.appendChild(option);
            });

            // Add separator
            const separator = document.createElement('option');
            separator.disabled = true;
            separator.textContent = '──────────';
            carrierSelect.appendChild(separator);

            // Add other carriers
            data.carriers.filter(c => !c.popular).forEach(carrier => {
                const option = document.createElement('option');
                option.value = carrier.value;
                option.textContent = `${carrier.label} (+$0.25)`;
                carrierSelect.appendChild(option);
            });
        } catch (error) {
            console.error('Failed to load carriers:', error);
        }
    }

    async handleServiceChange(serviceName) {
        this.currentService = serviceName;
        
        if (!serviceName) {
            this.clearPricing();
            return;
        }

        await this.updatePricing();
        this.showOptimizationTips(serviceName);
    }

    async updatePricing() {
        if (!this.currentService) return;

        try {
            const params = new URLSearchParams({
                service_name: this.currentService,
                include_forecast: 'true'
            });

            const token = localStorage.getItem('token');
            const headers = {};
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }

            const response = await fetch(`/api/v2/pricing/analysis?${params}`, {
                headers
            });
            
            if (!response.ok) {
                // Fallback to basic pricing
                const fallbackResponse = await fetch(`/services/price/${this.currentService}`, {
                    headers
                });
                const fallbackData = await fallbackResponse.json();
                this.displayBasicPricing(fallbackData);
                return;
            }

            const pricing = await response.json();
            this.currentPricing = pricing;
            this.displayPricing(pricing);
            
        } catch (error) {
            console.error('Pricing update failed:', error);
            this.displayErrorPricing();
        }
    }

    displayPricing(pricing) {
        // Update current price
        const currentPriceEl = document.getElementById('current-price');
        if (currentPriceEl) {
            currentPriceEl.textContent = `N${pricing.current_price.toFixed(2)}`;
        }

        // Update base price if different
        const basePriceEl = document.getElementById('base-price');
        if (basePriceEl && pricing.base_price !== pricing.current_price) {
            basePriceEl.textContent = `N${pricing.base_price.toFixed(2)}`;
            basePriceEl.parentElement.style.display = 'block';
        }

        // Show savings
        const savingsEl = document.getElementById('savings');
        if (savingsEl && pricing.savings > 0) {
            savingsEl.textContent = `Save N${pricing.savings.toFixed(2)}`;
            savingsEl.classList.remove('hidden');
            savingsEl.classList.add('visible');
        } else if (savingsEl) {
            savingsEl.classList.add('hidden');
        }

        // Show timing optimization
        this.displayTimingOptimization(pricing.timing_optimization);

        // Update tier badge
        this.updateTierBadge(pricing.tier);
    }

    displayBasicPricing(pricing) {
        const currentPriceEl = document.getElementById('current-price');
        if (currentPriceEl) {
            currentPriceEl.textContent = `N${pricing.base_price.toFixed(2)}`;
        }

        // Hide advanced features
        const savingsEl = document.getElementById('savings');
        if (savingsEl) {
            savingsEl.classList.add('hidden');
        }
    }

    displayTimingOptimization(timing) {
        const timingTipEl = document.getElementById('timing-tip');
        if (!timingTipEl || !timing) return;

        if (timing.recommendation === 'wait' && timing.potential_savings > 0) {
            timingTipEl.innerHTML = `
                <i class="icon-clock"></i>
                💡 Wait ${timing.optimal_time} to save N${timing.potential_savings.toFixed(2)}
            `;
            timingTipEl.style.display = 'block';
        } else if (timing.recommendation === 'immediate') {
            timingTipEl.innerHTML = `
                <i class="icon-check"></i>
                ⚡ Best time to verify now
            `;
            timingTipEl.style.display = 'block';
        } else {
            timingTipEl.style.display = 'none';
        }
    }

    updateTierBadge(tier) {
        const tierBadgeEl = document.getElementById('tier-badge');
        if (!tierBadgeEl) return;

        tierBadgeEl.textContent = tier.toUpperCase();
        tierBadgeEl.className = `tier-badge tier-${tier}`;
    }

    showOptimizationTips(serviceName) {
        const tipsEl = document.getElementById('optimization-tips');
        if (!tipsEl) return;

        const tips = this.getServiceTips(serviceName);
        if (tips.length > 0) {
            tipsEl.innerHTML = `
                <h4>💡 Optimization Tips</h4>
                <ul>
                    ${tips.map(tip => `<li>${tip}</li>`).join('')}
                </ul>
            `;
            tipsEl.style.display = 'block';
        } else {
            tipsEl.style.display = 'none';
        }
    }

    getServiceTips(serviceName) {
        const tips = {
            'whatsapp': [
                'WhatsApp verifications work best with US numbers',
                'Avoid using the same number multiple times'
            ],
            'telegram': [
                'Telegram accepts most carriers',
                'Consider using area codes from major cities'
            ],
            'discord': [
                'Discord may require voice verification for some regions',
                'US and UK numbers have highest success rates'
            ]
        };

        return tips[serviceName.toLowerCase()] || [];
    }

    async createVerification() {
        if (!this.currentService) {
            this.showError('Please select a service first');
            return;
        }

        const createBtn = document.getElementById('create-verification-btn');
        if (createBtn) {
            createBtn.disabled = true;
            createBtn.textContent = 'Creating...';
        }

        try {
            const payload = {
                service_name: this.currentService,
                capability: 'sms'
            };

            // Add preferences if set
            if (this.carrierPreference) {
                payload.carrier = this.carrierPreference;
            }
            if (this.areaCode) {
                payload.area_code = this.areaCode;
            }

            const token = localStorage.getItem('token');
            const response = await fetch('/verify/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(payload)
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.detail || 'Verification creation failed');
            }

            this.handleVerificationCreated(result);

        } catch (error) {
            console.error('Verification creation failed:', error);
            this.showError(error.message);
        } finally {
            if (createBtn) {
                createBtn.disabled = false;
                createBtn.textContent = 'Create Verification';
            }
        }
    }

    handleVerificationCreated(verification) {
        // Show success message
        this.showSuccess(`Verification created! Phone: ${verification.phone_number}`);

        // Redirect to verification page or update UI
        if (window.location.pathname.includes('dashboard')) {
            // If on dashboard, refresh verification list
            if (window.loadActiveVerifications) {
                window.loadActiveVerifications();
            }
        } else {
            // Redirect to verification page
            window.location.href = `/verify/${verification.id}`;
        }

        // Reset form
        this.resetForm();
    }

    resetForm() {
        const serviceSelect = document.getElementById('service-select');
        if (serviceSelect) serviceSelect.value = '';

        const carrierSelect = document.getElementById('carrier-select');
        if (carrierSelect) carrierSelect.value = '';

        const areaCodeInput = document.getElementById('area-code');
        if (areaCodeInput) areaCodeInput.value = '';

        this.currentService = null;
        this.carrierPreference = null;
        this.areaCode = null;
        this.clearPricing();
    }

    clearPricing() {
        const currentPriceEl = document.getElementById('current-price');
        if (currentPriceEl) currentPriceEl.textContent = 'N0.00';

        const savingsEl = document.getElementById('savings');
        if (savingsEl) savingsEl.classList.add('hidden');

        const timingTipEl = document.getElementById('timing-tip');
        if (timingTipEl) timingTipEl.style.display = 'none';

        const tipsEl = document.getElementById('optimization-tips');
        if (tipsEl) tipsEl.style.display = 'none';
    }

    displayErrorPricing() {
        const currentPriceEl = document.getElementById('current-price');
        if (currentPriceEl) {
            currentPriceEl.textContent = 'N1.00';
            currentPriceEl.style.color = '#666';
        }
    }

    showError(message) {
        // Use existing notification system or create simple alert
        if (window.showNotification) {
            window.showNotification(message, 'error');
        } else {
            alert(message);
        }
    }

    showSuccess(message) {
        if (window.showNotification) {
            window.showNotification(message, 'success');
        } else {
            alert(message);
        }
    }

    formatServiceName(service) {
        return service.charAt(0).toUpperCase() + service.slice(1).replace(/[-_]/g, ' ');
    }

    formatCategoryName(category) {
        return category.charAt(0).toUpperCase() + category.slice(1).replace(/[-_]/g, ' ');
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('smart-verification-form')) {
        window.smartVerification = new SmartVerificationManager();
    }
});