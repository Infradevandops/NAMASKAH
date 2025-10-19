// Cookie Consent Management
(function() {
    const COOKIE_NAME = 'namaskah_cookie_consent';
    const COOKIE_EXPIRY_DAYS = 365;

    // Check if consent already given
    function hasConsent() {
        return localStorage.getItem(COOKIE_NAME) === 'accepted';
    }

    // Set consent
    function setConsent(value) {
        localStorage.setItem(COOKIE_NAME, value);
        if (value === 'accepted') {
            document.cookie = `${COOKIE_NAME}=accepted; max-age=${COOKIE_EXPIRY_DAYS * 24 * 60 * 60}; path=/; SameSite=Lax`;
        }
    }

    // Create banner
    function createBanner() {
        const banner = document.createElement('div');
        banner.id = 'cookie-consent-banner';
        banner.innerHTML = `
            <div class="cookie-content">
                <div class="cookie-text">
                    <p><strong>🍪 We use cookies</strong></p>
                    <p>We use essential cookies to make our site work. We'd also like to set optional analytics cookies to help us improve it. <a href="/cookies" style="color: #d4af37; text-decoration: underline;">Learn more</a></p>
                </div>
                <div class="cookie-buttons">
                    <button id="cookie-accept" class="cookie-btn cookie-accept">Accept All</button>
                    <button id="cookie-essential" class="cookie-btn cookie-essential">Essential Only</button>
                </div>
            </div>
        `;
        document.body.appendChild(banner);

        // Event listeners
        document.getElementById('cookie-accept').addEventListener('click', () => {
            setConsent('accepted');
            banner.remove();
        });

        document.getElementById('cookie-essential').addEventListener('click', () => {
            setConsent('essential');
            banner.remove();
        });
    }

    // Show banner if no consent
    if (!hasConsent() && !window.location.pathname.includes('/cookies')) {
        // Wait for DOM to load
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', createBanner);
        } else {
            createBanner();
        }
    }
})();
