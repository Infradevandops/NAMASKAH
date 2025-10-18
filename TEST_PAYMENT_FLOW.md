# Payment Flow Test Results

## Test Objective
Verify if payment crediting is automatic or requires manual admin intervention.

## Test Setup
1. **Environment**: Production/Staging
2. **Payment Method**: Paystack
3. **Test Amount**: N10 ($5 USD minimum)
4. **User Account**: Test user account

## Payment Flow Steps

### Step 1: Initialize Payment
```
POST /wallet/fund
Body: {
  "amount": 5.00,
  "payment_method": "paystack"
}
```

**Expected Response:**
- Payment URL generated
- Reference ID created
- Status: "pending"

### Step 2: Complete Payment
- User redirected to Paystack checkout
- Payment completed successfully
- Paystack sends webhook to `/wallet/paystack/webhook`

### Step 3: Webhook Processing
**Automatic Process:**
1. Webhook received from Paystack
2. Payment reference verified
3. Amount converted (USD → N)
4. Credits added to user wallet
5. Transaction recorded
6. Email notification sent

### Step 4: Verification
- Check user wallet balance
- Verify transaction history
- Confirm email received

## Test Results

### ✅ Automatic Crediting (Expected)
- [ ] Webhook received successfully
- [ ] Payment verified automatically
- [ ] Credits added to wallet instantly
- [ ] Transaction recorded in database
- [ ] Email notification sent
- [ ] No admin intervention required

### ❌ Manual Crediting (If automatic fails)
- [ ] Webhook not received
- [ ] Payment stuck in "pending"
- [ ] Admin must manually credit via dashboard
- [ ] Admin endpoint: POST /admin/credit/{user_id}

## Current Implementation

### Webhook Endpoint: `/wallet/paystack/webhook`
```python
@app.post("/wallet/paystack/webhook")
async def paystack_webhook(request: Request):
    # Verify webhook signature
    # Extract payment data
    # Find user by reference
    # Add credits to wallet
    # Update transaction status
    # Send email notification
    return {"status": "success"}
```

### Admin Manual Credit: `/admin/credit/{user_id}`
```python
@app.post("/admin/credit/{user_id}")
async def admin_credit_user(user_id: str, amount: float):
    # Admin authentication required
    # Add credits to user wallet
    # Create transaction record
    # Send notification
    return {"message": "Credits added"}
```

## Expected Behavior

### Automatic Crediting (Primary Flow)
1. **Payment Completed** → Paystack webhook triggered
2. **Webhook Received** → Server validates signature
3. **Credits Added** → Wallet updated automatically
4. **User Notified** → Email sent instantly
5. **Time**: < 5 seconds

### Manual Crediting (Fallback)
1. **Payment Completed** → Webhook fails/delayed
2. **Admin Notified** → Payment tracking dashboard
3. **Admin Reviews** → Verifies payment on Paystack
4. **Manual Credit** → Admin adds credits via dashboard
5. **Time**: Minutes to hours (depends on admin availability)

## Webhook Configuration

### Paystack Dashboard Settings
- **Webhook URL**: `https://namaskah.app/wallet/paystack/webhook`
- **Events**: `charge.success`, `transfer.success`
- **Secret Key**: Stored in environment variables

### Webhook Verification
```python
import hmac
import hashlib

def verify_webhook(payload, signature, secret):
    computed = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha512
    ).hexdigest()
    return computed == signature
```

## Common Issues & Solutions

### Issue 1: Webhook Not Received
**Cause**: Firewall blocking, incorrect URL, SSL issues
**Solution**: 
- Verify webhook URL in Paystack dashboard
- Check server logs for incoming requests
- Ensure HTTPS is properly configured

### Issue 2: Duplicate Credits
**Cause**: Webhook retries, race conditions
**Solution**:
- Use idempotency keys (reference IDs)
- Check if transaction already processed
- Database constraints on reference field

### Issue 3: Amount Mismatch
**Cause**: Currency conversion errors
**Solution**:
- Verify exchange rate (1N = $2 USD)
- Round to 2 decimal places
- Log all conversions for audit

## Testing Checklist

### Pre-Test
- [ ] Paystack test keys configured
- [ ] Webhook URL accessible
- [ ] Database backup created
- [ ] Test user account created

### During Test
- [ ] Payment initiated successfully
- [ ] Redirected to Paystack checkout
- [ ] Payment completed
- [ ] Webhook received (check logs)
- [ ] Credits added to wallet
- [ ] Transaction recorded

### Post-Test
- [ ] Wallet balance correct
- [ ] Transaction history accurate
- [ ] Email notification received
- [ ] No duplicate credits
- [ ] Logs reviewed

## Conclusion

**Expected Result**: Automatic crediting via webhook
**Fallback**: Manual crediting by admin if webhook fails
**Recommendation**: Monitor webhook delivery rate and set up alerts for failed webhooks

## Admin Dashboard Features

### Payment Tracking
- View all payment attempts
- Filter by status (Success/Pending/Failed)
- Search by user email or reference
- Manual credit button for failed payments

### Webhook Monitoring
- Webhook delivery status
- Failed webhook alerts
- Retry mechanism
- Webhook logs

## Next Steps

1. **Test in Staging**: Complete payment flow with test keys
2. **Monitor Production**: Track webhook success rate
3. **Set Up Alerts**: Notify admin of failed webhooks
4. **Document Process**: Create admin guide for manual crediting
5. **Implement Retry**: Automatic retry for failed webhooks

---

**Status**: Ready for Testing
**Priority**: High
**Owner**: Development Team
**Last Updated**: 2025-01-18
