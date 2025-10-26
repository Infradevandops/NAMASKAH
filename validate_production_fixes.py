#!/usr/bin/env python3
"""Validate production fixes implementation."""

import os
import sys
from pathlib import Path


def check_middleware_activation():
    """Check if middleware is properly activated."""
    main_py = Path("main.py")
    if not main_py.exists():
        return False, "main.py not found"

    content = main_py.read_text()

    # Check imports
    required_imports = [
        "from app.middleware.security import",
        "from app.middleware.logging import",
        "from app.middleware.rate_limiting import",
    ]

    for import_line in required_imports:
        if import_line not in content:
            return False, f"Missing import: {import_line}"

    # Check middleware activation
    if "app.add_middleware(JWTAuthMiddleware)" not in content:
        return False, "JWTAuthMiddleware not activated"

    return True, "Middleware properly activated"


def check_secrets_management():
    """Check if secrets management is implemented."""
    secrets_py = Path("app/core/secrets.py")
    if not secrets_py.exists():
        return False, "secrets.py not found"

    config_py = Path("app/core/config.py")
    if not config_py.exists():
        return False, "config.py not found"

    config_content = config_py.read_text()
    if "SecretsManager.validate_required_secrets()" not in config_content:
        return False, "Secrets validation not integrated"

    return True, "Secrets management implemented"


def check_redis_activation():
    """Check if Redis caching is activated."""
    main_py = Path("main.py")
    content = main_py.read_text()

    if "from app.core.caching import cache" not in content:
        return False, "Cache import missing"

    if "await cache.connect()" not in content:
        return False, "Cache connection not activated"

    return True, "Redis caching activated"


def check_health_checks():
    """Check if health checks are implemented."""
    dockerfile = Path("Dockerfile")
    if not dockerfile.exists():
        return False, "Dockerfile not found"

    content = dockerfile.read_text()
    if "HEALTHCHECK" not in content:
        return False, "Docker health check missing"

    k8s_file = Path("k8s-deployment.yaml")
    if k8s_file.exists():
        k8s_content = k8s_file.read_text()
        if "livenessProbe" not in k8s_content:
            return False, "Kubernetes liveness probe missing"

    return True, "Health checks implemented"


def check_production_config():
    """Check if production configuration exists."""
    prod_env = Path(".env.production")
    if not prod_env.exists():
        return False, ".env.production not found"

    prod_compose = Path("docker-compose.prod.yml")
    if not prod_compose.exists():
        return False, "docker-compose.prod.yml not found"

    return True, "Production configuration ready"


def main():
    """Run all validation checks."""
    print("🔍 Validating Production Fixes Implementation")
    print("=" * 50)

    checks = [
        ("Security Middleware", check_middleware_activation),
        ("Secrets Management", check_secrets_management),
        ("Redis Caching", check_redis_activation),
        ("Health Checks", check_health_checks),
        ("Production Config", check_production_config),
    ]

    all_passed = True

    for name, check_func in checks:
        try:
            passed, message = check_func()
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status} {name}: {message}")

            if not passed:
                all_passed = False

        except Exception as e:
            print(f"❌ FAIL {name}: Error - {e}")
            all_passed = False

    print("=" * 50)

    if all_passed:
        print("🎉 All production fixes implemented successfully!")
        print("✅ Ready for production deployment")
        return 0
    else:
        print("⚠️  Some fixes need attention")
        print("❌ Not ready for production")
        return 1


if __name__ == "__main__":
    sys.exit(main())
