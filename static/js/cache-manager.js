/**
 * Cache Manager - Optimize API calls and improve performance
 */

class CacheManager {
    constructor() {
        this.cache = new Map();
        this.ttl = new Map();
        this.defaultTTL = 5 * 60 * 1000; // 5 minutes
        this.init();
    }

    init() {
        // Clear expired cache every minute
        setInterval(() => this.clearExpired(), 60000);
    }

    set(key, value, ttl = this.defaultTTL) {
        this.cache.set(key, value);
        this.ttl.set(key, Date.now() + ttl);
    }

    get(key) {
        if (!this.cache.has(key)) return null;
        
        if (Date.now() > this.ttl.get(key)) {
            this.delete(key);
            return null;
        }
        
        return this.cache.get(key);
    }

    delete(key) {
        this.cache.delete(key);
        this.ttl.delete(key);
    }

    clearExpired() {
        const now = Date.now();
        for (const [key, expiry] of this.ttl.entries()) {
            if (now > expiry) {
                this.delete(key);
            }
        }
    }

    // Cached API wrapper
    async cachedFetch(url, options = {}, ttl = this.defaultTTL) {
        const cacheKey = `${url}_${JSON.stringify(options)}`;
        
        // Return cached response if available
        const cached = this.get(cacheKey);
        if (cached) return cached;

        // Fetch and cache
        try {
            const response = await fetch(url, options);
            const data = await response.json();
            
            if (response.ok) {
                this.set(cacheKey, data, ttl);
            }
            
            return data;
        } catch (error) {
            throw error;
        }
    }

    // Cache service list for 10 minutes
    async getServices() {
        return this.cachedFetch('/services/list', {}, 10 * 60 * 1000);
    }

    // Cache pricing for 2 minutes
    async getPricing(service) {
        return this.cachedFetch(`/services/price/${service}`, {}, 2 * 60 * 1000);
    }

    // Cache carriers for 30 minutes
    async getCarriers() {
        return this.cachedFetch('/carriers/list', {}, 30 * 60 * 1000);
    }

    clear() {
        this.cache.clear();
        this.ttl.clear();
    }

    getStats() {
        return {
            size: this.cache.size,
            expired: Array.from(this.ttl.entries()).filter(([, expiry]) => Date.now() > expiry).length
        };
    }
}

// Global cache instance
window.cacheManager = new CacheManager();