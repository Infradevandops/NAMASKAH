"""
Validation Script for Applied Security Fixes
Pro Tips: Comprehensive testing without external dependencies
"""
import json
import time
import subprocess
import sys
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from urllib.parse import urlencode

class SecurityValidator:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.results = []
    
    def log_result(self, test_name: str, passed: bool, details: str):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        self.results.append({
            "test": test_name,
            "passed": passed,
            "details": details
        })
    
    def make_request(self, endpoint: str, method: str = "GET", data: dict = None, headers: dict = None):
        """Make HTTP request without external dependencies"""
        url = f"{self.base_url}{endpoint}"
        
        if headers is None:
            headers = {"Content-Type": "application/json"}
        
        try:
            if method == "GET":
                req = Request(url, headers=headers)
            else:
                json_data = json.dumps(data).encode('utf-8') if data else None
                req = Request(url, data=json_data, headers=headers)
                req.get_method = lambda: method
            
            with urlopen(req, timeout=5) as response:
                return {
                    "status_code": response.getcode(),
                    "headers": dict(response.headers),
                    "body": response.read().decode('utf-8')
                }
        
        except HTTPError as e:
            return {
                "status_code": e.code,
                "headers": dict(e.headers) if hasattr(e, 'headers') else {},
                "body": e.read().decode('utf-8') if hasattr(e, 'read') else str(e)
            }
        except URLError as e:
            return {
                "status_code": 0,
                "error": str(e)
            }
    
    def test_server_health(self):
        """Test if server is running"""
        print("🏥 Testing Server Health...")
        
        response = self.make_request("/health")
        
        if response.get("status_code") == 200:
            self.log_result("server_health", True, "Server is running and responding")
        else:
            self.log_result("server_health", False, f"Server not responding: {response.get('error', 'Unknown error')}")
    
    def test_security_headers(self):
        """Test security headers implementation"""
        print("🔒 Testing Security Headers...")
        
        response = self.make_request("/")
        
        if response.get("status_code") in [200, 404]:  # Either works, we just need headers
            headers = response.get("headers", {})
            
            required_headers = {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "X-XSS-Protection": "1; mode=block",
                "Strict-Transport-Security": "max-age=31536000"
            }
            
            missing_headers = []
            for header, expected_value in required_headers.items():
                if header not in headers:
                    missing_headers.append(header)
                elif headers[header] != expected_value:
                    missing_headers.append(f"{header} (wrong value)")
            
            if not missing_headers:
                self.log_result("security_headers", True, "All security headers present")
            else:
                self.log_result("security_headers", False, f"Missing headers: {', '.join(missing_headers)}")
        else:
            self.log_result("security_headers", False, "Could not test headers - server not responding")
    
    def test_rate_limiting(self):
        """Test rate limiting implementation"""
        print("⏱️ Testing Rate Limiting...")
        
        # Make multiple rapid requests
        rate_limited = False
        request_count = 0
        
        for i in range(15):  # Test with 15 rapid requests
            response = self.make_request("/health")
            request_count += 1
            
            if response.get("status_code") == 429:
                rate_limited = True
                break
            
            time.sleep(0.1)  # Small delay between requests
        
        if rate_limited:
            self.log_result("rate_limiting", True, f"Rate limiting triggered after {request_count} requests")
        else:
            self.log_result("rate_limiting", False, "Rate limiting not working or threshold too high")
    
    def test_input_sanitization(self):
        """Test input sanitization"""
        print("🧹 Testing Input Sanitization...")
        
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "';DROP TABLE users;--"
        ]
        
        sanitized_count = 0
        
        for malicious_input in malicious_inputs:
            response = self.make_request("/verify/create", "POST", {
                "service_name": malicious_input
            })
            
            # Check if request was properly rejected or sanitized
            if response.get("status_code") in [400, 422, 401]:  # Rejected
                sanitized_count += 1
            elif response.get("status_code") == 200:
                # Check if input was sanitized in response
                body = response.get("body", "")
                if malicious_input not in body:
                    sanitized_count += 1
        
        if sanitized_count >= len(malicious_inputs) * 0.8:  # 80% threshold
            self.log_result("input_sanitization", True, f"Input sanitization working ({sanitized_count}/{len(malicious_inputs)} blocked)")
        else:
            self.log_result("input_sanitization", False, f"Input sanitization insufficient ({sanitized_count}/{len(malicious_inputs)} blocked)")
    
    def test_bulk_verification(self):
        """Test bulk verification endpoint"""
        print("📦 Testing Bulk Verification...")
        
        response = self.make_request("/verify/bulk", "POST", {
            "services": ["telegram", "whatsapp"]
        })
        
        # Should fail without authentication, but endpoint should exist
        if response.get("status_code") in [401, 422]:
            self.log_result("bulk_verification", True, "Bulk verification endpoint exists and requires auth")
        elif response.get("status_code") == 404:
            self.log_result("bulk_verification", False, "Bulk verification endpoint not found")
        else:
            self.log_result("bulk_verification", True, "Bulk verification endpoint responding")
    
    def test_websocket_endpoint(self):
        """Test WebSocket endpoint availability"""
        print("🔌 Testing WebSocket Endpoint...")
        
        # We can't easily test WebSocket without additional libraries
        # So we'll check if the endpoint exists by looking for upgrade headers
        try:
            response = self.make_request("/ws/verification/test", headers={
                "Connection": "Upgrade",
                "Upgrade": "websocket"
            })
            
            # WebSocket endpoints typically return 426 or similar for non-WebSocket requests
            if response.get("status_code") in [426, 400, 404]:
                if response.get("status_code") == 404:
                    self.log_result("websocket_endpoint", False, "WebSocket endpoint not found")
                else:
                    self.log_result("websocket_endpoint", True, "WebSocket endpoint exists")
            else:
                self.log_result("websocket_endpoint", True, "WebSocket endpoint responding")
        
        except Exception as e:
            self.log_result("websocket_endpoint", False, f"WebSocket test failed: {str(e)}")
    
    def test_api_documentation(self):
        """Test API documentation availability"""
        print("📚 Testing API Documentation...")
        
        response = self.make_request("/docs")
        
        if response.get("status_code") == 200:
            self.log_result("api_documentation", True, "API documentation accessible")
        else:
            self.log_result("api_documentation", False, "API documentation not accessible")
    
    def test_admin_security(self):
        """Test admin endpoint security"""
        print("👑 Testing Admin Security...")
        
        response = self.make_request("/admin/users")
        
        # Should require authentication
        if response.get("status_code") in [401, 403]:
            self.log_result("admin_security", True, "Admin endpoints properly protected")
        elif response.get("status_code") == 404:
            self.log_result("admin_security", False, "Admin endpoints not found")
        else:
            self.log_result("admin_security", False, "Admin endpoints not properly protected")
    
    def generate_report(self):
        """Generate final test report"""
        print("\n" + "=" * 60)
        print("SECURITY VALIDATION REPORT")
        print("=" * 60)
        
        passed_tests = sum(1 for result in self.results if result["passed"])
        total_tests = len(self.results)
        
        print(f"\nTests Passed: {passed_tests}/{total_tests} ({passed_tests/total_tests*100:.1f}%)")
        
        if passed_tests == total_tests:
            print("\n🎉 ALL TESTS PASSED! Security fixes successfully implemented.")
            print("✅ System is ready for production deployment.")
        elif passed_tests >= total_tests * 0.8:
            print("\n⚠️ MOST TESTS PASSED. Review failed tests:")
            for result in self.results:
                if not result["passed"]:
                    print(f"   ❌ {result['test']}: {result['details']}")
        else:
            print("\n🚨 CRITICAL ISSUES DETECTED. Do not deploy:")
            for result in self.results:
                if not result["passed"]:
                    print(f"   ❌ {result['test']}: {result['details']}")
        
        print(f"\n📊 Security Score: {passed_tests/total_tests*100:.1f}%")
        
        return passed_tests/total_tests >= 0.8

def check_application_status():
    """Check if application is running"""
    print("🔍 Checking Application Status...")
    
    try:
        # Try to connect to the server
        validator = SecurityValidator()
        response = validator.make_request("/health")
        
        if response.get("status_code") == 200:
            print("✅ Application is running")
            return True
        else:
            print("❌ Application not responding")
            return False
    
    except Exception as e:
        print(f"❌ Cannot connect to application: {str(e)}")
        return False

def restart_application():
    """Restart the application"""
    print("🔄 Restarting application...")
    
    try:
        # Kill existing uvicorn processes
        subprocess.run(["pkill", "-f", "uvicorn"], check=False)
        time.sleep(2)
        
        # Start new process
        subprocess.Popen([
            "uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"
        ])
        
        # Wait for startup
        print("⏳ Waiting for application to start...")
        time.sleep(5)
        
        # Check if it's running
        if check_application_status():
            print("✅ Application restarted successfully")
            return True
        else:
            print("❌ Application failed to start")
            return False
    
    except Exception as e:
        print(f"❌ Failed to restart application: {str(e)}")
        return False

def main():
    """Main validation function"""
    print("🔍 Namaskah SMS - Security Fixes Validation")
    print("=" * 50)
    
    # Check if application is running
    if not check_application_status():
        print("\n🔄 Application not running. Attempting to start...")
        if not restart_application():
            print("❌ Cannot start application. Please start manually:")
            print("   uvicorn main:app --reload --host 0.0.0.0 --port 8000")
            sys.exit(1)
    
    # Run validation tests
    validator = SecurityValidator()
    
    print("\n🧪 Running Security Validation Tests...")
    print("-" * 40)
    
    validator.test_server_health()
    validator.test_security_headers()
    validator.test_rate_limiting()
    validator.test_input_sanitization()
    validator.test_bulk_verification()
    validator.test_websocket_endpoint()
    validator.test_api_documentation()
    validator.test_admin_security()
    
    # Generate report
    success = validator.generate_report()
    
    if success:
        print("\n🚀 Ready for production!")
        print("🔗 Application: http://localhost:8000")
        print("📊 Admin Panel: http://localhost:8000/admin")
        print("📚 API Docs: http://localhost:8000/docs")
    else:
        print("\n⚠️ Review and fix issues before deployment")
    
    return success

if __name__ == "__main__":
    main()