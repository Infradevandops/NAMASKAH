/**
 * Error Tracker - Production error handling and reporting
 */

class ErrorTracker {
    constructor() {
        this.errors = [];
        this.maxErrors = 50;
        this.init();
    }

    init() {
        this.setupGlobalErrorHandler();
        this.setupUnhandledRejectionHandler();
        this.setupAPIErrorInterceptor();
    }

    setupGlobalErrorHandler() {
        window.addEventListener('error', (event) => {
            this.logError({
                type: 'javascript',
                message: event.message,
                filename: event.filename,
                line: event.lineno,
                column: event.colno,
                stack: event.error?.stack,
                timestamp: Date.now(),
                url: window.location.href,
                userAgent: navigator.userAgent
            });
        });
    }

    setupUnhandledRejectionHandler() {
        window.addEventListener('unhandledrejection', (event) => {
            this.logError({
                type: 'promise_rejection',
                message: event.reason?.message || 'Unhandled Promise Rejection',
                stack: event.reason?.stack,
                timestamp: Date.now(),
                url: window.location.href
            });
        });
    }

    setupAPIErrorInterceptor() {
        // Intercept fetch errors
        const originalFetch = window.fetch;
        window.fetch = async (...args) => {
            try {
                const response = await originalFetch(...args);
                if (!response.ok) {
                    this.logError({
                        type: 'api_error',
                        message: `API Error: ${response.status} ${response.statusText}`,
                        endpoint: args[0],
                        status: response.status,
                        timestamp: Date.now()
                    });
                }
                return response;
            } catch (error) {
                this.logError({
                    type: 'network_error',
                    message: error.message,
                    endpoint: args[0],
                    timestamp: Date.now()
                });
                throw error;
            }
        };
    }

    logError(error) {
        // Add to local storage
        this.errors.push(error);
        if (this.errors.length > this.maxErrors) {
            this.errors.shift();
        }

        // Store in localStorage for persistence
        try {
            localStorage.setItem('error_log', JSON.stringify(this.errors.slice(-10)));
        } catch (e) {}

        // Send to server (production only)
        this.reportError(error);

        // Show user-friendly message for critical errors
        if (error.type === 'api_error' && error.status >= 500) {
            this.showUserError('Service temporarily unavailable. Please try again.');
        }
    }

    reportError(error) {
        // Only report in production
        if (window.location.hostname === 'localhost') return;

        fetch('/api/errors', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(error)
        }).catch(() => {}); // Silent fail
    }

    showUserError(message) {
        if (window.showNotification) {
            window.showNotification(message, 'error');
        }
    }

    getErrors() {
        return this.errors;
    }

    clearErrors() {
        this.errors = [];
        localStorage.removeItem('error_log');
    }
}

// Auto-initialize
window.errorTracker = new ErrorTracker();