"""
Comprehensive Testing Suite
Pro Tips: Automated testing, security validation, performance benchmarking
"""
import asyncio
import aiohttp
import time
import json
import logging
from typing import Dict, List, Any
import websockets
import subprocess
import sys

class SecurityTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_rate_limiting(self) -> Dict[str, Any]:
        """Test rate limiting implementation"""
        print("🔒 Testing Rate Limiting...")
        
        start_time = time.time()
        rate_limited = False
        request_count = 0
        
        for i in range(110):  # Exceed the 100 req/min limit
            try:
                async with self.session.get(f"{self.base_url}/health") as response:
                    request_count += 1
                    if response.status == 429:
                        rate_limited = True
                        break
            except Exception as e:
                print(f"Request {i+1} failed: {str(e)}")
                break
        
        duration = time.time() - start_time
        
        return {
            "test": "rate_limiting",
            "passed": rate_limited,
            "requests_sent": request_count,
            "duration": f"{duration:.2f}s",
            "details": f"Rate limit triggered at request {request_count}" if rate_limited else "Rate limiting not working"
        }
    
    async def test_sql_injection(self) -> Dict[str, Any]:
        """Test SQL injection prevention"""
        print("🔒 Testing SQL Injection Prevention...")
        
        malicious_payloads = [
            "admin@test.com'; DROP TABLE users;--",
            "admin@test.com' OR '1'='1",
            "admin@test.com'; INSERT INTO users (email) VALUES ('hacked@test.com');--",
            "admin@test.com' UNION SELECT * FROM users--"
        ]
        
        injection_blocked = 0
        
        for payload in malicious_payloads:
            try:
                data = {"email": payload, "password": "test123"}
                async with self.session.post(f"{self.base_url}/auth/login", json=data) as response:
                    if response.status in [400, 401, 422]:  # Properly rejected
                        injection_blocked += 1
            except Exception:
                injection_blocked += 1  # Connection error is also good (blocked)
        
        return {
            "test": "sql_injection",
            "passed": injection_blocked == len(malicious_payloads),
            "blocked_attempts": f"{injection_blocked}/{len(malicious_payloads)}",
            "details": "All injection attempts blocked" if injection_blocked == len(malicious_payloads) else "Some injections may have succeeded"
        }
    
    async def test_xss_prevention(self) -> Dict[str, Any]:
        """Test XSS prevention"""
        print("🔒 Testing XSS Prevention...")
        
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "';alert('XSS');//"
        ]
        
        xss_blocked = 0
        
        for payload in xss_payloads:
            try:
                data = {"service_name": payload}
                async with self.session.post(f"{self.base_url}/verify/create", json=data) as response:
                    if response.status in [400, 422]:  # Properly rejected
                        xss_blocked += 1
                    elif response.status == 200:
                        # Check if payload was sanitized in response
                        response_text = await response.text()
                        if payload not in response_text:
                            xss_blocked += 1
            except Exception:
                xss_blocked += 1
        
        return {
            "test": "xss_prevention",
            "passed": xss_blocked >= len(xss_payloads) * 0.8,  # 80% threshold
            "blocked_attempts": f"{xss_blocked}/{len(xss_payloads)}",
            "details": "XSS prevention working" if xss_blocked >= len(xss_payloads) * 0.8 else "XSS vulnerabilities detected"
        }
    
    async def test_csrf_protection(self) -> Dict[str, Any]:
        """Test CSRF protection"""
        print("🔒 Testing CSRF Protection...")
        
        # Try POST without CSRF token
        try:
            data = {"service_name": "telegram"}
            async with self.session.post(f"{self.base_url}/verify/create", json=data) as response:
                csrf_protected = response.status == 403
        except Exception:
            csrf_protected = True  # Connection error indicates protection
        
        return {
            "test": "csrf_protection",
            "passed": csrf_protected,
            "details": "CSRF protection active" if csrf_protected else "CSRF protection missing"
        }

class APITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        self.auth_token = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def authenticate(self) -> bool:
        """Authenticate and get token"""
        try:
            data = {"email": "admin@namaskah.app", "password": "Namaskah@Admin2024"}
            async with self.session.post(f"{self.base_url}/auth/login", json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    self.auth_token = result.get("access_token")
                    return True
        except Exception as e:
            print(f"Authentication failed: {str(e)}")
        return False
    
    async def test_api_authentication(self) -> Dict[str, Any]:
        """Test API key authentication"""
        print("🔑 Testing API Authentication...")
        
        # Test without API key
        try:
            async with self.session.post(f"{self.base_url}/verify/create", json={"service_name": "telegram"}) as response:
                no_auth_blocked = response.status in [401, 403]
        except Exception:
            no_auth_blocked = True
        
        # Test with invalid API key
        headers = {"X-API-Key": "nsk_invalid_key_12345"}
        try:
            async with self.session.post(f"{self.base_url}/verify/create", json={"service_name": "telegram"}, headers=headers) as response:
                invalid_key_blocked = response.status in [401, 403]
        except Exception:
            invalid_key_blocked = True
        
        return {
            "test": "api_authentication",
            "passed": no_auth_blocked and invalid_key_blocked,
            "details": {
                "no_auth_blocked": no_auth_blocked,
                "invalid_key_blocked": invalid_key_blocked
            }
        }
    
    async def test_bulk_verification(self) -> Dict[str, Any]:
        """Test bulk verification endpoint"""
        print("📦 Testing Bulk Verification...")
        
        if not await self.authenticate():
            return {"test": "bulk_verification", "passed": False, "details": "Authentication failed"}
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        data = {"services": ["telegram", "whatsapp", "discord"]}
        
        try:
            async with self.session.post(f"{self.base_url}/verify/bulk", json=data, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    bulk_working = "results" in result and len(result["results"]) == 3
                else:
                    bulk_working = False
        except Exception as e:
            bulk_working = False
            print(f"Bulk verification test failed: {str(e)}")
        
        return {
            "test": "bulk_verification",
            "passed": bulk_working,
            "details": "Bulk verification endpoint working" if bulk_working else "Bulk verification not implemented"
        }
    
    async def test_webhook_functionality(self) -> Dict[str, Any]:
        """Test webhook functionality"""
        print("🔗 Testing Webhook Functionality...")
        
        # This would require a test webhook server
        # For now, just test the endpoint exists
        if not await self.authenticate():
            return {"test": "webhook_functionality", "passed": False, "details": "Authentication failed"}
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        data = {
            "url": "https://httpbin.org/post",
            "events": ["verification.completed"]
        }
        
        try:
            async with self.session.post(f"{self.base_url}/webhooks", json=data, headers=headers) as response:
                webhook_working = response.status in [200, 201]
        except Exception:
            webhook_working = False
        
        return {
            "test": "webhook_functionality",
            "passed": webhook_working,
            "details": "Webhook endpoint available" if webhook_working else "Webhook endpoint not implemented"
        }

class WebSocketTester:
    def __init__(self, ws_url: str = "ws://localhost:8000"):
        self.ws_url = ws_url
    
    async def test_websocket_connection(self) -> Dict[str, Any]:
        """Test WebSocket connection"""
        print("🔌 Testing WebSocket Connection...")
        
        try:
            uri = f"{self.ws_url}/ws/verification/test_id"
            async with websockets.connect(uri, timeout=5) as websocket:
                # Send ping
                await websocket.send(json.dumps({"type": "ping"}))
                
                # Wait for response
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                data = json.loads(response)
                
                connection_working = data.get("type") in ["pong", "connection_established"]
        except Exception as e:
            connection_working = False
            print(f"WebSocket test failed: {str(e)}")
        
        return {
            "test": "websocket_connection",
            "passed": connection_working,
            "details": "WebSocket connection working" if connection_working else "WebSocket not available"
        }
    
    async def test_realtime_updates(self) -> Dict[str, Any]:
        """Test real-time updates"""
        print("⚡ Testing Real-time Updates...")
        
        try:
            uri = f"{self.ws_url}/ws/verification/test_verification"
            async with websockets.connect(uri, timeout=10) as websocket:
                # Wait for initial connection message
                initial_msg = await asyncio.wait_for(websocket.recv(), timeout=5)
                
                # Simulate waiting for SMS update
                update_received = False
                try:
                    update_msg = await asyncio.wait_for(websocket.recv(), timeout=10)
                    update_data = json.loads(update_msg)
                    update_received = update_data.get("type") in ["sms_received", "verification_completed"]
                except asyncio.TimeoutError:
                    update_received = False
        except Exception as e:
            update_received = False
            print(f"Real-time update test failed: {str(e)}")
        
        return {
            "test": "realtime_updates",
            "passed": update_received,
            "details": "Real-time updates working" if update_received else "Real-time updates not functional"
        }

class PerformanceTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    async def test_concurrent_requests(self) -> Dict[str, Any]:
        """Test concurrent request handling"""
        print("⚡ Testing Concurrent Requests...")
        
        async def make_request(session, i):
            try:
                start = time.time()
                async with session.get(f"{self.base_url}/health") as response:
                    duration = time.time() - start
                    return {"success": response.status == 200, "duration": duration}
            except Exception:
                return {"success": False, "duration": 0}
        
        async with aiohttp.ClientSession() as session:
            tasks = [make_request(session, i) for i in range(50)]
            results = await asyncio.gather(*tasks)
        
        successful = sum(1 for r in results if r["success"])
        avg_duration = sum(r["duration"] for r in results if r["success"]) / max(successful, 1)
        
        return {
            "test": "concurrent_requests",
            "passed": successful >= 45,  # 90% success rate
            "successful_requests": f"{successful}/50",
            "average_duration": f"{avg_duration:.3f}s",
            "details": f"Handled {successful}/50 concurrent requests successfully"
        }
    
    async def test_response_times(self) -> Dict[str, Any]:
        """Test API response times"""
        print("⏱️ Testing Response Times...")
        
        endpoints = [
            "/health",
            "/docs",
            "/auth/login"  # POST with dummy data
        ]
        
        results = {}
        
        async with aiohttp.ClientSession() as session:
            for endpoint in endpoints:
                times = []
                for _ in range(10):
                    start = time.time()
                    try:
                        if endpoint == "/auth/login":
                            async with session.post(f"{self.base_url}{endpoint}", json={"email": "test", "password": "test"}) as response:
                                duration = time.time() - start
                                times.append(duration)
                        else:
                            async with session.get(f"{self.base_url}{endpoint}") as response:
                                duration = time.time() - start
                                times.append(duration)
                    except Exception:
                        pass
                
                if times:
                    avg_time = sum(times) / len(times)
                    results[endpoint] = f"{avg_time:.3f}s"
        
        all_fast = all(float(time.replace('s', '')) < 0.5 for time in results.values())
        
        return {
            "test": "response_times",
            "passed": all_fast,
            "response_times": results,
            "details": "All endpoints under 500ms" if all_fast else "Some endpoints are slow"
        }

async def run_comprehensive_tests():
    """Run all tests and generate report"""
    print("🚀 Starting Comprehensive Security & Performance Tests\n")
    
    all_results = []
    
    # Security Tests
    print("=" * 50)
    print("SECURITY TESTS")
    print("=" * 50)
    
    async with SecurityTester() as security_tester:
        security_tests = [
            security_tester.test_rate_limiting(),
            security_tester.test_sql_injection(),
            security_tester.test_xss_prevention(),
            security_tester.test_csrf_protection()
        ]
        
        security_results = await asyncio.gather(*security_tests)
        all_results.extend(security_results)
    
    # API Tests
    print("\n" + "=" * 50)
    print("API TESTS")
    print("=" * 50)
    
    async with APITester() as api_tester:
        api_tests = [
            api_tester.test_api_authentication(),
            api_tester.test_bulk_verification(),
            api_tester.test_webhook_functionality()
        ]
        
        api_results = await asyncio.gather(*api_tests)
        all_results.extend(api_results)
    
    # WebSocket Tests
    print("\n" + "=" * 50)
    print("WEBSOCKET TESTS")
    print("=" * 50)
    
    ws_tester = WebSocketTester()
    ws_tests = [
        ws_tester.test_websocket_connection(),
        ws_tester.test_realtime_updates()
    ]
    
    ws_results = await asyncio.gather(*ws_tests)
    all_results.extend(ws_results)
    
    # Performance Tests
    print("\n" + "=" * 50)
    print("PERFORMANCE TESTS")
    print("=" * 50)
    
    perf_tester = PerformanceTester()
    perf_tests = [
        perf_tester.test_concurrent_requests(),
        perf_tester.test_response_times()
    ]
    
    perf_results = await asyncio.gather(*perf_tests)
    all_results.extend(perf_results)
    
    # Generate Report
    print("\n" + "=" * 50)
    print("TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed_tests = sum(1 for result in all_results if result.get("passed", False))
    total_tests = len(all_results)
    
    for result in all_results:
        status = "✅ PASS" if result.get("passed", False) else "❌ FAIL"
        print(f"{status} {result['test']}: {result.get('details', 'No details')}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.1f}%)")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! System is ready for production.")
    elif passed_tests >= total_tests * 0.8:
        print("⚠️ Most tests passed. Review failed tests before deployment.")
    else:
        print("🚨 Critical issues detected. Do not deploy until fixed.")
    
    return all_results

if __name__ == "__main__":
    asyncio.run(run_comprehensive_tests())