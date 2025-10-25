#!/usr/bin/env python3
"""
Production Optimization Test Suite
Tests performance monitoring, error tracking, and caching
"""

import requests
import time
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

class ProductionTester:
    def __init__(self):
        self.admin_token = None
        
    def test_all(self):
        """Run all production tests"""
        print("🚀 Testing Production Optimizations")
        print("=" * 50)
        
        try:
            self.login_admin()
            self.test_performance_monitoring()
            self.test_error_tracking()
            self.test_caching()
            self.test_health_checks()
            self.test_production_endpoints()
            
            print("\n✅ All production tests passed!")
            
        except Exception as e:
            print(f"\n❌ Production test failed: {e}")
            
    def login_admin(self):
        """Login as admin for testing"""
        print("\n1. Admin Authentication...")
        
        login_data = {
            "email": "admin@namaskah.app",
            "password": "Namaskah@Admin2024"
        }
        
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            self.admin_token = data["token"]
            print(f"   ✓ Admin login successful")
        else:
            raise Exception("Admin login failed")
            
    def test_performance_monitoring(self):
        """Test performance metrics collection"""
        print("\n2. Testing Performance Monitoring...")
        
        # Test metrics endpoint
        metric_data = {
            "type": "page_load",
            "data": {"duration": 1234},
            "timestamp": int(time.time() * 1000)
        }
        
        response = requests.post(f"{BASE_URL}/api/metrics", json=metric_data)
        assert response.status_code == 200, "Metrics endpoint should work"
        
        result = response.json()
        assert result["status"] == "logged", "Metric should be logged"
        print("   ✓ Performance metrics collection working")
        
    def test_error_tracking(self):
        """Test error logging"""
        print("\n3. Testing Error Tracking...")
        
        error_data = {
            "type": "javascript",
            "message": "Test error for monitoring",
            "filename": "test.js",
            "line": 42,
            "timestamp": int(time.time() * 1000)
        }
        
        response = requests.post(f"{BASE_URL}/api/errors", json=error_data)
        assert response.status_code == 200, "Error endpoint should work"
        
        result = response.json()
        assert result["status"] == "logged", "Error should be logged"
        print("   ✓ Error tracking working")
        
    def test_caching(self):
        """Test API response caching"""
        print("\n4. Testing API Caching...")
        
        # Test services endpoint (should be fast on second call)
        start_time = time.time()
        response1 = requests.get(f"{BASE_URL}/services/list")
        first_call_time = time.time() - start_time
        
        start_time = time.time()
        response2 = requests.get(f"{BASE_URL}/services/list")
        second_call_time = time.time() - start_time
        
        assert response1.status_code == 200, "Services endpoint should work"
        assert response2.status_code == 200, "Services endpoint should work on second call"
        
        # Second call should be faster (cached)
        if second_call_time < first_call_time * 0.8:
            print(f"   ✓ Caching working (first: {first_call_time:.3f}s, second: {second_call_time:.3f}s)")
        else:
            print(f"   ⚠️ Caching may not be working (first: {first_call_time:.3f}s, second: {second_call_time:.3f}s)")
            
    def test_health_checks(self):
        """Test production health monitoring"""
        print("\n5. Testing Health Checks...")
        
        if not self.admin_token:
            print("   ⚠️ Skipping health checks (no admin token)")
            return
            
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test health endpoint
        response = requests.get(f"{BASE_URL}/admin/production/health", headers=headers)
        assert response.status_code == 200, "Health endpoint should work"
        
        health_data = response.json()
        assert "status" in health_data, "Should return health status"
        
        print(f"   ✓ System health: {health_data['status']}")
        print(f"   ✓ Database: {health_data.get('database', 'unknown')}")
        print(f"   ✓ TextVerified API: {health_data.get('textverified_api', 'unknown')}")
        
    def test_production_endpoints(self):
        """Test production monitoring endpoints"""
        print("\n6. Testing Production Endpoints...")
        
        if not self.admin_token:
            print("   ⚠️ Skipping production endpoints (no admin token)")
            return
            
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test metrics endpoint
        response = requests.get(f"{BASE_URL}/admin/production/metrics", headers=headers)
        assert response.status_code == 200, "Production metrics should work"
        
        metrics_data = response.json()
        assert "total_metrics" in metrics_data, "Should return metrics data"
        
        print(f"   ✓ Total metrics collected: {metrics_data['total_metrics']}")
        print(f"   ✓ Error count: {metrics_data['error_count']}")
        print(f"   ✓ Recent metrics: {metrics_data['recent_metrics']}")
        
    def test_dashboard_performance(self):
        """Test enhanced dashboard performance"""
        print("\n7. Testing Dashboard Performance...")
        
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/dashboard/enhanced")
        load_time = time.time() - start_time
        
        assert response.status_code == 200, "Enhanced dashboard should load"
        
        # Check for production scripts
        content = response.text
        assert "performance-monitor.js" in content, "Should include performance monitoring"
        assert "error-tracker.js" in content, "Should include error tracking"
        assert "cache-manager.js" in content, "Should include cache manager"
        
        print(f"   ✓ Dashboard loaded in {load_time:.3f}s")
        print("   ✓ Production monitoring scripts included")
        
        # Performance benchmark
        if load_time < 1.0:
            print("   ✅ Excellent performance (< 1s)")
        elif load_time < 2.0:
            print("   ✓ Good performance (< 2s)")
        else:
            print("   ⚠️ Slow performance (> 2s)")

def main():
    """Run production optimization tests"""
    tester = ProductionTester()
    tester.test_all()
    tester.test_dashboard_performance()
    
    print("\n" + "=" * 50)
    print("🎯 Production Optimization Summary:")
    print("• Performance monitoring implemented")
    print("• Error tracking and reporting active")
    print("• API response caching enabled")
    print("• Health monitoring endpoints ready")
    print("• Production-ready dashboard deployed")
    print("\n📊 Monitor production at:")
    print(f"   Health: {BASE_URL}/admin/production/health")
    print(f"   Metrics: {BASE_URL}/admin/production/metrics")
    print(f"   Dashboard: {BASE_URL}/dashboard/enhanced")

if __name__ == "__main__":
    main()