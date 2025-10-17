# 👥 User Activity & Payment Troubleshooting Guide

## 🚀 Quick Commands

### Check Specific User
```bash
python check_user_activity.py user@example.com
```

### List All Users
```bash
python check_user_activity.py list
```

### Check Pending Payments
```bash
python check_user_activity.py payments
```

### Manually Add Credits
```bash
python check_user_activity.py add user@example.com 10.50
```

---

## 🔍 Investigating Payment Issues

### Step 1: Check User Details
```bash
python check_user_activity.py user@example.com
```

**Output shows**:
- Current balance
- Free verifications
- All transactions
- Recent verifications
- Active rentals

### Step 2: Check Paystack Transactions
```bash
python check_user_activity.py payments
```

**Look for**:
- Payment reference
- Amount paid
- Whether credit transaction exists

### Step 3: Verify on Paystack Dashboard
1. Go to: https://dashboard.paystack.com/transactions
2. Search for user email or reference
3. Check payment status (success/failed)
4. Note the amount and reference

### Step 4: Manual Credit (If Needed)
```bash
# Add credits manually
python check_user_activity.py add user@example.com 5.00
```

---

## 🐛 Common Payment Issues

### Issue 1: Payment Successful but No Credits

**Cause**: Webhook not received or failed

**Solution**:
```bash
# 1. Check user
python check_user_activity.py user@example.com

# 2. Verify payment on Paystack dashboard

# 3. Manually add credits
python check_user_activity.py add user@example.com 5.00
```

### Issue 2: Duplicate Payment

**Cause**: User paid twice

**Solution**:
```bash
# Check transactions
python check_user_activity.py user@example.com

# Look for duplicate Paystack references
# Refund one payment via Paystack dashboard
```

### Issue 3: Wrong Amount Credited

**Cause**: Currency conversion issue

**Solution**:
```bash
# Check current balance
python check_user_activity.py user@example.com

# Calculate correct amount (1 USD = 0.5N)
# Adjust credits
python check_user_activity.py add user@example.com 2.50
```

---

## 📊 Admin Panel Alternative

### Via Web Interface
1. Go to: https://namaskah.onrender.com/admin
2. Login: admin@namaskah.app / Admin@2024!
3. Search for user email
4. View transactions and balance
5. Add credits manually

---

## 🔧 Direct Database Access

### Using SQLite CLI
```bash
# Connect to database
sqlite3 sms.db

# Check user
SELECT * FROM users WHERE email = 'user@example.com';

# Check transactions
SELECT * FROM transactions WHERE user_id = 'user_xxx' ORDER BY created_at DESC;

# Add credits manually
UPDATE users SET credits = credits + 5.0 WHERE email = 'user@example.com';

# Create transaction record
INSERT INTO transactions (id, user_id, amount, type, description, created_at)
VALUES ('txn_manual_123', 'user_xxx', 5.0, 'credit', 'Manual adjustment', datetime('now'));
```

---

## 📝 Payment Flow Debugging

### Normal Flow
```
1. User clicks "Fund Wallet"
2. Paystack payment page opens
3. User completes payment
4. Paystack sends webhook to /wallet/paystack/webhook
5. Webhook verified and processed
6. Credits added to user account
7. Transaction created
8. Confirmation email sent
```

### Check Each Step
```bash
# 1. Check Render logs
# Go to: https://dashboard.render.com → Logs
# Search for: "Paystack webhook" or "Payment processed"

# 2. Check user transactions
python check_user_activity.py user@example.com

# 3. Check Paystack dashboard
# Verify payment status

# 4. Manual fix if needed
python check_user_activity.py add user@example.com 5.00
```

---

## 🚨 Emergency Credit Addition

### For Production (Render)
```bash
# SSH into Render (if available) or use web shell
python check_user_activity.py add user@example.com 10.00
```

### For Local Development
```bash
# Run script locally
python check_user_activity.py add user@example.com 10.00
```

### Via Admin Panel
1. Login to admin panel
2. Search user
3. Click "Add Credits"
4. Enter amount
5. Submit

---

## 📈 Monitoring Payments

### Check Recent Payments
```bash
python check_user_activity.py payments
```

### Check All Users
```bash
python check_user_activity.py list
```

### Export Data
```bash
# Via admin panel
# Click "Export Users" or "Export Transactions"
# Download CSV file
```

---

## ✅ Verification Checklist

When user reports payment issue:

- [ ] Get user email
- [ ] Check user balance: `python check_user_activity.py user@example.com`
- [ ] Check Paystack dashboard for payment
- [ ] Verify payment reference matches
- [ ] Check Render logs for webhook
- [ ] If payment successful but no credits, add manually
- [ ] Notify user of resolution
- [ ] Document issue for future reference

---

## 🔐 Security Notes

- Only admins should run these scripts
- Never share database access
- Log all manual credit additions
- Verify payment on Paystack before adding credits
- Keep audit trail of adjustments

---

## 📞 Support Workflow

### User Reports: "I paid but didn't get credits"

**Response Template**:
```
Thank you for contacting us. I'm investigating your payment.

Please provide:
1. Email address used for registration
2. Payment reference (from Paystack email)
3. Amount paid
4. Date/time of payment

I'll check our records and resolve this within 1 hour.
```

**Investigation**:
```bash
# 1. Check user
python check_user_activity.py user@example.com

# 2. Check payments
python check_user_activity.py payments

# 3. Verify on Paystack

# 4. Add credits if confirmed
python check_user_activity.py add user@example.com 5.00

# 5. Notify user
```

---

## 🎯 Quick Reference

| Task | Command |
|------|---------|
| Check user | `python check_user_activity.py user@example.com` |
| List users | `python check_user_activity.py list` |
| Check payments | `python check_user_activity.py payments` |
| Add credits | `python check_user_activity.py add user@example.com 10` |
| Admin panel | https://namaskah.onrender.com/admin |
| Paystack dashboard | https://dashboard.paystack.com |

---

**Created**: 2024
**Status**: Ready for use
