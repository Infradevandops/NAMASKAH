#!/usr/bin/env python3
"""
Final Python Linting Fixes
Address remaining critical linting issues.
"""

import os
import re
from pathlib import Path

def fix_remaining_issues():
    """Fix remaining linting issues."""
    print("🔧 Applying final linting fixes...")
    
    # Fix unused variables by prefixing with underscore
    files_to_fix = [
        'app/middleware/logging.py',
        'app/core/logging.py', 
        'app/services/payment_service.py',
        'app/api/verification.py'
    ]
    
    fixed_count = 0
    
    for file_path in files_to_fix:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                # Fix common unused variable patterns
                patterns = [
                    # Fix unused exception variables
                    (r'except\s+(\w+)\s+as\s+(\w+):\s*\n\s*pass', r'except \1:\n        pass'),
                    # Fix unused function parameters
                    (r'def\s+\w+\([^)]*(\w+):\s*(\w+)[^)]*\):', r'def \1(\2: _\2):'),
                ]
                
                for pattern, replacement in patterns:
                    content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
                
                if content != original_content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    fixed_count += 1
                    
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
    
    print(f"✅ Applied final fixes to {fixed_count} files")

def main():
    """Run final linting fixes."""
    print("🎯 Final Python linting fixes...")
    print("=" * 50)
    
    os.chdir('/Users/machine/Project/GitHub/Namaskah. app')
    
    fix_remaining_issues()
    
    print("=" * 50)
    print("✅ Final linting fixes completed!")
    
    return True

if __name__ == "__main__":
    main()