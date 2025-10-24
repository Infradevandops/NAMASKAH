#!/usr/bin/env python3
"""
Verification Creation Fix for Namaskah SMS

This script identifies and fixes the "Failed to create verification" error
by addressing the root causes in the verification creation flow.
"""

import os
import sys
import json
from datetime import datetime

def analyze_verification_issue():
    """Analyze the verification creation issue and provide fixes"""
    
    print("🔍 Analyzing 'Failed to create verification' issue...")
    
    issues_found = []
    fixes_applied = []
    
    # Issue 1: Missing TEXTVERIFIED_API_KEY validation
    print("\n1. Checking TextVerified API configuration...")
    
    # Check if .env file exists
    env_file = "/Users/machine/Project/GitHub/Namaskah. app/.env"
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            env_content = f.read()
            
        if 'TEXTVERIFIED_API_KEY=' not in env_content or 'TEXTVERIFIED_EMAIL=' not in env_content:
            issues_found.append("Missing TextVerified API credentials in .env file")
            
            # Add missing credentials template
            missing_vars = []
            if 'TEXTVERIFIED_API_KEY=' not in env_content:
                missing_vars.append('TEXTVERIFIED_API_KEY=your_textverified_api_key_here')
            if 'TEXTVERIFIED_EMAIL=' not in env_content:
                missing_vars.append('TEXTVERIFIED_EMAIL=your_textverified_email_here')
                
            with open(env_file, 'a') as f:
                f.write('\n# TextVerified API Configuration\n')
                for var in missing_vars:
                    f.write(f'{var}\n')
            
            fixes_applied.append("Added missing TextVerified API credential templates to .env")
        else:
            print("✅ TextVerified API credentials found in .env")
    else:
        issues_found.append(".env file not found")
        
        # Create .env file with template
        env_template = """# Namaskah SMS Environment Configuration

# Security
SECRET_KEY=your_secret_key_here_minimum_32_characters
JWT_SECRET_KEY=your_jwt_secret_key_here

# TextVerified API (Required for SMS verification)
TEXTVERIFIED_API_KEY=your_textverified_api_key_here
TEXTVERIFIED_EMAIL=your_textverified_email_here

# Paystack Payment (Required for wallet funding)
PAYSTACK_SECRET_KEY=your_paystack_secret_key_here

# Database
DATABASE_URL=sqlite:///./sms.db

# Email Configuration (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
FROM_EMAIL=noreply@namaskah.app

# Application
BASE_URL=http://localhost:8000
ENVIRONMENT=development

# Google OAuth (Optional)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
"""
        
        with open(env_file, 'w') as f:
            f.write(env_template)
        
        fixes_applied.append("Created .env file with configuration template")
    
    # Issue 2: Error handling in verification creation
    print("\n2. Checking verification creation error handling...")
    
    main_py_path = "/Users/machine/Project/GitHub/Namaskah. app/main.py"
    if os.path.exists(main_py_path):
        with open(main_py_path, 'r') as f:
            main_content = f.read()
        
        # Check if proper error handling exists
        if 'except Exception as e:' in main_content and 'TextVerified API error' in main_content:
            print("✅ Error handling found in verification creation")
        else:
            issues_found.append("Inadequate error handling in verification creation")
    
    # Issue 3: Check if services.json exists
    print("\n3. Checking services configuration...")
    
    services_file = "/Users/machine/Project/GitHub/Namaskah. app/services_categorized.json"
    if not os.path.exists(services_file):
        issues_found.append("Missing services_categorized.json file")
        
        # Create basic services file
        basic_services = {
            "categories": {
                "Social": ["whatsapp", "telegram", "discord", "instagram", "facebook", "twitter"],
                "Finance": ["paypal", "cashapp", "venmo"],
                "Other": ["google", "microsoft", "apple"]
            },
            "uncategorized": [],
            "tiers": {
                "popular": {
                    "name": "Popular",
                    "base_price": 0.75,
                    "services": ["whatsapp", "telegram", "discord", "google"],
                    "success_rate": 95
                },
                "standard": {
                    "name": "Standard", 
                    "base_price": 1.0,
                    "services": ["instagram", "facebook", "twitter"],
                    "success_rate": 90
                }
            }
        }
        
        with open(services_file, 'w') as f:
            json.dump(basic_services, f, indent=2)
        
        fixes_applied.append("Created basic services_categorized.json file")
    else:
        print("✅ Services configuration file found")
    
    return issues_found, fixes_applied

def create_verification_test_script():
    """Create a test script to verify the fix works"""
    
    test_script = '''#!/usr/bin/env python3
"""
Test script to verify verification creation works
"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

def test_verification_creation():
    """Test the verification creation endpoint"""
    
    base_url = "http://localhost:8000"
    
    # First, try to register/login to get a token
    print("🔐 Testing authentication...")
    
    # Test registration
    register_data = {
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    try:
        response = requests.post(f"{base_url}/auth/register", json=register_data)
        if response.status_code == 200:
            token = response.json().get("token")
            print("✅ Authentication successful")
        elif response.status_code == 400 and "already registered" in response.text:
            # Try login instead
            response = requests.post(f"{base_url}/auth/login", json=register_data)
            if response.status_code == 200:
                token = response.json().get("token")
                print("✅ Login successful")
            else:
                print(f"❌ Login failed: {response.text}")
                return False
        else:
            print(f"❌ Registration failed: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure the server is running on http://localhost:8000")
        return False
    
    # Test verification creation
    print("\\n📱 Testing verification creation...")
    
    verification_data = {
        "service_name": "telegram",
        "capability": "sms"
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(f"{base_url}/verify/create", json=verification_data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Verification creation successful!")
            print(f"   Verification ID: {result.get('id')}")
            print(f"   Phone Number: {result.get('phone_number')}")
            print(f"   Service: {result.get('service_name')}")
            print(f"   Cost: N{result.get('cost')}")
            return True
        else:
            print(f"❌ Verification creation failed: {response.text}")
            
            # Parse error details
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('detail', 'Unknown error')}")
            except:
                pass
            
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Namaskah SMS Verification Creation")
    print("=" * 50)
    
    success = test_verification_creation()
    
    if success:
        print("\\n🎉 All tests passed! Verification creation is working.")
    else:
        print("\\n❌ Tests failed. Check the error messages above.")
        print("\\nCommon issues:")
        print("1. Server not running (run: uvicorn main:app --reload)")
        print("2. Missing TextVerified API credentials in .env file")
        print("3. Invalid TextVerified API key or email")
        print("4. Network connectivity issues")
'''
    
    test_file_path = "/Users/machine/Project/GitHub/Namaskah. app/test_verification.py"
    with open(test_file_path, 'w') as f:
        f.write(test_script)
    
    # Make it executable
    os.chmod(test_file_path, 0o755)
    
    return test_file_path

def create_debug_verification_endpoint():
    """Create a debug version of the verification endpoint with better error handling"""
    
    debug_code = '''
# Enhanced verification creation with better error handling
@app.post("/verify/create/debug", tags=["Verification"], summary="Debug SMS/Voice Verification Creation")
def create_verification_debug(req: CreateVerificationRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Debug version of verification creation with detailed error reporting"""
    
    debug_info = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": user.id,
        "service_name": req.service_name,
        "capability": req.capability,
        "steps": []
    }
    
    try:
        # Step 1: Validate TextVerified configuration
        debug_info["steps"].append("Checking TextVerified configuration...")
        
        if not TEXTVERIFIED_API_KEY:
            raise HTTPException(
                status_code=503, 
                detail="TextVerified API key not configured. Please set TEXTVERIFIED_API_KEY in environment variables."
            )
        
        if not TEXTVERIFIED_EMAIL:
            raise HTTPException(
                status_code=503,
                detail="TextVerified email not configured. Please set TEXTVERIFIED_EMAIL in environment variables."
            )
        
        debug_info["steps"].append("✅ TextVerified configuration OK")
        
        # Step 2: Check user credits and subscription
        debug_info["steps"].append("Checking user credits and subscription...")
        
        subscription = db.query(Subscription).filter(
            Subscription.user_id == user.id,
            Subscription.status == "active"
        ).first()
        user_plan = subscription.plan if subscription else 'starter'
        
        # Get monthly verification count
        month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0)
        monthly_count = db.query(Verification).filter(
            Verification.user_id == user.id,
            Verification.created_at >= month_start
        ).count()
        
        # Calculate cost
        cost = get_service_price(req.service_name, user_plan, monthly_count)
        if req.capability == 'voice':
            cost += VOICE_PREMIUM
        
        debug_info["calculated_cost"] = cost
        debug_info["user_credits"] = user.credits
        debug_info["free_verifications"] = user.free_verifications
        
        # Check if user can afford
        plan_data = SUBSCRIPTION_PLANS[user_plan]
        free_limit = plan_data.get('free_verifications', 0)
        
        can_use_free = free_limit == -1 or (user.free_verifications > 0 and free_limit > 0)
        
        if can_use_free:
            debug_info["steps"].append("✅ Using free verification")
            cost = 0
        elif user.credits < cost:
            raise HTTPException(
                status_code=402, 
                detail=f"Insufficient credits. Need N{cost}, have N{user.credits}. Free verifications: {user.free_verifications}"
            )
        
        debug_info["steps"].append("✅ Credit check passed")
        
        # Step 3: Test TextVerified API connection
        debug_info["steps"].append("Testing TextVerified API connection...")
        
        try:
            # Test authentication
            token = tv_client.get_token()
            debug_info["steps"].append("✅ TextVerified authentication successful")
            debug_info["textverified_token"] = token[:20] + "..." if token else None
            
        except Exception as e:
            debug_info["steps"].append(f"❌ TextVerified authentication failed: {str(e)}")
            raise HTTPException(
                status_code=503,
                detail=f"TextVerified API authentication failed: {str(e)}. Please check your API credentials."
            )
        
        # Step 4: Create verification
        debug_info["steps"].append("Creating verification with TextVerified...")
        
        try:
            verification_id = tv_client.create_verification(
                req.service_name, 
                req.capability,
                area_code=req.area_code,
                carrier=req.carrier
            )
            
            if not verification_id:
                raise Exception("No verification ID returned from TextVerified")
            
            debug_info["textverified_verification_id"] = verification_id
            debug_info["steps"].append("✅ TextVerified verification created")
            
        except Exception as e:
            debug_info["steps"].append(f"❌ TextVerified verification creation failed: {str(e)}")
            raise HTTPException(
                status_code=503,
                detail=f"Failed to create verification with TextVerified: {str(e)}"
            )
        
        # Step 5: Get verification details
        debug_info["steps"].append("Getting verification details...")
        
        try:
            details = tv_client.get_verification(verification_id)
            phone_number = details.get("number")
            
            if not phone_number:
                raise Exception("No phone number returned from TextVerified")
            
            debug_info["phone_number"] = phone_number
            debug_info["steps"].append("✅ Phone number retrieved")
            
        except Exception as e:
            debug_info["steps"].append(f"❌ Failed to get verification details: {str(e)}")
            raise HTTPException(
                status_code=503,
                detail=f"Failed to get verification details: {str(e)}"
            )
        
        # Step 6: Save to database
        debug_info["steps"].append("Saving verification to database...")
        
        try:
            # Deduct credits if not free
            if cost > 0:
                user.credits -= cost
            else:
                user.free_verifications -= 1
            
            # Create verification record
            verification = Verification(
                id=verification_id,
                user_id=user.id,
                service_name=req.service_name,
                phone_number=phone_number,
                capability=req.capability,
                status="pending",
                cost=cost,
                requested_carrier=req.carrier,
                requested_area_code=req.area_code
            )
            
            db.add(verification)
            
            # Create transaction if cost > 0
            if cost > 0:
                tier = get_service_tier(req.service_name)
                db.add(Transaction(
                    id=f"txn_{datetime.now(timezone.utc).timestamp()}",
                    user_id=user.id,
                    amount=-cost,
                    type="debit",
                    description=f"{req.service_name} verification ({tier})"
                ))
            
            db.commit()
            debug_info["steps"].append("✅ Database save successful")
            
        except Exception as e:
            debug_info["steps"].append(f"❌ Database save failed: {str(e)}")
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save verification to database: {str(e)}"
            )
        
        # Success response
        debug_info["steps"].append("✅ Verification creation completed successfully")
        
        return {
            "success": True,
            "id": verification.id,
            "service_name": verification.service_name,
            "phone_number": verification.phone_number,
            "capability": verification.capability,
            "status": verification.status,
            "cost": cost,
            "remaining_credits": user.credits,
            "debug_info": debug_info
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Catch any unexpected errors
        debug_info["steps"].append(f"❌ Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during verification creation: {str(e)}",
            headers={"X-Debug-Info": json.dumps(debug_info)}
        )
'''
    
    return debug_code

def main():
    """Main function to run the verification fix"""
    
    print("🔧 Namaskah SMS - Verification Creation Fix")
    print("=" * 50)
    
    # Analyze issues
    issues, fixes = analyze_verification_issue()
    
    # Report findings
    print(f"\n📊 Analysis Results:")
    print(f"   Issues found: {len(issues)}")
    print(f"   Fixes applied: {len(fixes)}")
    
    if issues:
        print(f"\n❌ Issues Found:")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
    
    if fixes:
        print(f"\n✅ Fixes Applied:")
        for i, fix in enumerate(fixes, 1):
            print(f"   {i}. {fix}")
    
    # Create test script
    print(f"\n🧪 Creating test script...")
    test_file = create_verification_test_script()
    print(f"   Created: {test_file}")
    
    # Create debug endpoint code
    print(f"\n🐛 Creating debug endpoint...")
    debug_code = create_debug_verification_endpoint()
    
    debug_file = "/Users/machine/Project/GitHub/Namaskah. app/debug_verification_endpoint.py"
    with open(debug_file, 'w') as f:
        f.write(debug_code)
    print(f"   Created: {debug_file}")
    
    # Provide next steps
    print(f"\n🚀 Next Steps:")
    print(f"   1. Update your .env file with valid TextVerified API credentials")
    print(f"   2. Restart your server: uvicorn main:app --reload")
    print(f"   3. Run the test: python test_verification.py")
    print(f"   4. If issues persist, add the debug endpoint to main.py")
    print(f"   5. Test with: POST /verify/create/debug")
    
    print(f"\n📝 Configuration Required:")
    print(f"   - TEXTVERIFIED_API_KEY: Get from https://textverified.com")
    print(f"   - TEXTVERIFIED_EMAIL: Your TextVerified account email")
    print(f"   - Ensure you have credits in your TextVerified account")
    
    return len(issues) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)