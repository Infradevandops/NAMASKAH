#!/usr/bin/env python3
"""
Simple test script for error handling (no external dependencies)
"""

import urllib.request
import urllib.parse
import urllib.error
import json
import sys


def test_endpoint(url, method="GET", data=None, headers=None):
    """Test an endpoint and return status"""
    try:
        if headers is None:
            headers = {}

        if data:
            data = json.dumps(data).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=data, headers=headers, method=method)

        with urllib.request.urlopen(req) as response:
            return response.status, "Success"

    except urllib.error.HTTPError as e:
        return e.code, f"HTTP Error: {e.reason}"
    except urllib.error.URLError as e:
        return None, f"URL Error: {e.reason}"
    except Exception as e:
        return None, f"Error: {str(e)}"


def main():
    base_url = "http://localhost:8000"

    print("🧪 Simple Error Handling Test")
    print("=" * 50)

    # Test cases
    tests = [
        ("Health Check", f"{base_url}/health", "GET", None, None, [200]),
        ("Invalid Auth", f"{base_url}/admin/stats", "GET", None, {}, [401, 403]),
        (
            "Invalid Login",
            f"{base_url}/auth/login",
            "POST",
            {"email": "invalid@test.com", "password": "wrong"},
            None,
            [401, 422],
        ),
        ("404 Test", f"{base_url}/nonexistent", "GET", None, None, [404]),
    ]

    results = []

    for name, url, method, data, headers, expected_codes in tests:
        status, message = test_endpoint(url, method, data, headers)

        if status in expected_codes:
            result = f"✅ {name}: {status} - {message}"
        elif status is None:
            result = f"🔥 {name}: Connection failed - {message}"
        else:
            result = f"❌ {name}: Expected {expected_codes}, got {status} - {message}"

        results.append(result)
        print(result)

    print("\n" + "=" * 50)
    passed = len([r for r in results if r.startswith("✅")])
    failed = len([r for r in results if r.startswith("❌")])
    errors = len([r for r in results if r.startswith("🔥")])

    print(f"📊 Results: {passed} passed, {failed} failed, {errors} errors")

    if errors > 0:
        print("\n⚠️  Server may not be running. Start with: uvicorn main:app --reload")


if __name__ == "__main__":
    main()
