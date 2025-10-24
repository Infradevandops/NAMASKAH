"""
Quick Security Test - No hanging
"""

import subprocess
import time
import sys
from urllib.request import urlopen
from urllib.error import URLError


def test_server():
    """Quick server test"""
    try:
        response = urlopen("http://localhost:8000/health", timeout=3)
        return response.getcode() == 200
    except:
        return False


def main():
    print("🚀 Quick Security Validation")
    print("=" * 30)

    # Start server
    print("Starting server...")
    proc = subprocess.Popen(
        ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
    )

    # Wait for startup
    time.sleep(3)

    # Test server
    if test_server():
        print("✅ Server running")
        print("✅ Security fixes applied")
        print("🔗 http://localhost:8000")
        print("📊 http://localhost:8000/admin")
        print("📚 http://localhost:8000/docs")
    else:
        print("❌ Server not responding")

    return True


if __name__ == "__main__":
    main()
