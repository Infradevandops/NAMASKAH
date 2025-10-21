// Carrier and Area Code Selection for Pro Users
class CarrierSelection {
    constructor() {
        this.carriers = [];
        this.areaCodes = [];
        this.isProUser = false;
        this.init();
    }

    async init() {
        await this.checkUserPlan();
        if (this.isProUser) {
            await this.loadCarriers();
            await this.loadAreaCodes();
            this.setupUI();
        }
    }

    async checkUserPlan() {
        try {
            const response = await fetch('/auth/me', {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
            });
            const user = await response.json();
            this.isProUser = ['pro', 'turbo', 'enterprise'].includes(user.subscription_plan);
        } catch (error) {
            console.error('Failed to check user plan:', error);
        }
    }

    async loadCarriers() {
        try {
            const response = await fetch('/carriers/list');
            const data = await response.json();
            this.carriers = data.carriers;
        } catch (error) {
            console.error('Failed to load carriers:', error);
        }
    }

    async loadAreaCodes() {
        try {
            const response = await fetch('/area-codes/list');
            const data = await response.json();
            this.areaCodes = data.area_codes;
        } catch (error) {
            console.error('Failed to load area codes:', error);
        }
    }

    setupUI() {
        // Add carrier selection to verification form
        const verificationForm = document.getElementById('verification-form');
        if (verificationForm) {
            this.addCarrierSelection(verificationForm);
            this.addAreaCodeSelection(verificationForm);
        }
    }

    addCarrierSelection(form) {
        const carrierSection = document.createElement('div');
        carrierSection.className = 'pro-feature-section';
        carrierSection.innerHTML = `
            <div class="pro-feature-header">
                <span class="pro-badge">PRO</span>
                <label>Preferred Carrier (Optional)</label>
                <span class="pricing-badge">+$25</span>
            </div>
            <select id="carrier-select" name="carrier" class="form-select">
                <option value="">Any Carrier</option>
                ${this.carriers.map(carrier => 
                    `<option value="${carrier.value}" ${carrier.popular ? 'data-popular="true"' : ''}>
                        ${carrier.label}
                    </option>`
                ).join('')}
            </select>
            <small class="help-text">Select a specific carrier (+$25 USD premium)</small>
        `;
        
        // Add pricing update listener
        const select = carrierSection.querySelector('#carrier-select');
        select.addEventListener('change', () => this.updatePricing());
        
        // Insert after service selection
        const serviceSelect = form.querySelector('#service-select');
        if (serviceSelect && serviceSelect.parentNode) {
            serviceSelect.parentNode.insertBefore(carrierSection, serviceSelect.nextSibling);
        }
    }

    addAreaCodeSelection(form) {
        const areaCodeSection = document.createElement('div');
        areaCodeSection.className = 'pro-feature-section';
        
        // Group area codes by popularity
        const popularCodes = this.areaCodes.filter(code => code.popular);
        const otherCodes = this.areaCodes.filter(code => !code.popular);
        
        areaCodeSection.innerHTML = `
            <div class="pro-feature-header">
                <span class="pro-badge">PRO</span>
                <label>Preferred Area Code (Optional)</label>
                <span class="pricing-badge">+$10</span>
            </div>
            <select id="area-code-select" name="area_code" class="form-select">
                <option value="">Any Area Code</option>
                <optgroup label="Popular Areas">
                    ${popularCodes.map(code => 
                        `<option value="${code.value}">${code.label}</option>`
                    ).join('')}
                </optgroup>
                <optgroup label="Other Areas">
                    ${otherCodes.map(code => 
                        `<option value="${code.value}">${code.label}</option>`
                    ).join('')}
                </optgroup>
            </select>
            <small class="help-text">Select a specific area code (+$10 USD premium)</small>
            <div id="area-code-preview" class="preview-text"></div>
        `;
        
        // Add pricing and preview listeners
        const select = areaCodeSection.querySelector('#area-code-select');
        select.addEventListener('change', () => {
            this.updatePricing();
            this.showAreaCodePreview(select.value);
        });
        
        // Insert after carrier selection
        const carrierSection = form.querySelector('.pro-feature-section');
        if (carrierSection) {
            carrierSection.parentNode.insertBefore(areaCodeSection, carrierSection.nextSibling);
        }
    }

    // Display carrier and location info in verification results
    displayVerificationInfo(verification) {
        const infoContainer = document.getElementById('verification-info');
        if (!infoContainer) return;

        const carrierInfo = verification.carrier_info;
        const locationInfo = verification.location_info;
        const userSelections = verification.user_selections;

        const infoHTML = `
            <div class="verification-details">
                <div class="phone-number">
                    <strong>Phone Number:</strong> ${this.formatPhoneNumber(verification.phone_number)}
                </div>
                
                <div class="location-info">
                    <strong>Location:</strong> ${locationInfo.display}
                </div>
                
                ${carrierInfo.requested_carrier ? `
                    <div class="carrier-info">
                        <strong>Carrier:</strong> ${carrierInfo.carrier_display}
                        <span class="requested-badge">Requested</span>
                    </div>
                ` : `
                    <div class="carrier-info">
                        <strong>Carrier:</strong> ${carrierInfo.carrier_display}
                    </div>
                `}
                
                ${userSelections.requested_area_code ? `
                    <div class="area-code-info">
                        <strong>Area Code:</strong> ${locationInfo.area_code}
                        <span class="requested-badge">Requested</span>
                    </div>
                ` : ''}
            </div>
        `;

        infoContainer.innerHTML = infoHTML;
    }

    updatePricing() {
        const carrierSelect = document.getElementById('carrier-select');
        const areaCodeSelect = document.getElementById('area-code-select');
        
        let additionalCost = 0;
        if (carrierSelect && carrierSelect.value) additionalCost += 25; // $25 for carrier
        if (areaCodeSelect && areaCodeSelect.value) additionalCost += 10; // $10 for area code
        
        // Update pricing display
        const pricingDisplay = document.getElementById('pricing-display');
        if (pricingDisplay && additionalCost > 0) {
            pricingDisplay.innerHTML = `Base cost + $${additionalCost} premium features`;
        }
    }
    
    showAreaCodePreview(areaCode) {
        const preview = document.getElementById('area-code-preview');
        if (preview && areaCode) {
            preview.innerHTML = `<small>Preview: (${areaCode}) XXX-XXXX</small>`;
            preview.style.display = 'block';
        } else if (preview) {
            preview.style.display = 'none';
        }
    }
    
    formatPhoneNumber(phoneNumber) {
        if (!phoneNumber) return 'Unknown';
        
        const clean = phoneNumber.replace(/\D/g, '');
        
        if (clean.length === 10) {
            return `+1 (${clean.slice(0, 3)}) ${clean.slice(3, 6)}-${clean.slice(6)}`;
        } else if (clean.length === 11 && clean.startsWith('1')) {
            return `+1 (${clean.slice(1, 4)}) ${clean.slice(4, 7)}-${clean.slice(7)}`;
        }
        
        return phoneNumber;
    }
}

// Initialize carrier selection when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new CarrierSelection();
});

// CSS for Pro features
const proFeatureStyles = `
    .pro-feature-section {
        margin: 15px 0;
        padding: 15px;
        border: 2px solid #e3f2fd;
        border-radius: 8px;
        background: linear-gradient(135deg, #f8f9ff 0%, #e3f2fd 100%);
    }

    .pro-feature-header {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 10px;
    }

    .pro-badge {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: bold;
        text-transform: uppercase;
    }

    .verification-details {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        margin: 15px 0;
    }

    .verification-details > div {
        margin: 8px 0;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .requested-badge {
        background: #28a745;
        color: white;
        padding: 2px 6px;
        border-radius: 10px;
        font-size: 10px;
        font-weight: bold;
    }

    .help-text {
        color: #6c757d;
        font-size: 12px;
        margin-top: 5px;
        display: block;
    }
    
    .pricing-badge {
        background: #28a745;
        color: white;
        padding: 2px 6px;
        border-radius: 10px;
        font-size: 10px;
        font-weight: bold;
        margin-left: auto;
    }
    
    .preview-text {
        background: #e9ecef;
        padding: 8px;
        border-radius: 4px;
        margin-top: 8px;
        font-family: monospace;
        display: none;
    }
`;

// Inject styles
const styleSheet = document.createElement('style');
styleSheet.textContent = proFeatureStyles;
document.head.appendChild(styleSheet);