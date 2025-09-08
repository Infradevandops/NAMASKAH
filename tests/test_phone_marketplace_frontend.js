/**
 * Frontend tests for Phone Number Marketplace
 * Tests UI functionality, user interactions, and API integration
 */

describe('Phone Number Marketplace', () => {
    let marketplace;
    let mockFetch;

    beforeEach(() => {
        // Setup DOM
        document.body.innerHTML = `
            <div id="current-user"></div>
            <select id="country-select"></select>
            <input id="area-code" />
            <select id="limit-select"><option value="20" selected>20</option></select>
            <input type="checkbox" id="cap-sms" checked />
            <input type="checkbox" id="cap-voice" />
            <input type="checkbox" id="cap-mms" />
            <div id="subscription-info"></div>
            <div id="search-results"></div>
            <div id="loading-state"></div>
            <div id="results-count"></div>
            <div id="owned-numbers-list"></div>
            <div id="purchase-details"></div>
            <input type="checkbox" id="auto-renew" />
            <button id="confirm-purchase-btn"></button>
            <div id="number-details-content"></div>
            <button id="renew-btn"></button>
            <button id="cancel-btn"></button>
            <button id="grid-view-btn" class="active"></button>
            <button id="list-view-btn"></button>
        `;

        // Mock fetch
        mockFetch = jest.fn();
        global.fetch = mockFetch;

        // Mock localStorage
        Object.defineProperty(window, 'localStorage', {
            value: {
                getItem: jest.fn(() => 'mock_token'),
                setItem: jest.fn(),
                removeItem: jest.fn(),
            },
            writable: true,
        });

        // Mock bootstrap Modal
        global.bootstrap = {
            Modal: jest.fn().mockImplementation(() => ({
                show: jest.fn(),
                hide: jest.fn()
            }))
        };

        marketplace = new PhoneMarketplace();
    });

    afterEach(() => {
        jest.clearAllMocks();
    });

    describe('Initialization', () => {
        test('should initialize marketplace successfully', async () => {
            // Mock API responses
            mockFetch
                .mockResolvedValueOnce({
                    ok: true,
                    json: () => Promise.resolve({ id: 'user1', username: 'testuser', subscription_plan: 'BASIC' })
                })
                .mockResolvedValueOnce({
                    ok: true,
                    json: () => Promise.resolve({
                        success: true,
                        countries: [
                            { code: 'US', name: 'United States', flag: '🇺🇸' },
                            { code: 'GB', name: 'United Kingdom', flag: '🇬🇧' }
                        ]
                    })
                })
                .mockResolvedValueOnce({
                    ok: true,
                    json: () => Promise.resolve({ active_count: 1, total_monthly_cost: '1.50' })
                });

            await marketplace.init();

            expect(marketplace.currentUser).toBeDefined();
            expect(marketplace.countries).toHaveLength(2);
            expect(document.getElementById('current-user').textContent).toBe('testuser');
        });

        test('should handle initialization errors gracefully', async () => {
            mockFetch.mockRejectedValue(new Error('Network error'));

            await marketplace.init();

            // Should fallback to demo user
            expect(marketplace.currentUser.username).toBe('Demo User');
        });
    });

    describe('Country Selection', () => {
        test('should populate country select with available countries', () => {
            marketplace.countries = [
                { code: 'US', name: 'United States', flag: '🇺🇸' },
                { code: 'GB', name: 'United Kingdom', flag: '🇬🇧' }
            ];

            marketplace.populateCountrySelect();

            const select = document.getElementById('country-select');
            expect(select.children).toHaveLength(3); // Including default option
            expect(select.children[1].textContent).toBe('🇺🇸 United States');
            expect(select.children[2].textContent).toBe('🇬🇧 United Kingdom');
        });
    });

    describe('Number Search', () => {
        test('should search for available numbers successfully', async () => {
            const mockNumbers = [
                {
                    phone_number: '+15551234567',
                    country_code: 'US',
                    area_code: '555',
                    region: 'United States',
                    provider: 'mock',
                    monthly_cost: '1.50',
                    sms_cost_per_message: '0.01',
                    capabilities: ['sms', 'voice']
                }
            ];

            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve({
                    success: true,
                    numbers: mockNumbers,
                    total_count: 1
                })
            });

            // Set up search parameters
            document.getElementById('country-select').value = 'US';
            document.getElementById('area-code').value = '555';

            await marketplace.searchNumbers();

            expect(mockFetch).toHaveBeenCalledWith(
                expect.stringContaining('/api/numbers/available/US'),
                expect.objectContaining({
                    headers: expect.objectContaining({
                        'Authorization': 'Bearer mock_token'
                    })
                })
            );

            expect(marketplace.availableNumbers).toHaveLength(1);
            expect(marketplace.availableNumbers[0].phone_number).toBe('+15551234567');
        });

        test('should show error when no country selected', async () => {
            const showErrorSpy = jest.spyOn(marketplace, 'showError');
            
            document.getElementById('country-select').value = '';
            
            await marketplace.searchNumbers();
            
            expect(showErrorSpy).toHaveBeenCalledWith('Please select a country first');
        });

        test('should handle search API errors', async () => {
            mockFetch.mockResolvedValueOnce({
                ok: false,
                status: 500
            });

            const showErrorSpy = jest.spyOn(marketplace, 'showError');
            document.getElementById('country-select').value = 'US';

            await marketplace.searchNumbers();

            expect(showErrorSpy).toHaveBeenCalledWith('Failed to search for available numbers');
        });
    });

    describe('Number Sorting', () => {
        beforeEach(() => {
            marketplace.availableNumbers = [
                { phone_number: '+15551234567', country_code: 'US', area_code: '555', provider: 'twilio', monthly_cost: '2.00' },
                { phone_number: '+447001234567', country_code: 'GB', area_code: '700', provider: 'vonage', monthly_cost: '1.50' },
                { phone_number: '+15559876543', country_code: 'US', area_code: '559', provider: 'mock', monthly_cost: '1.00' }
            ];
        });

        test('should sort numbers by country code', () => {
            marketplace.sortNumbers('country');

            expect(marketplace.availableNumbers[0].country_code).toBe('GB');
            expect(marketplace.availableNumbers[1].country_code).toBe('US');
            expect(marketplace.availableNumbers[2].country_code).toBe('US');
        });

        test('should sort numbers by area code', () => {
            marketplace.sortNumbers('area_code');

            expect(marketplace.availableNumbers[0].area_code).toBe('555');
            expect(marketplace.availableNumbers[1].area_code).toBe('559');
            expect(marketplace.availableNumbers[2].area_code).toBe('700');
        });

        test('should sort numbers by provider', () => {
            marketplace.sortNumbers('provider');

            expect(marketplace.availableNumbers[0].provider).toBe('mock');
            expect(marketplace.availableNumbers[1].provider).toBe('twilio');
            expect(marketplace.availableNumbers[2].provider).toBe('vonage');
        });

        test('should sort numbers by price low to high', () => {
            marketplace.sortNumbers('price_low');

            expect(parseFloat(marketplace.availableNumbers[0].monthly_cost)).toBe(1.00);
            expect(parseFloat(marketplace.availableNumbers[1].monthly_cost)).toBe(1.50);
            expect(parseFloat(marketplace.availableNumbers[2].monthly_cost)).toBe(2.00);
        });

        test('should sort numbers by price high to low', () => {
            marketplace.sortNumbers('price_high');

            expect(parseFloat(marketplace.availableNumbers[0].monthly_cost)).toBe(2.00);
            expect(parseFloat(marketplace.availableNumbers[1].monthly_cost)).toBe(1.50);
            expect(parseFloat(marketplace.availableNumbers[2].monthly_cost)).toBe(1.00);
        });
    });

    describe('View Modes', () => {
        test('should switch to grid view', () => {
            marketplace.setViewMode('grid');

            expect(marketplace.currentView).toBe('grid');
            expect(document.getElementById('grid-view-btn').classList.contains('active')).toBe(true);
            expect(document.getElementById('list-view-btn').classList.contains('active')).toBe(false);
        });

        test('should switch to list view', () => {
            marketplace.setViewMode('list');

            expect(marketplace.currentView).toBe('list');
            expect(document.getElementById('list-view-btn').classList.contains('active')).toBe(true);
            expect(document.getElementById('grid-view-btn').classList.contains('active')).toBe(false);
        });
    });

    describe('Number Purchase', () => {
        const mockNumber = {
            phone_number: '+15551234567',
            country_code: 'US',
            area_code: '555',
            region: 'United States',
            provider: 'mock',
            monthly_cost: '1.50',
            sms_cost_per_message: '0.01',
            voice_cost_per_minute: '0.02',
            setup_fee: '0.00',
            capabilities: ['sms', 'voice']
        };

        test('should show purchase modal with number details', () => {
            marketplace.availableNumbers = [mockNumber];
            marketplace.countries = [{ code: 'US', name: 'United States', flag: '🇺🇸' }];

            marketplace.showPurchaseModal('+15551234567');

            expect(marketplace.selectedNumber).toEqual(mockNumber);
            expect(document.getElementById('purchase-details').innerHTML).toContain('+15551234567');
            expect(document.getElementById('purchase-details').innerHTML).toContain('$1.50/month');
        });

        test('should purchase number successfully', async () => {
            marketplace.selectedNumber = mockNumber;
            
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve({
                    success: true,
                    transaction_id: 'txn_123',
                    phone_number: mockNumber
                })
            });

            const showSuccessSpy = jest.spyOn(marketplace, 'showSuccess');
            const loadSubscriptionInfoSpy = jest.spyOn(marketplace, 'loadSubscriptionInfo').mockResolvedValue();

            await marketplace.confirmPurchase();

            expect(mockFetch).toHaveBeenCalledWith('/api/numbers/purchase', expect.objectContaining({
                method: 'POST',
                headers: expect.objectContaining({
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer mock_token'
                }),
                body: JSON.stringify({
                    phone_number: '+15551234567',
                    auto_renew: false // Default checkbox state
                })
            }));

            expect(showSuccessSpy).toHaveBeenCalledWith('Successfully purchased +15551234567!');
            expect(loadSubscriptionInfoSpy).toHaveBeenCalled();
        });

        test('should handle purchase errors', async () => {
            marketplace.selectedNumber = mockNumber;
            
            mockFetch.mockResolvedValueOnce({
                ok: false,
                json: () => Promise.resolve({ detail: 'Insufficient funds' })
            });

            const showErrorSpy = jest.spyOn(marketplace, 'showError');

            await marketplace.confirmPurchase();

            expect(showErrorSpy).toHaveBeenCalledWith('Purchase failed: Insufficient funds');
        });
    });

    describe('Owned Numbers Management', () => {
        const mockOwnedNumbers = [
            {
                id: 'num1',
                phone_number: '+15551234567',
                country_code: 'US',
                provider: 'mock',
                status: 'active',
                monthly_cost: '1.50',
                expires_at: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(), // 30 days from now
                monthly_sms_sent: 100,
                total_sms_received: 50
            }
        ];

        test('should load and display owned numbers', async () => {
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve({
                    success: true,
                    numbers: mockOwnedNumbers,
                    total_count: 1
                })
            });

            await marketplace.showMyNumbers();

            expect(marketplace.ownedNumbers).toHaveLength(1);
            expect(document.getElementById('owned-numbers-list').innerHTML).toContain('+15551234567');
            expect(document.getElementById('owned-numbers-list').innerHTML).toContain('status-active');
        });

        test('should show empty state when no numbers owned', async () => {
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve({
                    success: true,
                    numbers: [],
                    total_count: 0
                })
            });

            await marketplace.showMyNumbers();

            expect(document.getElementById('owned-numbers-list').innerHTML).toContain('No Numbers Owned');
        });

        test('should show expiry warnings for numbers expiring soon', () => {
            const expiringNumber = {
                ...mockOwnedNumbers[0],
                expires_at: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString() // 5 days from now
            };

            marketplace.ownedNumbers = [expiringNumber];
            marketplace.displayOwnedNumbers();

            expect(document.getElementById('owned-numbers-list').innerHTML).toContain('Expires in 5 days');
            expect(document.getElementById('owned-numbers-list').innerHTML).toContain('expiry-warning');
        });
    });

    describe('Number Renewal', () => {
        test('should renew number successfully', async () => {
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve({
                    success: true,
                    message: 'Number renewed successfully',
                    new_expires_at: new Date(Date.now() + 60 * 24 * 60 * 60 * 1000).toISOString()
                })
            });

            const showSuccessSpy = jest.spyOn(marketplace, 'showSuccess');
            const showMyNumbersSpy = jest.spyOn(marketplace, 'showMyNumbers').mockResolvedValue();

            // Mock confirm dialog
            window.confirm = jest.fn(() => true);

            await marketplace.renewNumber('num1');

            expect(mockFetch).toHaveBeenCalledWith('/api/numbers/num1/renew', expect.objectContaining({
                method: 'PUT',
                headers: expect.objectContaining({
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer mock_token'
                }),
                body: JSON.stringify({ renewal_months: 1 })
            }));

            expect(showSuccessSpy).toHaveBeenCalled();
            expect(showMyNumbersSpy).toHaveBeenCalled();
        });

        test('should not renew if user cancels confirmation', async () => {
            window.confirm = jest.fn(() => false);

            await marketplace.renewNumber('num1');

            expect(mockFetch).not.toHaveBeenCalled();
        });
    });

    describe('Number Cancellation', () => {
        test('should cancel number successfully', async () => {
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve({ success: true })
            });

            const showSuccessSpy = jest.spyOn(marketplace, 'showSuccess');
            const showMyNumbersSpy = jest.spyOn(marketplace, 'showMyNumbers').mockResolvedValue();
            const loadSubscriptionInfoSpy = jest.spyOn(marketplace, 'loadSubscriptionInfo').mockResolvedValue();

            window.confirm = jest.fn(() => true);

            await marketplace.cancelNumber('num1');

            expect(mockFetch).toHaveBeenCalledWith('/api/numbers/num1', expect.objectContaining({
                method: 'DELETE',
                headers: expect.objectContaining({
                    'Authorization': 'Bearer mock_token'
                })
            }));

            expect(showSuccessSpy).toHaveBeenCalledWith('Number cancelled successfully');
            expect(showMyNumbersSpy).toHaveBeenCalled();
            expect(loadSubscriptionInfoSpy).toHaveBeenCalled();
        });

        test('should not cancel if user cancels confirmation', async () => {
            window.confirm = jest.fn(() => false);

            await marketplace.cancelNumber('num1');

            expect(mockFetch).not.toHaveBeenCalled();
        });
    });

    describe('Usage Statistics', () => {
        test('should display number usage details', async () => {
            const mockUsageData = {
                phone_number_id: 'num1',
                phone_number: '+15551234567',
                period_start: '2024-01-01T00:00:00Z',
                period_end: '2024-01-31T23:59:59Z',
                usage: {
                    sms_sent: 100,
                    sms_received: 50,
                    voice_minutes: 30
                },
                costs: {
                    sms_cost: '1.00',
                    voice_cost: '0.60',
                    monthly_fee: '1.50',
                    total_cost: '3.10'
                },
                subscription: {
                    status: 'active',
                    expires_at: '2024-02-01T00:00:00Z',
                    auto_renew: true
                }
            };

            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve(mockUsageData)
            });

            await marketplace.showNumberDetails('num1');

            expect(document.getElementById('number-details-content').innerHTML).toContain('+15551234567');
            expect(document.getElementById('number-details-content').innerHTML).toContain('100'); // SMS sent
            expect(document.getElementById('number-details-content').innerHTML).toContain('$3.10'); // Total cost
        });
    });

    describe('Subscription Info', () => {
        test('should display subscription information correctly', () => {
            const subscriptionInfo = {
                plan: 'BASIC',
                numbers_used: 2,
                numbers_limit: 3,
                monthly_cost: 3.00,
                usage_percentage: 66.67
            };

            marketplace.displaySubscriptionInfo(subscriptionInfo);

            const container = document.getElementById('subscription-info');
            expect(container.innerHTML).toContain('BASIC');
            expect(container.innerHTML).toContain('2 / 3');
            expect(container.innerHTML).toContain('$3.00/mo');
            expect(container.innerHTML).toContain('width: 66.67%');
        });

        test('should show warning when approaching limit', () => {
            const subscriptionInfo = {
                plan: 'BASIC',
                numbers_used: 2,
                numbers_limit: 3,
                monthly_cost: 3.00,
                usage_percentage: 85
            };

            marketplace.displaySubscriptionInfo(subscriptionInfo);

            expect(document.getElementById('subscription-info').innerHTML).toContain('Approaching limit');
        });
    });

    describe('Utility Functions', () => {
        test('should get correct number limit for subscription plan', () => {
            expect(marketplace.getNumberLimitForPlan('FREE')).toBe(1);
            expect(marketplace.getNumberLimitForPlan('BASIC')).toBe(3);
            expect(marketplace.getNumberLimitForPlan('PREMIUM')).toBe(10);
            expect(marketplace.getNumberLimitForPlan('ENTERPRISE')).toBe(50);
            expect(marketplace.getNumberLimitForPlan('UNKNOWN')).toBe(1);
        });

        test('should capitalize first letter correctly', () => {
            expect(marketplace.capitalizeFirst('hello')).toBe('Hello');
            expect(marketplace.capitalizeFirst('WORLD')).toBe('WORLD');
            expect(marketplace.capitalizeFirst('')).toBe('');
        });

        test('should format dates correctly', () => {
            const date = '2024-01-15T12:00:00Z';
            const formatted = marketplace.formatDate(date);
            expect(formatted).toMatch(/\d{1,2}\/\d{1,2}\/\d{4}/); // MM/DD/YYYY or similar
        });
    });

    describe('Error Handling', () => {
        test('should show error notifications', () => {
            marketplace.showError('Test error message');

            const notification = document.querySelector('.alert-danger');
            expect(notification).toBeTruthy();
            expect(notification.textContent).toContain('Test error message');
        });

        test('should show success notifications', () => {
            marketplace.showSuccess('Test success message');

            const notification = document.querySelector('.alert-success');
            expect(notification).toBeTruthy();
            expect(notification.textContent).toContain('Test success message');
        });

        test('should handle network errors gracefully', async () => {
            mockFetch.mockRejectedValue(new Error('Network error'));
            
            const showErrorSpy = jest.spyOn(marketplace, 'showError');
            document.getElementById('country-select').value = 'US';

            await marketplace.searchNumbers();

            expect(showErrorSpy).toHaveBeenCalledWith('Failed to search for available numbers');
        });
    });
});

// Test configuration for Jest
module.exports = {
    testEnvironment: 'jsdom',
    setupFilesAfterEnv: ['<rootDir>/tests/setup.js'],
    collectCoverageFrom: [
        'static/js/phone-marketplace.js',
        '!**/node_modules/**',
        '!**/vendor/**'
    ],
    coverageThreshold: {
        global: {
            branches: 80,
            functions: 80,
            lines: 80,
            statements: 80
        }
    }
};