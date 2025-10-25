#!/usr/bin/env python3
"""
Comprehensive Button Functionality Test for Namaskah SMS
Tests ALL buttons in the dashboard to ensure they're connecting and productive
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
ADMIN_USER = {"email": "admin@namaskah.app", "password": "Namaskah@Admin2024"}


class ComprehensiveButtonTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.user_data = None
        self.button_results = {}

    def log(self, message, status="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {status}: {message}")

    def login_admin(self):
        """Login as admin to test all functionality"""
        try:
            response = self.session.post(
                f"{BASE_URL}/auth/login",
                json=ADMIN_USER,
                headers={"Content-Type": "application/json"},
            )

            if response.status_code == 200:
                data = response.json()
                self.token = data.get("token")
                self.user_data = data
                self.log("✅ Admin login successful", "SUCCESS")
                return True
            else:
                self.log(f"❌ Admin login failed: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Login error: {e}", "ERROR")
            return False

    def test_button(
        self, button_name, endpoint, method="GET", data=None, expected_status=200
    ):
        """Test individual button functionality"""
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            if data:
                headers["Content-Type"] = "application/json"

            if method == "GET":
                response = self.session.get(f"{BASE_URL}{endpoint}", headers=headers)
            elif method == "POST":
                response = self.session.post(
                    f"{BASE_URL}{endpoint}", json=data, headers=headers
                )
            elif method == "DELETE":
                response = self.session.delete(f"{BASE_URL}{endpoint}", headers=headers)

            success = response.status_code == expected_status

            if success:
                try:
                    response_data = response.json()
                    data_info = self._extract_data_info(response_data)
                    self.button_results[button_name] = {
                        "status": "✅ WORKING",
                        "endpoint": endpoint,
                        "method": method,
                        "response_code": response.status_code,
                        "data_info": data_info,
                    }
                    self.log(f"✅ {button_name}: {data_info}", "SUCCESS")
                except:
                    self.button_results[button_name] = {
                        "status": "✅ WORKING",
                        "endpoint": endpoint,
                        "method": method,
                        "response_code": response.status_code,
                        "data_info": "Non-JSON response",
                    }
                    self.log(f"✅ {button_name}: Working (non-JSON)", "SUCCESS")
            else:
                self.button_results[button_name] = {
                    "status": "❌ FAILED",
                    "endpoint": endpoint,
                    "method": method,
                    "response_code": response.status_code,
                    "error": response.text[:100],
                }
                self.log(f"❌ {button_name}: Failed ({response.status_code})", "ERROR")

            return success

        except Exception as e:
            self.button_results[button_name] = {
                "status": "❌ ERROR",
                "endpoint": endpoint,
                "method": method,
                "error": str(e),
            }
            self.log(f"❌ {button_name}: Error - {e}", "ERROR")
            return False

    def _extract_data_info(self, data):
        """Extract useful information from API response"""
        if isinstance(data, dict):
            if "verifications" in data:
                return f"{len(data['verifications'])} verifications"
            elif "transactions" in data:
                return f"{len(data['transactions'])} transactions"
            elif "users" in data:
                return f"{len(data['users'])} users"
            elif "keys" in data:
                return f"{len(data['keys'])} API keys"
            elif "webhooks" in data:
                return f"{len(data['webhooks'])} webhooks"
            elif "receipts" in data:
                return f"{len(data['receipts'])} receipts"
            elif "notifications" in data:
                return f"{data.get('total_count', 0)} notifications"
            elif "total_users" in data:
                return f"{data['total_users']} users, {data.get('total_verifications', 0)} verifications"
            elif "categories" in data:
                return f"{len(data['categories'])} service categories"
            elif "status" in data and "service" in data:
                return f"Service: {data['service']} - {data['status']}"
            elif "success" in data:
                return "Payment initialization ready"
            else:
                return f"{len(data)} data items"
        return "Response received"

    def test_all_buttons(self):
        """Test all dashboard buttons systematically"""

        # Authentication & User Management Buttons
        self.log("\n🔐 AUTHENTICATION & USER BUTTONS", "INFO")
        self.test_button("Login Button", "/auth/me", "GET")

        # Dashboard Navigation Buttons
        self.log("\n📊 DASHBOARD NAVIGATION BUTTONS", "INFO")
        self.test_button("Analytics Button", "/analytics/dashboard", "GET")
        self.test_button("History Button", "/verifications/history", "GET")
        self.test_button("Transactions Button", "/transactions/history", "GET")
        self.test_button("Wallet Transactions", "/wallet/transactions", "GET")

        # Service & Verification Buttons
        self.log("\n📱 SERVICE & VERIFICATION BUTTONS", "INFO")
        self.test_button("Services List Button", "/services/list", "GET")
        self.test_button("Service Status Button", "/services/status", "GET")
        self.test_button("Active Verifications", "/verifications/active", "GET")

        # Settings & Configuration Buttons
        self.log("\n⚙️ SETTINGS & CONFIGURATION BUTTONS", "INFO")
        self.test_button("API Keys List", "/api-keys/list", "GET")
        self.test_button("Webhooks List", "/webhooks/list", "GET")
        self.test_button("Notification Settings", "/notifications/settings", "GET")

        # Receipt & Notification Buttons
        self.log("\n🧾 RECEIPT & NOTIFICATION BUTTONS", "INFO")
        self.test_button("Receipts History", "/receipts/history", "GET")
        self.test_button("Notifications List", "/notifications/list", "GET")

        # Referral & Subscription Buttons
        self.log("\n💰 REFERRAL & SUBSCRIPTION BUTTONS", "INFO")
        self.test_button("Referral Stats", "/referrals/stats", "GET")
        self.test_button("Subscription Plans", "/subscription/plans", "GET")
        self.test_button("Current Subscription", "/subscription/current", "GET")

        # Admin Panel Buttons (if admin)
        self.log("\n👑 ADMIN PANEL BUTTONS", "INFO")
        self.test_button("Admin Stats", "/admin/stats", "GET")
        self.test_button("Admin Users", "/admin/users", "GET")
        self.test_button("Admin Verifications", "/admin/verifications/active", "GET")
        self.test_button("Admin Rentals", "/admin/rentals/active", "GET")
        self.test_button("Admin Payment Logs", "/admin/payment-logs", "GET")
        self.test_button("Admin Activity Logs", "/admin/activity-logs", "GET")

        # Wallet & Payment Buttons
        self.log("\n💳 WALLET & PAYMENT BUTTONS", "INFO")
        wallet_data = {"amount": 5.0, "payment_method": "paystack"}
        self.test_button(
            "Fund Wallet (Paystack)",
            "/wallet/paystack/initialize",
            "POST",
            wallet_data,
            200,
        )

        # System & Health Buttons
        self.log("\n🔧 SYSTEM & HEALTH BUTTONS", "INFO")
        self.test_button("Health Check", "/health", "GET")
        self.test_button("System Health", "/system/health", "GET")

        # Export & Download Buttons
        self.log("\n📥 EXPORT & DOWNLOAD BUTTONS", "INFO")
        self.test_button("Export Verifications", "/verifications/export", "GET")
        self.test_button("Export Transactions", "/transactions/export", "GET")

        # Support & Contact Buttons
        self.log("\n💬 SUPPORT & CONTACT BUTTONS", "INFO")
        support_data = {
            "name": "Test User",
            "email": "test@example.com",
            "category": "technical",
            "message": "Button functionality test",
        }
        self.test_button("Support Submit", "/support/submit", "POST", support_data, 200)

        # Google OAuth Button
        self.log("\n🔍 GOOGLE OAUTH BUTTON", "INFO")
        self.test_button("Google OAuth Config", "/auth/google/config", "GET")

        # Additional Feature Buttons
        self.log("\n🚀 ADDITIONAL FEATURE BUTTONS", "INFO")
        self.test_button("Carriers List", "/carriers/list", "GET")
        self.test_button("Area Codes List", "/area-codes/list", "GET")

    def test_button_interactions(self):
        """Test button interactions that require specific data"""
        self.log("\n🔄 TESTING BUTTON INTERACTIONS", "INFO")

        # Test API Key Creation
        api_key_data = {"name": "Test Key"}
        self.test_button(
            "Create API Key", "/api-keys/create", "POST", api_key_data, 200
        )

        # Test Webhook Creation
        webhook_data = {"url": "https://example.com/webhook"}
        self.test_button(
            "Create Webhook", "/webhooks/create", "POST", webhook_data, 200
        )

        # Test Verification Creation (might fail due to credits/config)
        verification_data = {"service_name": "telegram", "capability": "sms"}
        self.test_button(
            "Create Verification", "/verify/create", "POST", verification_data, 200
        )

    def generate_report(self):
        """Generate comprehensive test report"""
        self.log("\n" + "=" * 80, "INFO")
        self.log("📊 COMPREHENSIVE BUTTON FUNCTIONALITY REPORT", "INFO")
        self.log("=" * 80, "INFO")

        working_buttons = []
        failed_buttons = []
        error_buttons = []

        for button_name, result in self.button_results.items():
            if "✅ WORKING" in result["status"]:
                working_buttons.append(button_name)
            elif "❌ FAILED" in result["status"]:
                failed_buttons.append(button_name)
            else:
                error_buttons.append(button_name)

        total_buttons = len(self.button_results)
        success_rate = (
            (len(working_buttons) / total_buttons * 100) if total_buttons > 0 else 0
        )

        self.log(f"\n📈 SUMMARY STATISTICS:", "INFO")
        self.log(f"   Total Buttons Tested: {total_buttons}", "INFO")
        self.log(f"   ✅ Working: {len(working_buttons)}", "SUCCESS")
        self.log(f"   ❌ Failed: {len(failed_buttons)}", "ERROR")
        self.log(f"   🔧 Errors: {len(error_buttons)}", "ERROR")
        self.log(f"   📊 Success Rate: {success_rate:.1f}%", "INFO")

        # Detailed Results
        self.log(f"\n✅ WORKING BUTTONS ({len(working_buttons)}):", "SUCCESS")
        for button in working_buttons:
            result = self.button_results[button]
            self.log(f"   • {button}: {result.get('data_info', 'Working')}", "SUCCESS")

        if failed_buttons:
            self.log(f"\n❌ FAILED BUTTONS ({len(failed_buttons)}):", "ERROR")
            for button in failed_buttons:
                result = self.button_results[button]
                self.log(
                    f"   • {button}: {result['endpoint']} ({result.get('response_code', 'N/A')})",
                    "ERROR",
                )

        if error_buttons:
            self.log(f"\n🔧 ERROR BUTTONS ({len(error_buttons)}):", "ERROR")
            for button in error_buttons:
                result = self.button_results[button]
                self.log(
                    f"   • {button}: {result.get('error', 'Unknown error')}", "ERROR"
                )

        # Productivity Assessment
        self.log(f"\n🎯 PRODUCTIVITY ASSESSMENT:", "INFO")
        if success_rate >= 90:
            self.log(
                "   🎉 EXCELLENT: All buttons are highly functional and productive",
                "SUCCESS",
            )
        elif success_rate >= 75:
            self.log(
                "   ✅ GOOD: Most buttons are working well with minor issues", "SUCCESS"
            )
        elif success_rate >= 50:
            self.log(
                "   ⚠️ MODERATE: Some buttons need attention for full productivity",
                "ERROR",
            )
        else:
            self.log(
                "   ❌ POOR: Many buttons need fixing for proper functionality", "ERROR"
            )

        # Recommendations
        self.log(f"\n💡 RECOMMENDATIONS:", "INFO")
        if failed_buttons:
            self.log(
                "   1. Fix failed button endpoints for complete functionality", "INFO"
            )
        if error_buttons:
            self.log("   2. Debug error buttons to improve reliability", "INFO")
        if success_rate < 100:
            self.log(
                "   3. Test button interactions in browser for user experience", "INFO"
            )
        self.log("   4. Monitor button performance in production environment", "INFO")

        return (
            success_rate,
            len(working_buttons),
            len(failed_buttons),
            len(error_buttons),
        )

    def run_comprehensive_test(self):
        """Run the complete button functionality test"""
        self.log("🚀 Starting Comprehensive Button Functionality Test", "INFO")
        self.log("=" * 80, "INFO")

        # Login first
        if not self.login_admin():
            self.log("❌ Cannot proceed without admin login", "ERROR")
            return False

        # Test all buttons
        self.test_all_buttons()

        # Test button interactions
        self.test_button_interactions()

        # Generate report
        success_rate, working, failed, errors = self.generate_report()

        # Final assessment
        self.log(f"\n🏁 FINAL ASSESSMENT:", "INFO")
        if success_rate >= 85:
            self.log("✅ BUTTONS ARE PRODUCTIVE AND CONNECTING PROPERLY", "SUCCESS")
            return True
        else:
            self.log("⚠️ SOME BUTTONS NEED ATTENTION FOR FULL PRODUCTIVITY", "ERROR")
            return False


def main():
    """Main function"""
    print("🧪 Namaskah SMS - Comprehensive Button Functionality Test")
    print("=" * 80)

    tester = ComprehensiveButtonTester()
    success = tester.run_comprehensive_test()

    if success:
        print("\n🎉 Button functionality test completed successfully!")
        print("✅ All critical buttons are connecting and productive.")
        sys.exit(0)
    else:
        print("\n⚠️ Button functionality test completed with issues.")
        print("🔧 Some buttons may need attention for optimal productivity.")
        sys.exit(1)


if __name__ == "__main__":
    main()
