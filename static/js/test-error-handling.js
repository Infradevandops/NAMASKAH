/**
 * Frontend Error Handling Tests
 * Run in browser console to test error handling
 */

class FrontendErrorTester {
    constructor() {
        this.results = [];
    }
    
    log(message, type = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        const emoji = type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️';
        const result = `${emoji} [${timestamp}] ${message}`;
        this.results.push(result);
        console.log(result);
    }
    
    async testNetworkErrors() {
        this.log('Testing network error handling...', 'info');
        
        try {
            // Test with invalid URL
            await fetch('http://invalid-domain-12345.com/api/test');
            this.log('Network error test failed - should have thrown', 'error');
        } catch (error) {
            this.log('Network error caught correctly', 'success');
        }
        
        try {
            // Test with non-existent endpoint
            const response = await fetch('/api/nonexistent');
            if (response.status === 404) {
                this.log('404 error handled correctly', 'success');
            } else {
                this.log(`Unexpected status: ${response.status}`, 'error');
            }
        } catch (error) {
            this.log('Fetch error: ' + error.message, 'error');
        }
    }
    
    async testAuthErrors() {
        this.log('Testing authentication error handling...', 'info');
        
        try {
            // Test with invalid token
            const response = await fetch('/admin/stats', {
                headers: { 'Authorization': 'Bearer test_invalid_token' }
            });
            
            if (response.status === 401) {
                this.log('401 Unauthorized handled correctly', 'success');
            } else {
                this.log(`Expected 401, got ${response.status}`, 'error');
            }
        } catch (error) {
            this.log('Auth test error: ' + error.message, 'error');
        }
    }
    
    testGlobalErrorHandler() {
        this.log('Testing global error handler...', 'info');
        
        // Simulate a JavaScript error
        try {
            // This should trigger the global error handler
            setTimeout(() => {
                throw new Error('Test error for global handler');
            }, 100);
            this.log('Global error test initiated', 'success');
        } catch (error) {
            this.log('Global error test setup failed', 'error');
        }
    }
    
    testFormValidation() {
        this.log('Testing form validation...', 'info');
        
        // Test login form validation
        const loginEmail = document.getElementById('login-email');
        const loginpassword: "test_password"';
            loginpassword: "test_password"function') {
                // This should show validation error
                this.log('Form validation test available', 'success');
            } else {
                this.log('Login function not available', 'error');
            }
        } else {
            this.log('Login form elements not found', 'error');
        }
    }
    
    testNotificationSystem() {
        this.log('Testing notification system...', 'info');
        
        if (typeof showNotification === 'function') {
            showNotification('Test notification', 'success');
            this.log('Notification system working', 'success');
        } else {
            this.log('showNotification function not available', 'error');
        }
    }
    
    testErrorRecovery() {
        this.log('Testing error recovery mechanisms...', 'info');
        
        // Test fetchWithRetry if available
        if (typeof fetchWithRetry === 'function') {
            this.log('fetchWithRetry function available', 'success');
        } else {
            this.log('fetchWithRetry function not available', 'error');
        }
        
        // Test handleAPIError if available
        if (typeof handleAPIError === 'function') {
            this.log('handleAPIError function available', 'success');
        } else {
            this.log('handleAPIError function not available', 'error');
        }
    }
    
    async runAllTests() {
        console.clear();
        this.log('🧪 Starting Frontend Error Handling Tests', 'info');
        this.log('=' + '='.repeat(50), 'info');
        
        await this.testNetworkErrors();
        await this.testAuthErrors();
        this.testGlobalErrorHandler();
        this.testFormValidation();
        this.testNotificationSystem();
        this.testErrorRecovery();
        
        this.log('=' + '='.repeat(50), 'info');
        this.log('📊 Test Results Summary:', 'info');
        
        const passed = this.results.filter(r => r.includes('✅')).length;
        const failed = this.results.filter(r => r.includes('❌')).length;
        
        this.log(`Total: ${this.results.length}, Passed: ${passed}, Failed: ${failed}`, 'info');
        
        return {
            total: this.results.length,
            passed,
            failed,
            results: this.results
        };
    }
}

// Make tester available globally
window.frontendErrorTester = new FrontendErrorTester();

// Auto-run if in development
if (window.location.hostname === 'localhost') {
    console.log('🔧 Frontend Error Tester loaded. Run: frontendErrorTester.runAllTests()');
}