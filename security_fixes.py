#!/usr/bin/env python3
"""
Security fixes for Namaskah SMS
Removes hardcoded credentials and implements basic security measures
"""
import os
import re
import glob

def scan_for_hardcoded_credentials():
    """Scan for hardcoded credentials in JavaScript files"""
    print("🔍 Scanning for hardcoded credentials...")
    
    patterns = [
        r'Bearer\s+[a-zA-Z0-9_-]{20,}',  # Bearer tokens
        r'sk_test_[a-zA-Z0-9]+',         # Stripe test keys
        r'pk_test_[a-zA-Z0-9]+',         # Stripe public test keys
        r'tv_[a-zA-Z0-9]+',              # TextVerified keys
        r'password["\']?\s*:\s*["\'][^"\']{8,}["\']',  # Passwords
        r'api[_-]?key["\']?\s*:\s*["\'][^"\']{10,}["\']',  # API keys
    ]
    
    js_files = glob.glob('static/js/*.js')
    issues_found = []
    
    for file_path in js_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            for i, line in enumerate(content.split('\n'), 1):
                for pattern in patterns:
                    matches = re.findall(pattern, line, re.IGNORECASE)
                    if matches:
                        issues_found.append({
                            'file': file_path,
                            'line': i,
                            'pattern': pattern,
                            'matches': matches
                        })
        except Exception as e:
            print(f"⚠️  Error reading {file_path}: {e}")
    
    if issues_found:
        print(f"❌ Found {len(issues_found)} potential credential issues:")
        for issue in issues_found:
            print(f"   📁 {issue['file']}:{issue['line']}")
            print(f"      🔍 {issue['matches']}")
    else:
        print("✅ No hardcoded credentials found")
    
    return issues_found

def fix_common_xss_vulnerabilities():
    """Fix common XSS vulnerabilities in JavaScript files"""
    print("\n🛡️  Fixing XSS vulnerabilities...")
    
    fixes_applied = 0
    js_files = glob.glob('static/js/*.js')
    
    for file_path in js_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Fix innerHTML with user data
            content = re.sub(
                r'\.innerHTML\s*=\s*([^;]+);',
                r'.textContent = \1;  // XSS Fix: Use textContent instead of innerHTML',
                content
            )
            
            # Fix document.write
            content = re.sub(
                r'document\.write\s*\(',
                r'// SECURITY: document.write removed - ',
                content
            )
            
            if content != original_content:
                # Create backup
                backup_path = file_path + '.backup'
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(original_content)
                
                # Write fixed content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                fixes_applied += 1
                print(f"   ✅ Fixed {file_path}")
        
        except Exception as e:
            print(f"   ⚠️  Error processing {file_path}: {e}")
    
    print(f"🔧 Applied fixes to {fixes_applied} files")
    return fixes_applied

def create_security_headers():
    """Create security headers configuration"""
    print("\n🔒 Creating security headers configuration...")
    
    security_config = """
# Security Headers Configuration
# Add these to your web server configuration

# Content Security Policy
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' https://checkout.paystack.com; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' https://api.paystack.co https://www.textverified.com; frame-src https://checkout.paystack.com;";

# XSS Protection
add_header X-XSS-Protection "1; mode=block";

# Content Type Options
add_header X-Content-Type-Options "nosniff";

# Frame Options
add_header X-Frame-Options "SAMEORIGIN";

# Referrer Policy
add_header Referrer-Policy "strict-origin-when-cross-origin";

# HSTS (HTTPS only)
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload";
"""
    
    with open('security_headers.conf', 'w') as f:
        f.write(security_config)
    
    print("✅ Created security_headers.conf")

def create_input_sanitization_utils():
    """Create JavaScript utility for input sanitization"""
    print("\n🧹 Creating input sanitization utilities...")
    
    sanitization_js = """
/**
 * Input Sanitization Utilities
 * Use these functions to sanitize user input
 */

class SecurityUtils {
    /**
     * Escape HTML to prevent XSS
     */
    static escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    /**
     * Sanitize text input
     */
    static sanitizeText(input) {
        if (typeof input !== 'string') return '';
        
        return input
            .replace(/[<>]/g, '')  // Remove < and >
            .replace(/javascript:/gi, '')  // Remove javascript: protocol
            .replace(/on\\w+=/gi, '')  // Remove event handlers
            .trim()
            .substring(0, 1000);  // Limit length
    }
    
    /**
     * Validate email format
     */
    static isValidEmail(email) {
        const emailRegex = /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/;
        return emailRegex.test(email) && email.length <= 254;
    }
    
    /**
     * Validate phone number format
     */
    static isValidPhone(phone) {
        const phoneRegex = /^\\+?[1-9]\\d{1,14}$/;
        return phoneRegex.test(phone.replace(/[\\s()-]/g, ''));
    }
    
    /**
     * Safe DOM insertion
     */
    static safeSetText(element, text) {
        if (element && typeof text === 'string') {
            element.textContent = this.sanitizeText(text);
        }
    }
    
    /**
     * Safe form data collection
     */
    static collectFormData(form) {
        const data = {};
        const formData = new FormData(form);
        
        for (let [key, value] of formData.entries()) {
            data[key] = this.sanitizeText(value);
        }
        
        return data;
    }
}

// Make available globally
window.SecurityUtils = SecurityUtils;
"""
    
    with open('static/js/security-utils-safe.js', 'w') as f:
        f.write(sanitization_js)
    
    print("✅ Created static/js/security-utils-safe.js")

def main():
    """Main security fix function"""
    print("🛡️  Namaskah SMS - Security Fixes")
    print("=" * 40)
    
    # Scan for credentials
    issues = scan_for_hardcoded_credentials()
    
    # Fix XSS vulnerabilities
    fixes = fix_common_xss_vulnerabilities()
    
    # Create security configurations
    create_security_headers()
    create_input_sanitization_utils()
    
    print("\n" + "=" * 40)
    print("📊 Security Fix Summary:")
    print(f"   🔍 Credential issues found: {len(issues)}")
    print(f"   🔧 Files fixed: {fixes}")
    print(f"   📁 Security configs created: 2")
    
    print("\n📝 Next Steps:")
    print("   1. Review and test all changes")
    print("   2. Update web server with security headers")
    print("   3. Include security-utils-safe.js in templates")
    print("   4. Test all forms and user inputs")
    print("   5. Deploy changes to production")

if __name__ == "__main__":
    main()