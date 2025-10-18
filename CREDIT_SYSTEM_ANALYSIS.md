# CREDIT SYSTEM ANALYSIS

## Overview
The platform uses **Namaskah Coins (N)** as internal currency where **1N = $2 USD**.

---

## 💰 HOW USERS GET CREDITED

### 1. **Payment via Paystack (Primary Method)**
**Location**: `/wallet/paystack/webhook` endpoint (line ~2502)

**Flow**:
1. User initiates payment via Paystack
2. Pays in Nigerian Naira (NGN)
3. System converts: NGN → USD → Namaskah Coins
4. Formula: `namaskah_amount = usd_amount * 0.5` (since 1N = $2)
5. Credits added: `user.credits += namaskah_amount`
6. Transaction record created with type "credit"
7. Email confirmation sent

**Example**:
- User pays ₦1,478 NGN (≈ $1 USD)
- Receives: 0.5N credits
- Can purchase: 0 verifications (needs 1N minimum)

**Minimum Funding**: N2.50 ($5 USD) recommended

---

### 2. **Manual Payment Verification**
**Location**: `/wallet/paystack/verify/{reference}` endpoint (line ~2595)

**Flow**:
1. Admin or user manually verifies payment
2. System checks Paystack API for payment status
3. If successful, converts and credits account
4. Same conversion formula as webhook

**Use Case**: Backup when webhook fails

---

### 3. **Admin Manual Credit Addition**
**Location**: `/admin/credits/add` endpoint (line ~1909)

**Flow**:
1. Admin selects user in admin panel
2. Enters amount in Namaskah Coins (N)
3. Credits added directly: `user.credits += req.amount`
4. Transaction created with description "Admin added credits"

**Use Case**: 
- Customer support refunds
- Promotional credits
- Testing

---

### 4. **New User Bonus**
**Location**: User registration (line ~1117)

**Flow**:
1. New user registers
2. Receives: `free_verifications = 1.0`
3. First verification is free (no credit deduction)

**Note**: This is NOT added to credits, it's a separate counter

---

### 5. **Referral Bonus**
**Location**: User registration with referral code (line ~1117)

**Flow**:
1. New user registers with referral code
2. New user gets: `free_verifications += 1.0` (2 total)
3. Referrer gets: 1 free verification AFTER referred user funds N2.50+

**Status**: Partially implemented (referrer reward pending funding trigger)

---

### 6. **Verification Refund**
**Location**: `/verify/{verification_id}` DELETE endpoint (line ~1673)

**Flow**:
1. User cancels active verification
2. Full refund: `user.credits += verification.cost`
3. Transaction created with type "credit"
4. Description: "Refund for cancelled {service} verification"

**Conditions**: Only if verification not completed

---

### 7. **Rental Early Release Refund**
**Location**: `/rentals/{rental_id}/release` endpoint (line ~3240)

**Flow**:
1. User releases rental before expiry
2. Calculates unused time
3. 50% refund: `refund = (unused_hours * hourly_rate) * 0.5`
4. Credits added: `user.credits += refund`
5. Transaction created

**Example**:
- Rented for 7 days (N5)
- Used 3 days
- Refund: 4 days * (N5/7) * 0.5 = N1.43

---

## 💸 HOW CREDITS ARE DEDUCTED

### 1. **SMS/Voice Verification**
**Location**: `/verify/create` endpoint (line ~1476)

**Deduction**:
```python
if user.free_verifications >= 1:
    user.free_verifications -= 1
    cost = 0  # Free
elif user.credits < cost:
    raise HTTPException(402, "Insufficient credits")
else:
    user.credits -= cost
```

**Pricing**:
- Popular services (WhatsApp, Instagram, etc.): N1 ($2)
- General/unlisted services: N1.25 ($2.50)
- Voice verification: SMS price + N0.25

**Discounts**:
- Developer plan (N25+ funded): 20% off
- Enterprise plan (N100+ funded): 35% off

---

### 2. **Subscription Plans**
**Location**: `/subscription/subscribe` endpoint (line ~2184)

**Deduction**:
```python
user.credits -= plan['price']
```

**Plans**:
- **Starter**: N12.5 ($25) - 7 days, no discount
- **Pro**: N25 ($50) - 30 days, 20% discount on verifications
- **Turbo**: N75 ($150) - Lifetime, 35% discount on verifications

---

### 3. **Number Rentals**
**Location**: `/rentals/create` endpoint (line ~3059)

**Deduction**:
```python
user.credits -= cost
```

**Pricing**:
- Service-specific: N5 (7d) to N50 (365d)
- General use: N6 (7d) to N80 (365d)
- Manual mode: 30% discount

---

### 4. **Rental Extension**
**Location**: `/rentals/{rental_id}/extend` endpoint (line ~3195)

**Deduction**:
```python
user.credits -= cost
```

**Calculation**: Proportional to additional hours requested

---

## 📊 TRANSACTION TRACKING

Every credit operation creates a `Transaction` record:

```python
Transaction(
    id=f"txn_{timestamp}",
    user_id=user.id,
    amount=amount,  # Positive for credit, negative for debit
    type="credit" or "debit",
    description="Reason for transaction",
    created_at=datetime.now(timezone.utc)
)
```

**Transaction Types**:
- **credit**: Payment received, refund, admin addition
- **debit**: Verification purchase, subscription, rental

---

## 🔍 CREDIT BALANCE CHECKS

### Low Balance Alert
**Location**: After verification purchase (line ~1482)

**Trigger**: When `user.credits <= threshold` (default 1.0N)

**Action**: Email notification sent to user

---

### Insufficient Credits
**Locations**: Multiple endpoints

**Check**:
```python
if user.credits < cost:
    raise HTTPException(402, f"Insufficient credits. Need N{cost}, have N{user.credits}")
```

**User sees**: "Insufficient credits" error with exact amounts

---

## 💡 CREDIT SYSTEM ISSUES IDENTIFIED

### ✅ Working Correctly
1. Paystack webhook crediting
2. Admin manual credit addition
3. Verification refunds
4. Rental refunds (50%)
5. Transaction logging
6. Balance checks

### ⚠️ Potential Issues

1. **Referral Reward Not Triggered**
   - Code exists but referrer doesn't get free verification when referred user funds
   - Line ~1117: Comment says "Transactions will be created when referred user funds wallet"
   - **Missing**: Webhook handler doesn't check for pending referral rewards

2. **No Minimum Funding Enforcement**
   - README says minimum N2.50 ($5 USD)
   - Code allows any amount
   - Users could fund N0.50 and not afford any service

3. **Free Verifications Not Tracked in Transactions**
   - When `free_verifications` is used, no transaction record created
   - Makes analytics incomplete

4. **Subscription Discount Not Applied Automatically**
   - User must have active subscription
   - Discount calculated at verification time
   - No automatic tier detection based on total funded

5. **Currency Conversion Rate Cached**
   - USD to NGN rate cached for 1 hour
   - Could cause discrepancies during rate fluctuations
   - Line ~120: `exchange_rate_cache`

---

## 📈 RECOMMENDATIONS

### High Priority
1. **Implement Referral Reward Trigger**
   - Add check in Paystack webhook
   - When user funds N2.50+, credit referrer with 1 free verification

2. **Enforce Minimum Funding**
   - Add validation in `/wallet/paystack/initialize`
   - Reject payments < N2.50

3. **Track Free Verifications in Transactions**
   - Create transaction with amount=0, type="free"
   - Better analytics and audit trail

### Medium Priority
4. **Auto-Upgrade Subscription Tiers**
   - Check total funded amount
   - Auto-apply Developer (N25+) or Enterprise (N100+) discounts
   - No need for manual subscription purchase

5. **Add Credit Expiry**
   - Implement credit expiration (e.g., 1 year)
   - Send warnings before expiry

6. **Add Credit Transfer**
   - Allow users to transfer credits to other users
   - Useful for teams/resellers

### Low Priority
7. **Multi-Currency Support**
   - Accept USD, EUR directly
   - Reduce conversion complexity

8. **Credit Packages with Bonus**
   - Fund N50, get N55
   - Encourage larger deposits

---

## 🎯 SUMMARY

**Credit Flow**:
```
Payment (NGN) → Paystack → Webhook → Convert to USD → Convert to N → user.credits += amount
```

**Debit Flow**:
```
User Action → Check balance → Deduct credits → Create transaction → Provide service
```

**Current Status**: ✅ **Functional but needs refinements**
- Core crediting works via Paystack
- Refunds work correctly
- Admin can manually add credits
- Referral system incomplete
- No minimum funding enforcement
