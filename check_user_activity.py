#!/usr/bin/env python3
"""Check user activities and transactions"""

import sqlite3
from datetime import datetime

def check_user(email=None, user_id=None):
    """Check user details, balance, and transactions"""
    conn = sqlite3.connect('sms.db')
    cursor = conn.cursor()
    
    # Find user
    if email:
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    elif user_id:
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    else:
        print("❌ Provide email or user_id")
        return
    
    user = cursor.fetchone()
    if not user:
        print(f"❌ User not found: {email or user_id}")
        return
    
    # Display user info
    print("\n" + "="*60)
    print("👤 USER DETAILS")
    print("="*60)
    print(f"ID: {user[0]}")
    print(f"Email: {user[1]}")
    print(f"Credits: N{user[3]:.2f}")
    print(f"Free Verifications: {user[4]}")
    print(f"Is Admin: {user[5]}")
    print(f"Email Verified: {user[6]}")
    print(f"Referral Code: {user[10]}")
    print(f"Created: {user[13]}")
    
    user_id = user[0]
    
    # Get transactions
    print("\n" + "="*60)
    print("💰 TRANSACTIONS")
    print("="*60)
    cursor.execute("""
        SELECT id, amount, type, description, created_at 
        FROM transactions 
        WHERE user_id = ? 
        ORDER BY created_at DESC
    """, (user_id,))
    
    transactions = cursor.fetchall()
    if transactions:
        for txn in transactions:
            symbol = "+" if txn[2] == "credit" else "-"
            print(f"{txn[4]} | {symbol}N{abs(txn[1]):.2f} | {txn[3]}")
    else:
        print("No transactions found")
    
    # Get verifications
    print("\n" + "="*60)
    print("📱 VERIFICATIONS")
    print("="*60)
    cursor.execute("""
        SELECT id, service_name, status, cost, created_at 
        FROM verifications 
        WHERE user_id = ? 
        ORDER BY created_at DESC 
        LIMIT 10
    """, (user_id,))
    
    verifications = cursor.fetchall()
    if verifications:
        for ver in verifications:
            print(f"{ver[4]} | {ver[1]} | {ver[2]} | N{ver[3]:.2f}")
    else:
        print("No verifications found")
    
    # Get rentals
    print("\n" + "="*60)
    print("🏠 RENTALS")
    print("="*60)
    cursor.execute("""
        SELECT id, service_name, status, cost, started_at, expires_at 
        FROM number_rentals 
        WHERE user_id = ? 
        ORDER BY started_at DESC
    """, (user_id,))
    
    rentals = cursor.fetchall()
    if rentals:
        for rental in rentals:
            print(f"{rental[4]} | {rental[1]} | {rental[2]} | N{rental[3]:.2f}")
    else:
        print("No rentals found")
    
    conn.close()
    print("\n" + "="*60 + "\n")


def check_pending_payments():
    """Check for pending Paystack payments"""
    conn = sqlite3.connect('sms.db')
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("💳 CHECKING PENDING PAYMENTS")
    print("="*60)
    
    # Look for payment-related transactions
    cursor.execute("""
        SELECT user_id, description, created_at 
        FROM transactions 
        WHERE description LIKE '%Paystack%' 
        ORDER BY created_at DESC 
        LIMIT 20
    """)
    
    payments = cursor.fetchall()
    if payments:
        print("\nRecent Paystack transactions:")
        for pay in payments:
            print(f"{pay[2]} | User: {pay[0]} | {pay[1]}")
    else:
        print("No Paystack transactions found")
    
    conn.close()
    print("\n" + "="*60 + "\n")


def list_all_users():
    """List all users with balances"""
    conn = sqlite3.connect('sms.db')
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("👥 ALL USERS")
    print("="*60)
    
    cursor.execute("""
        SELECT email, credits, free_verifications, created_at 
        FROM users 
        ORDER BY created_at DESC
    """)
    
    users = cursor.fetchall()
    for user in users:
        print(f"{user[0]} | N{user[1]:.2f} | Free: {user[2]} | {user[3]}")
    
    print(f"\nTotal users: {len(users)}")
    conn.close()
    print("\n" + "="*60 + "\n")


def add_credits(email, amount):
    """Manually add credits to user"""
    conn = sqlite3.connect('sms.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, email, credits FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    
    if not user:
        print(f"❌ User not found: {email}")
        return
    
    user_id = user[0]
    old_balance = user[2]
    new_balance = old_balance + amount
    
    # Update credits
    cursor.execute("UPDATE users SET credits = ? WHERE id = ?", (new_balance, user_id))
    
    # Create transaction
    txn_id = f"txn_{datetime.now().timestamp()}"
    cursor.execute("""
        INSERT INTO transactions (id, user_id, amount, type, description, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (txn_id, user_id, amount, "credit", f"Manual credit adjustment", datetime.now()))
    
    conn.commit()
    conn.close()
    
    print(f"✅ Added N{amount:.2f} to {email}")
    print(f"   Old balance: N{old_balance:.2f}")
    print(f"   New balance: N{new_balance:.2f}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("\n📊 User Activity Checker\n")
        print("Usage:")
        print("  python check_user_activity.py <email>           - Check user by email")
        print("  python check_user_activity.py list              - List all users")
        print("  python check_user_activity.py payments          - Check pending payments")
        print("  python check_user_activity.py add <email> <amount> - Add credits")
        print("\nExamples:")
        print("  python check_user_activity.py user@example.com")
        print("  python check_user_activity.py list")
        print("  python check_user_activity.py payments")
        print("  python check_user_activity.py add user@example.com 10.50")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "list":
        list_all_users()
    elif command == "payments":
        check_pending_payments()
    elif command == "add":
        if len(sys.argv) < 4:
            print("❌ Usage: python check_user_activity.py add <email> <amount>")
            sys.exit(1)
        email = sys.argv[2]
        amount = float(sys.argv[3])
        add_credits(email, amount)
    else:
        # Assume it's an email
        check_user(email=command)
