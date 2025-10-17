#!/usr/bin/env python3
"""
Test script to verify all subscription/pricing modals and features
"""

import re
from pathlib import Path

def test_modals_exist():
    """Check if all required modals exist in index.html"""
    index_path = Path("templates/index.html")
    content = index_path.read_text()
    
    required_modals = {
        "pricing-offer-modal": "Pricing tier offer modal (Developer/Enterprise plans)",
        "fund-wallet-modal": "Fund wallet modal",
        "rental-modal": "Number rental modal",
        "unlisted-modal": "Unlisted service modal",
        "forgot-password-modal": "Password reset modal",
        "support-modal": "Support contact modal"
    }
    
    print("=" * 70)
    print("MODAL EXISTENCE CHECK")
    print("=" * 70)
    
    missing = []
    for modal_id, description in required_modals.items():
        if f'id="{modal_id}"' in content:
            print(f"✅ {modal_id}: {description}")
        else:
            print(f"❌ MISSING: {modal_id}: {description}")
            missing.append(modal_id)
    
    return len(missing) == 0, missing

def test_pricing_tiers():
    """Check if pricing tier information is present"""
    index_path = Path("templates/index.html")
    content = index_path.read_text()
    
    print("\n" + "=" * 70)
    print("PRICING TIER FEATURES")
    print("=" * 70)
    
    features = {
        "Developer Plan (20% discount)": ["Developer Plan", "20%", "N0.40", "N50"],
        "Enterprise Plan (30% discount)": ["Enterprise Plan", "30%", "N0.35", "N200"],
        "Fund buttons": ["fundWalletWithPlan(50)", "fundWalletWithPlan(200)"]
    }
    
    all_present = True
    for feature_name, keywords in features.items():
        found = all(keyword in content for keyword in keywords)
        if found:
            print(f"✅ {feature_name}: All elements present")
        else:
            print(f"❌ {feature_name}: Missing elements")
            missing_keywords = [k for k in keywords if k not in content]
            print(f"   Missing: {missing_keywords}")
            all_present = False
    
    return all_present

def test_rental_features():
    """Check if rental modal has all required features"""
    index_path = Path("templates/index.html")
    content = index_path.read_text()
    
    print("\n" + "=" * 70)
    print("RENTAL MODAL FEATURES")
    print("=" * 70)
    
    rental_features = {
        "Service selection dropdown": 'id="rental-service"',
        "Custom service input": 'id="custom-rental-service"',
        "Mode selection (Always/Manual)": ['mode-always', 'mode-manual'],
        "Duration options": ['duration-7', 'duration-14', 'duration-30', 'duration-60', 'duration-90'],
        "Price display": 'id="rental-total"',
        "Create rental button": 'onclick="createRentalNumber()"'
    }
    
    all_present = True
    for feature_name, identifiers in rental_features.items():
        if isinstance(identifiers, list):
            found = all(identifier in content for identifier in identifiers)
            if found:
                print(f"✅ {feature_name}: All options present")
            else:
                missing = [i for i in identifiers if i not in content]
                print(f"❌ {feature_name}: Missing {missing}")
                all_present = False
        else:
            if identifiers in content:
                print(f"✅ {feature_name}: Present")
            else:
                print(f"❌ {feature_name}: Missing")
                all_present = False
    
    return all_present

def test_payment_methods():
    """Check if payment method selection is present"""
    index_path = Path("templates/index.html")
    content = index_path.read_text()
    
    print("\n" + "=" * 70)
    print("PAYMENT METHOD FEATURES")
    print("=" * 70)
    
    payment_features = {
        "Payment methods container": 'id="payment-methods"',
        "Paystack option": "selectPayment('paystack')",
        "Amount input": 'id="fund-amount"',
        "Minimum amount validation": 'min="5"',
        "Payment method display": ["Bank Transfer", "Card", "USSD"]
    }
    
    all_present = True
    for feature_name, identifiers in payment_features.items():
        if isinstance(identifiers, list):
            found = all(identifier in content for identifier in identifiers)
            if found:
                print(f"✅ {feature_name}: All methods present")
            else:
                missing = [i for i in identifiers if i not in content]
                print(f"⚠️  {feature_name}: Some missing {missing}")
        else:
            if identifiers in content:
                print(f"✅ {feature_name}: Present")
            else:
                print(f"❌ {feature_name}: Missing")
                all_present = False
    
    return all_present

def test_verification_capabilities():
    """Check if SMS and Voice verification options exist"""
    index_path = Path("templates/index.html")
    content = index_path.read_text()
    
    print("\n" + "=" * 70)
    print("VERIFICATION CAPABILITY FEATURES")
    print("=" * 70)
    
    capabilities = {
        "Capability selection container": 'id="capability-selection"',
        "SMS option": ['capability-sms-label', 'value="sms"'],
        "Voice option": ['capability-voice-label', 'value="voice"'],
        "Price display for SMS": "N0.50",
        "Price display for Voice": "N0.75"
    }
    
    all_present = True
    for feature_name, identifiers in capabilities.items():
        if isinstance(identifiers, list):
            found = all(identifier in content for identifier in identifiers)
            if found:
                print(f"✅ {feature_name}: Present")
            else:
                print(f"❌ {feature_name}: Missing")
                all_present = False
        else:
            if identifiers in content:
                print(f"✅ {feature_name}: Present")
            else:
                print(f"❌ {feature_name}: Missing")
                all_present = False
    
    return all_present

def test_javascript_functions():
    """Check if all required JavaScript functions exist"""
    js_files = {
        "wallet.js": ["showFundWallet", "closeFundWallet", "showPaymentMethods", 
                      "selectPayment", "showPricingOffer", "closePricingOffer", 
                      "fundWalletWithPlan"],
        "verification.js": ["createVerification", "checkMessages", "cancelVerification",
                           "checkVoiceCall", "retryVerification"],
        "rentals.js": ["showRentalModal", "closeRentalModal", "createRentalNumber",
                      "updateRentalPrice"]
    }
    
    print("\n" + "=" * 70)
    print("JAVASCRIPT FUNCTION CHECK")
    print("=" * 70)
    
    all_present = True
    for js_file, functions in js_files.items():
        js_path = Path(f"static/js/{js_file}")
        if not js_path.exists():
            print(f"❌ {js_file}: File not found")
            all_present = False
            continue
        
        content = js_path.read_text()
        print(f"\n{js_file}:")
        for func in functions:
            # Check for function definition (async or regular)
            if f"function {func}" in content or f"async function {func}" in content or f"{func} =" in content:
                print(f"  ✅ {func}")
            else:
                print(f"  ❌ {func} - NOT FOUND")
                all_present = False
    
    return all_present

def test_modal_open_close_functions():
    """Check if modal open/close functions are properly defined"""
    index_path = Path("templates/index.html")
    content = index_path.read_text()
    
    print("\n" + "=" * 70)
    print("MODAL OPEN/CLOSE FUNCTIONS")
    print("=" * 70)
    
    modal_functions = {
        "Pricing Offer": ["showPricingOffer", "closePricingOffer"],
        "Fund Wallet": ["showFundWallet", "closeFundWallet"],
        "Rental": ["showRentalModal", "closeRentalModal"],
        "Unlisted Service": ["showUnlistedModal", "closeUnlistedModal"],
        "Forgot Password": ["showForgotPassword", "closeForgotPassword"],
        "Support": ["showSupportModal", "closeSupportModal"]
    }
    
    all_present = True
    for modal_name, functions in modal_functions.items():
        open_func, close_func = functions
        open_exists = f"onclick=\"{open_func}()" in content or f"function {open_func}" in content
        close_exists = f"onclick=\"{close_func}()" in content or f"function {close_func}" in content
        
        if open_exists and close_exists:
            print(f"✅ {modal_name}: Open and Close functions present")
        else:
            print(f"❌ {modal_name}: Missing functions")
            if not open_exists:
                print(f"   Missing: {open_func}")
            if not close_exists:
                print(f"   Missing: {close_func}")
            all_present = False
    
    return all_present

def test_rental_pricing_structure():
    """Check if rental pricing structure matches README"""
    index_path = Path("templates/index.html")
    content = index_path.read_text()
    
    print("\n" + "=" * 70)
    print("RENTAL PRICING STRUCTURE")
    print("=" * 70)
    
    # Check for duration options
    durations = ["7 days", "14 days", "30 days", "60 days", "90 days"]
    modes = ["Always Ready", "Manual"]
    
    all_present = True
    
    print("\nDuration Options:")
    for duration in durations:
        if duration in content:
            print(f"  ✅ {duration}")
        else:
            print(f"  ❌ {duration} - NOT FOUND")
            all_present = False
    
    print("\nRental Modes:")
    for mode in modes:
        if mode in content:
            print(f"  ✅ {mode}")
        else:
            print(f"  ❌ {mode} - NOT FOUND")
            all_present = False
    
    # Check for 30% discount mention
    if "30%" in content and "Manual" in content:
        print("\n  ✅ 30% discount for Manual mode mentioned")
    else:
        print("\n  ❌ 30% discount for Manual mode NOT mentioned")
        all_present = False
    
    return all_present

def main():
    print("\n" + "=" * 70)
    print("SUBSCRIPTION FLOW & MODAL TESTING")
    print("=" * 70)
    
    results = {
        "Modals Exist": test_modals_exist(),
        "Pricing Tiers": test_pricing_tiers(),
        "Rental Features": test_rental_features(),
        "Payment Methods": test_payment_methods(),
        "Verification Capabilities": test_verification_capabilities(),
        "JavaScript Functions": test_javascript_functions(),
        "Modal Open/Close": test_modal_open_close_functions(),
        "Rental Pricing": test_rental_pricing_structure()
    }
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    passed = 0
    failed = 0
    
    for test_name, result in results.items():
        if isinstance(result, tuple):
            result, missing = result
        
        if result:
            print(f"✅ {test_name}: PASSED")
            passed += 1
        else:
            print(f"❌ {test_name}: FAILED")
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"Total: {passed} passed, {failed} failed")
    print("=" * 70)
    
    if failed == 0:
        print("\n🎉 All subscription flow features are properly implemented!")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Review the issues above.")

if __name__ == "__main__":
    main()
