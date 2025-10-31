#!/usr/bin/env python3
"""Fix database issues in production"""

import os
import sys
sys.path.append('.')

def fix_sqlalchemy_text_issue():
    """Fix SQLAlchemy text() issue in health checks"""
    
    # Fix health_checks.py
    health_checks_path = "app/core/health_checks.py"
    
    try:
        with open(health_checks_path, 'r') as f:
            content = f.read()
        
        # Replace raw SQL strings with text() wrapper
        fixes = [
            ('SELECT 1', 'text("SELECT 1")'),
            ("'SELECT 1'", 'text("SELECT 1")'),
            ('"SELECT 1"', 'text("SELECT 1")'),
            ('SELECT version()', 'text("SELECT version()")'),
            ("'SELECT version()'", 'text("SELECT version()")'),
        ]
        
        updated = False
        for old, new in fixes:
            if old in content and 'text(' not in content:
                content = content.replace(old, new)
                updated = True
        
        # Add text import if needed
        if updated and 'from sqlalchemy import text' not in content:
            if 'from sqlalchemy import' in content:
                content = content.replace(
                    'from sqlalchemy import',
                    'from sqlalchemy import text,'
                )
            else:
                content = 'from sqlalchemy import text\n' + content
        
        if updated:
            with open(health_checks_path, 'w') as f:
                f.write(content)
            print(f"✅ Fixed {health_checks_path}")
        else:
            print(f"ℹ️ {health_checks_path} already correct or not found")
            
    except FileNotFoundError:
        print(f"⚠️ {health_checks_path} not found")
    except Exception as e:
        print(f"❌ Error fixing {health_checks_path}: {e}")

def create_minimal_health_check():
    """Create a minimal, working health check"""
    
    health_check_content = '''"""Health check utilities for system monitoring."""
from typing import Dict, Any
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

def check_database_health(db: Session) -> Dict[str, Any]:
    """Check database connectivity and health."""
    try:
        # Simple connectivity test
        result = db.execute(text("SELECT 1")).fetchone()
        if result and result[0] == 1:
            return {
                "status": "healthy",
                "message": "Database connection successful"
            }
        else:
            return {
                "status": "unhealthy", 
                "error": "Database query returned unexpected result"
            }
    except SQLAlchemyError as e:
        return {
            "status": "unhealthy",
            "error": f"Database error: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": f"Unexpected error: {str(e)}"
        }

def check_system_health(db: Session) -> Dict[str, Any]:
    """Comprehensive system health check."""
    health_status = {
        "status": "healthy",
        "timestamp": None,
        "services": {}
    }
    
    # Check database
    db_health = check_database_health(db)
    health_status["services"]["database"] = db_health
    
    # Overall status
    if db_health["status"] != "healthy":
        health_status["status"] = "unhealthy"
    
    return health_status
'''
    
    try:
        os.makedirs("app/core", exist_ok=True)
        with open("app/core/health_checks.py", 'w') as f:
            f.write(health_check_content)
        print("✅ Created minimal health check")
    except Exception as e:
        print(f"❌ Error creating health check: {e}")

def fix_auth_service_imports():
    """Fix authentication service imports"""
    
    try:
        # Check if auth service exists and fix imports
        auth_service_path = "app/services/auth_service.py"
        
        if os.path.exists(auth_service_path):
            with open(auth_service_path, 'r') as f:
                content = f.read()
            
            # Ensure proper imports
            required_imports = [
                "from sqlalchemy import text",
                "from sqlalchemy.exc import SQLAlchemyError"
            ]
            
            updated = False
            for imp in required_imports:
                if imp not in content:
                    # Add import at the top
                    lines = content.split('\n')
                    import_line = imp
                    
                    # Find where to insert
                    insert_idx = 0
                    for i, line in enumerate(lines):
                        if line.startswith('from ') or line.startswith('import '):
                            insert_idx = i + 1
                    
                    lines.insert(insert_idx, import_line)
                    content = '\n'.join(lines)
                    updated = True
            
            if updated:
                with open(auth_service_path, 'w') as f:
                    f.write(content)
                print("✅ Fixed auth service imports")
        
    except Exception as e:
        print(f"❌ Error fixing auth service: {e}")

def main():
    """Main function to fix database issues"""
    print("🔧 Fixing Database Issues")
    print("=" * 40)
    
    # Fix SQLAlchemy text() issues
    print("1. Fixing SQLAlchemy text() issues...")
    fix_sqlalchemy_text_issue()
    
    # Create minimal health check
    print("2. Creating minimal health check...")
    create_minimal_health_check()
    
    # Fix auth service imports
    print("3. Fixing auth service imports...")
    fix_auth_service_imports()
    
    print("\n✅ Database fixes applied!")
    print("📝 Next steps:")
    print("   1. Commit and push changes")
    print("   2. Wait for deployment")
    print("   3. Test health endpoint")

if __name__ == "__main__":
    main()