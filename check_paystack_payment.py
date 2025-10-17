#!/usr/bin/env python3
"""Check Paystack payment for specific user"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")

def check_user_payments(email):
    """Check all payments for a user email on Paystack"""
    if not PAYSTACK_SECRET_KEY:
        print("❌ PAYSTACK_SECRET_KEY not configured")
        return
    
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
    
    # Search transactions by email
    url = f"https://api.paystack.co/transaction?customer={email}"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        if not data.get('status'):
            print(f"❌ API Error: {data.get('message')}")
            return
        
        transactions = data.get('data', [])
        
        print(f"\n{'='*80}")
        print(f"💳 PAYSTACK TRANSACTIONS FOR: {email}")
        print(f"{'='*80}\n")
        
        if not transactions:
            print("No transactions found")
            return
        
        for txn in transactions:
            print(f"Reference: {txn.get('reference')}")
            print(f"Amount: ₦{txn.get('amount', 0)/100:.2f}")
            print(f"Status: {txn.get('status')}")
            print(f"Date: {txn.get('created_at')}")
            print(f"Channel: {txn.get('channel')}")
            if txn.get('metadata'):
                print(f"Metadata: {txn.get('metadata')}")
            print(f"{'-'*80}\n")
        
        print(f"Total transactions: {len(transactions)}\n")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("\nUsage: python check_paystack_payment.py <email>")
        print("Example: python check_paystack_payment.py worldkingctn@gmail.com")
        sys.exit(1)
    
    email = sys.argv[1]
    check_user_payments(email)
