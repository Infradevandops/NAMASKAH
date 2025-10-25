// Error Rate Monitoring System
class ErrorMonitor {
    constructor() {
        this.errors = [];
        this.errorThreshold = 5; // 5% error rate threshold
        this.timeWindow = 300000; // 5 minutes
        this.init();
    }

    init() {
        this.setupGlobalErrorHandling();
        this.setupAPIErrorTracking();
        this.startMonitoring();
    }

    setupGlobalErrorHandling() {
        // Track JavaScript errors
        window.addEventListener('error', (event) => {
            this.recordError({
                type: 'javascript',
                message: event.message,
                filename: event.filename,
                line: event.lineno,
                timestamp: Date.now()
            });
        });

        // Track unhandled promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            this.recordError({
                type: 'promise_rejection',
                message: event.reason?.message || 'Unhandled promise rejection',
                timestamp: Date.now()
            });
        });
    }

    setupAPIErrorTracking() {
        // Override fetch to track API errors
        const originalFetch = window.fetch;
        window.fetch = async (...args) => {
            try {
                const response = await originalFetch(...args);
                
                if (!response.ok) {
                    this.recordError({
                        type: 'api_error',
                        status: response.status,
                        url: args[0],
                        timestamp: Date.now()
                    });
                }
                
                return response;
            } catch (error) {
                this.recordError({
                    type: 'network_error',
                    message: error.message,
                    url: args[0],
                    timestamp: Date.now()
                });
                throw error;
            }
        };
    }

    recordError(error) {
        this.errors.push(error);
        
        // Clean old errors outside time window
        const cutoff = Date.now() - this.timeWindow;
        this.errors = this.errors.filter(e => e.timestamp > cutoff);
        
        // Check if error rate exceeds threshold
        this.checkErrorRate();
        
        console.error('Error recorded:', error);
    }

    checkErrorRate() {
        const totalRequests = this.getTotalRequests();
        const errorCount = this.errors.length;
        
        if (totalRequests > 0) {
            const errorRate = (errorCount / totalRequests) * 100;
            
            if (errorRate > this.errorThreshold) {
                this.triggerAlert(errorRate);
            }
        }
    }

    getTotalRequests() {
        // Get total requests from performance monitor if available
        if (window.performanceMonitor) {
            return window.performanceMonitor.metrics.totalRequests;
        }
        return this.errors.length * 2; // Rough estimate
    }

    triggerAlert(errorRate) {
        console.warn(`High error rate detected: ${errorRate.toFixed(1)}%`);
        
        // Show user notification
        if (typeof showNotification === 'function') {
            showNotification(
                `⚠️ High error rate detected (${errorRate.toFixed(1)}%). Some features may be unstable.`,
                'warning'
            );
        }
        
        // Send to backend for logging
        this.reportToBackend(errorRate);
    }

    async reportToBackend(errorRate) {
        try {
            await fetch('/performance/error-report', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    error_rate: errorRate,
                    error_count: this.errors.length,
                    recent_errors: this.errors.slice(-5), // Last 5 errors
                    timestamp: Date.now()
                })
            });
        } catch (error) {
            console.error('Failed to report error rate:', error);
        }
    }

    getErrorStats() {
        const cutoff = Date.now() - this.timeWindow;
        const recentErrors = this.errors.filter(e => e.timestamp > cutoff);
        
        const errorsByType = {};
        recentErrors.forEach(error => {
            errorsByType[error.type] = (errorsByType[error.type] || 0) + 1;
        });
        
        return {
            total_errors: recentErrors.length,
            error_rate: this.getTotalRequests() > 0 
                ? (recentErrors.length / this.getTotalRequests() * 100).toFixed(1)
                : 0,
            errors_by_type: errorsByType,
            time_window_minutes: this.timeWindow / 60000
        };
    }

    startMonitoring() {
        // Update error stats every 30 seconds
        setInterval(() => {
            const stats = this.getErrorStats();
            
            // Update UI if elements exist
            const errorRateElement = document.getElementById('error-rate');
            if (errorRateElement) {
                errorRateElement.textContent = `${stats.error_rate}%`;
            }
            
            // Update status indicator
            const errorStatus = document.getElementById('error-status');
            if (errorStatus) {
                const rate = parseFloat(stats.error_rate);
                if (rate < 1) {
                    errorStatus.className = 'status-indicator good';
                } else if (rate < 5) {
                    errorStatus.className = 'status-indicator warning';
                } else {
                    errorStatus.className = 'status-indicator error';
                }
            }
        }, 30000);
    }
}

// Initialize error monitoring
window.errorMonitor = new ErrorMonitor();

// Export for use in other modules
window.getErrorStats = () => window.errorMonitor.getErrorStats();