#!/usr/bin/env python3
"""
Performance Baseline Test
Tests current application performance before optimizations
"""

import time
import requests
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
import statistics

BASE_URL = "http://localhost:8000"

def test_health_endpoint():
    """Test basic health endpoint"""
    start = time.time()
    response = requests.get(f"{BASE_URL}/health")
    end = time.time()
    
    return {
        "endpoint": "/health",
        "status_code": response.status_code,
        "response_time": round((end - start) * 1000, 2),
        "success": response.status_code == 200
    }

def test_services_list():
    """Test services list endpoint (should be cached)"""
    start = time.time()
    response = requests.get(f"{BASE_URL}/services/list")
    end = time.time()
    
    return {
        "endpoint": "/services/list",
        "status_code": response.status_code,
        "response_time": round((end - start) * 1000, 2),
        "success": response.status_code == 200
    }

def concurrent_requests(endpoint, count=10):
    """Test concurrent requests"""
    def make_request():
        start = time.time()
        response = requests.get(f"{BASE_URL}{endpoint}")
        end = time.time()
        return (end - start) * 1000
    
    with ThreadPoolExecutor(max_workers=count) as executor:
        futures = [executor.submit(make_request) for _ in range(count)]
        response_times = [future.result() for future in futures]
    
    return {
        "endpoint": endpoint,
        "concurrent_requests": count,
        "avg_response_time": round(statistics.mean(response_times), 2),
        "min_response_time": round(min(response_times), 2),
        "max_response_time": round(max(response_times), 2),
        "median_response_time": round(statistics.median(response_times), 2)
    }

def main():
    print("🧪 Performance Baseline Test")
    print("=" * 50)
    
    # Test basic endpoints
    health_result = test_health_endpoint()
    print(f"✅ Health Check: {health_result['response_time']}ms")
    
    services_result = test_services_list()
    print(f"✅ Services List: {services_result['response_time']}ms")
    
    # Test concurrent load
    print("\n🔄 Concurrent Load Test (10 requests)")
    concurrent_result = concurrent_requests("/health", 10)
    print(f"   Average: {concurrent_result['avg_response_time']}ms")
    print(f"   Median: {concurrent_result['median_response_time']}ms")
    print(f"   Min/Max: {concurrent_result['min_response_time']}/{concurrent_result['max_response_time']}ms")
    
    # Performance assessment
    avg_time = concurrent_result['avg_response_time']
    if avg_time < 100:
        grade = "🟢 EXCELLENT"
    elif avg_time < 200:
        grade = "🟡 GOOD"
    elif avg_time < 500:
        grade = "🟠 FAIR"
    else:
        grade = "🔴 NEEDS OPTIMIZATION"
    
    print(f"\n📊 Performance Grade: {grade}")
    print(f"📈 Baseline Average: {avg_time}ms")
    
    return {
        "baseline_performance": avg_time,
        "grade": grade,
        "health_check": health_result,
        "services_list": services_result,
        "concurrent_load": concurrent_result
    }

if __name__ == "__main__":
    try:
        results = main()
        print(f"\n✅ Baseline test complete")
    except requests.exceptions.ConnectionError:
        print("❌ Application not running. Start with: uvicorn main:app --reload")
    except Exception as e:
        print(f"❌ Test failed: {e}")