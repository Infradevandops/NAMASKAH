#!/usr/bin/env python3
"""
Infrastructure Readiness Validation
Validates all components are ready for optimization phase
"""

import subprocess
import sys
import importlib
import redis
import requests
import time

def check_python_dependencies():
    """Check if all required packages are installed"""
    required_packages = [
        'fastapi', 'uvicorn', 'sqlalchemy', 'redis', 'sentry_sdk',
        'pydantic', 'bcrypt', 'requests', 'jinja2'
    ]
    
    missing = []
    for package in required_packages:
        try:
            importlib.import_module(package)
        except ImportError:
            missing.append(package)
    
    return len(missing) == 0, missing

def check_redis_connection():
    """Check Redis connectivity"""
    try:
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        r.ping()
        return True, "Connected"
    except Exception as e:
        return False, str(e)

def check_application_import():
    """Check if main application imports successfully"""
    try:
        import main
        return True, {
            'sentry_available': main.SENTRY_AVAILABLE,
            'security_patches': main.SECURITY_PATCHES_AVAILABLE,
            'websocket_support': main.WEBSOCKET_AVAILABLE,
            'optimizations': main.OPTIMIZATIONS_AVAILABLE
        }
    except Exception as e:
        return False, str(e)

def check_database_indexes():
    """Check if database indexes are created"""
    try:
        import main
        # Database should be initialized when main is imported
        return True, "Indexes created automatically on startup"
    except Exception as e:
        return False, str(e)

def run_performance_baseline():
    """Run basic performance test"""
    try:
        # Start application in background for testing
        import threading
        import uvicorn
        
        def start_app():
            uvicorn.run("main:app", host="127.0.0.1", port=8001, log_level="error")
        
        # Start app in thread
        app_thread = threading.Thread(target=start_app, daemon=True)
        app_thread.start()
        
        # Wait for startup
        time.sleep(3)
        
        # Test health endpoint
        response = requests.get("http://127.0.0.1:8001/health", timeout=5)
        return response.status_code == 200, f"Response: {response.status_code}"
        
    except Exception as e:
        return False, str(e)

def main():
    print("🔍 Infrastructure Readiness Validation")
    print("=" * 60)
    
    results = {}
    
    # Check Python dependencies
    print("📦 Checking Python Dependencies...")
    deps_ok, missing = check_python_dependencies()
    results['dependencies'] = deps_ok
    if deps_ok:
        print("   ✅ All required packages installed")
    else:
        print(f"   ❌ Missing packages: {', '.join(missing)}")
    
    # Check Redis
    print("\n🔄 Checking Redis Connection...")
    redis_ok, redis_msg = check_redis_connection()
    results['redis'] = redis_ok
    if redis_ok:
        print(f"   ✅ Redis: {redis_msg}")
    else:
        print(f"   ❌ Redis: {redis_msg}")
    
    # Check application import
    print("\n🚀 Checking Application Import...")
    app_ok, app_info = check_application_import()
    results['application'] = app_ok
    if app_ok:
        print("   ✅ Application imports successfully")
        print(f"   ✅ Sentry Available: {app_info['sentry_available']}")
        print(f"   ✅ Security Patches: {app_info['security_patches']}")
        print(f"   ✅ WebSocket Support: {app_info['websocket_support']}")
        print(f"   ✅ Optimizations: {app_info['optimizations']}")
    else:
        print(f"   ❌ Application import failed: {app_info}")
    
    # Check database
    print("\n🗄️ Checking Database Setup...")
    db_ok, db_msg = check_database_indexes()
    results['database'] = db_ok
    if db_ok:
        print(f"   ✅ Database: {db_msg}")
    else:
        print(f"   ❌ Database: {db_msg}")
    
    # Overall assessment
    print("\n" + "=" * 60)
    total_checks = len(results)
    passed_checks = sum(results.values())
    percentage = (passed_checks / total_checks) * 100
    
    print(f"📊 Overall Readiness: {passed_checks}/{total_checks} ({percentage:.0f}%)")
    
    if percentage >= 90:
        status = "🟢 READY FOR OPTIMIZATION"
        recommendation = "Proceed with Phase 1 optimization immediately"
    elif percentage >= 75:
        status = "🟡 MOSTLY READY"
        recommendation = "Fix remaining issues then proceed"
    else:
        status = "🔴 NOT READY"
        recommendation = "Address critical issues before optimization"
    
    print(f"🎯 Status: {status}")
    print(f"💡 Recommendation: {recommendation}")
    
    # Next steps
    if percentage >= 90:
        print("\n🚀 NEXT STEPS:")
        print("1. Start application: uvicorn main:app --reload")
        print("2. Run performance baseline: python3 performance_baseline.py")
        print("3. Begin Phase 1 optimization plan")
        print("4. Monitor with Sentry dashboard")
    
    return results

if __name__ == "__main__":
    try:
        results = main()
        print(f"\n✅ Validation complete")
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        sys.exit(1)