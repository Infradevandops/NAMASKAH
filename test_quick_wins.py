#!/usr/bin/env python3
"""Test script for quick wins implementation"""
import requests
import time
import sys

API_BASE = "http://localhost:8000"

def test_health_endpoint():
    """Test 1: Health endpoint responds"""
    print("\n🧪 Test 1: Health Endpoint")
    try:
        res = requests.get(f"{API_BASE}/health", timeout=5)
        if res.status_code == 200:
            print("✅ Health endpoint working")
            return True
        else:
            print(f"❌ Health endpoint returned {res.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health endpoint failed: {e}")
        return False

def test_compression():
    """Test 2: Response compression enabled"""
    print("\n🧪 Test 2: Response Compression")
    try:
        res = requests.get(f"{API_BASE}/services/list", timeout=5)
        
        # Check if response is compressed
        content_encoding = res.headers.get('Content-Encoding', '')
        content_length = len(res.content)
        
        if content_encoding == 'gzip':
            print(f"✅ Compression enabled (gzip)")
            print(f"   Response size: {content_length} bytes")
            return True
        else:
            print(f"⚠️  Compression not detected")
            print(f"   Content-Encoding: {content_encoding or 'none'}")
            print(f"   Response size: {content_length} bytes")
            return False
    except Exception as e:
        print(f"❌ Compression test failed: {e}")
        return False

def test_status_page():
    """Test 3: Status page loads"""
    print("\n🧪 Test 3: Status Page")
    try:
        res = requests.get(f"{API_BASE}/status", timeout=5)
        if res.status_code == 200 and 'TextVerified API' in res.text:
            print("✅ Status page shows API health indicator")
            return True
        else:
            print(f"❌ Status page issue (status: {res.status_code})")
            return False
    except Exception as e:
        print(f"❌ Status page test failed: {e}")
        return False

def test_api_status():
    """Test 4: API status endpoint"""
    print("\n🧪 Test 4: API Status Endpoint")
    try:
        res = requests.get(f"{API_BASE}/services/status", timeout=5)
        if res.status_code == 200:
            data = res.json()
            api_status = data.get('status', {}).get('textverified_api', 'unknown')
            print(f"✅ API status endpoint working")
            print(f"   TextVerified API: {api_status}")
            return True
        else:
            print(f"❌ API status endpoint returned {res.status_code}")
            return False
    except Exception as e:
        print(f"❌ API status test failed: {e}")
        return False

def test_response_time():
    """Test 5: Response time improvement"""
    print("\n🧪 Test 5: Response Time")
    try:
        start = time.time()
        res = requests.get(f"{API_BASE}/services/list", timeout=5)
        duration = time.time() - start
        
        if res.status_code == 200:
            print(f"✅ Response time: {duration*1000:.0f}ms")
            if duration < 0.5:
                print("   🚀 Excellent performance!")
            elif duration < 1.0:
                print("   ✅ Good performance")
            else:
                print("   ⚠️  Slow response")
            return True
        else:
            print(f"❌ Request failed with status {res.status_code}")
            return False
    except Exception as e:
        print(f"❌ Response time test failed: {e}")
        return False

def main():
    print("=" * 60)
    print("🧪 Quick Wins Implementation Tests")
    print("=" * 60)
    
    # Check if server is running
    print("\n🔍 Checking if server is running...")
    try:
        requests.get(f"{API_BASE}/health", timeout=2)
        print("✅ Server is running")
    except:
        print("❌ Server is not running!")
        print("\n💡 Start the server first:")
        print("   python3 main.py")
        sys.exit(1)
    
    # Run tests
    results = []
    results.append(("Health Endpoint", test_health_endpoint()))
    results.append(("Response Compression", test_compression()))
    results.append(("Status Page", test_status_page()))
    results.append(("API Status", test_api_status()))
    results.append(("Response Time", test_response_time()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Quick wins implemented successfully!")
        print("\n📝 Next steps:")
        print("   1. Check app.log for request logs")
        print("   2. Monitor /services/status for API health")
        print("   3. Deploy to staging/production")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
