// Performance Monitoring Dashboard
class PerformanceMonitor {
    constructor() {
        this.metrics = {
            responseTime: [],
            errorRate: 0,
            successRate: 100,
            activeUsers: 0,
            totalRequests: 0,
            failedRequests: 0
        };
        this.startTime = Date.now();
        this.init();
    }

    init() {
        this.trackPageLoad();
        this.trackAPIRequests();
        this.startRealTimeMonitoring();
    }

    trackPageLoad() {
        if (performance.timing) {
            const loadTime = performance.timing.loadEventEnd - performance.timing.navigationStart;
            this.addMetric('pageLoad', loadTime);
        }
    }

    trackAPIRequests() {
        const originalFetch = window.fetch;
        window.fetch = async (...args) => {
            const startTime = performance.now();
            try {
                const response = await originalFetch(...args);
                const endTime = performance.now();
                const responseTime = endTime - startTime;
                
                this.addMetric('apiResponse', responseTime);
                this.metrics.totalRequests++;
                
                if (!response.ok) {
                    this.metrics.failedRequests++;
                }
                
                this.updateMetrics();
                return response;
            } catch (error) {
                this.metrics.failedRequests++;
                this.updateMetrics();
                throw error;
            }
        };
    }

    addMetric(type, value) {
        if (type === 'apiResponse' || type === 'pageLoad') {
            this.metrics.responseTime.push({
                time: Date.now(),
                value: value
            });
            
            // Keep only last 50 measurements
            if (this.metrics.responseTime.length > 50) {
                this.metrics.responseTime.shift();
            }
        }
    }

    updateMetrics() {
        this.metrics.errorRate = this.metrics.totalRequests > 0 
            ? (this.metrics.failedRequests / this.metrics.totalRequests * 100).toFixed(1)
            : 0;
        this.metrics.successRate = (100 - this.metrics.errorRate).toFixed(1);
        
        this.updateDashboard();
    }

    updateDashboard() {
        const avgResponseTime = this.getAverageResponseTime();
        
        // Update performance cards
        this.updateCard('response-time', `${avgResponseTime}ms`);
        this.updateCard('error-rate', `${this.metrics.errorRate}%`);
        this.updateCard('success-rate', `${this.metrics.successRate}%`);
        this.updateCard('total-requests', this.metrics.totalRequests);
        
        // Update status indicators
        this.updateStatus('response-status', avgResponseTime < 500 ? 'good' : avgResponseTime < 1000 ? 'warning' : 'error');
        this.updateStatus('error-status', this.metrics.errorRate < 1 ? 'good' : this.metrics.errorRate < 5 ? 'warning' : 'error');
    }

    updateCard(id, value) {
        const element = document.getElementById(id);
        if (element) element.textContent = value;
    }

    updateStatus(id, status) {
        const element = document.getElementById(id);
        if (element) {
            element.className = `status-indicator ${status}`;
        }
    }

    getAverageResponseTime() {
        if (this.metrics.responseTime.length === 0) return 0;
        const sum = this.metrics.responseTime.reduce((acc, metric) => acc + metric.value, 0);
        return Math.round(sum / this.metrics.responseTime.length);
    }

    startRealTimeMonitoring() {
        setInterval(() => {
            this.checkSystemHealth();
            this.updateUptime();
        }, 5000);
    }

    async checkSystemHealth() {
        try {
            const startTime = performance.now();
            const response = await fetch('/health');
            const endTime = performance.now();
            
            if (response.ok) {
                this.addMetric('apiResponse', endTime - startTime);
                this.updateStatus('system-status', 'good');
            } else {
                this.updateStatus('system-status', 'error');
            }
        } catch (error) {
            this.updateStatus('system-status', 'error');
        }
    }

    updateUptime() {
        const uptime = Date.now() - this.startTime;
        const hours = Math.floor(uptime / (1000 * 60 * 60));
        const minutes = Math.floor((uptime % (1000 * 60 * 60)) / (1000 * 60));
        this.updateCard('uptime', `${hours}h ${minutes}m`);
    }

    getMetrics() {
        return {
            ...this.metrics,
            averageResponseTime: this.getAverageResponseTime(),
            uptime: Date.now() - this.startTime
        };
    }
}

// Initialize performance monitoring
window.performanceMonitor = new PerformanceMonitor();

// Export for use in other modules
window.getPerformanceMetrics = () => window.performanceMonitor.getMetrics();