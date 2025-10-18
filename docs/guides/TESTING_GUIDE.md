# 🧪 SMS Verification Testing Guide

## 🎯 Focus: Testing Core Verification System

Email setup postponed - focusing on SMS verification functionality.

---

## ✅ Pre-Testing Checklist

- [x] Email verification requirement removed
- [x] Users can create verifications immediately
- [x] Google OAuth fixed
- [x] Deployed to production

---

## 🚀 Quick Test (5 minutes)

### 1. Register & Login
1. Go to: https://namaskah.onrender.com/app
2. Register new account (email verification not required)
3. Login successful → Dashboard loads

### 2. Fund Wallet
**Option A: Use Free Verification**
- New users get 1 free verification
- Skip funding for first test

**Option B: Fund with Paystack**
- Click "Fund Wallet"
- Enter amount (minimum $5 USD)
- Complete Paystack payment
- Credits added to wallet

### 3. Create SMS Verification
1. Select service (e.g., WhatsApp, Telegram)
2. Click "Get Number"
3. Receive phone number instantly
4. Cost deducted from wallet/free verification

### 4. Check Messages
1. Wait 60-120 seconds
2. Click "Check Messages"
3. SMS code should appear
4. Copy code for use

### 5. Cancel (Optional)
- Click "Cancel Verification"
- Full refund to wallet
- Number released

---

## 🔍 Detailed Testing Scenarios

### Scenario 1: Free Verification (New User)
```
1. Register → 1 free verification available
2. Select WhatsApp
3. Get number → Free verification used
4. Check messages → SMS received
5. Balance: 0 credits, 0 free verifications
```

### Scenario 2: Paid Verification
```
1. Fund wallet → N5 ($10 USD)
2. Select Instagram
3. Get number → N1 deducted
4. Check messages → SMS received
5. Balance: N4 remaining
```

### Scenario 3: Cancel & Refund
```
1. Create verification → N1 deducted
2. Wait 30 seconds
3. Cancel verification
4. Refund → N1 returned
5. Balance restored
```

### Scenario 4: Multiple Services
```
1. WhatsApp verification → Success
2. Telegram verification → Success
3. Facebook verification → Success
4. Check history → All 3 listed
```

### Scenario 5: Voice Verification
```
1. Select service
2. Choose "Voice" capability
3. Get number → N1.25 deducted
4. Receive voice call
5. Check transcription
```

---

## 🧪 Test Cases

### Authentication
- [ ] Register new user
- [ ] Login with email/password
- [ ] Login with Google OAuth
- [ ] Logout
- [ ] Session persists on refresh

### Wallet
- [ ] View current balance
- [ ] Fund wallet via Paystack
- [ ] Payment confirmation
- [ ] Transaction history
- [ ] Export transactions CSV

### Verification Creation
- [ ] Select service from list
- [ ] Search services
- [ ] Filter by category
- [ ] Create SMS verification
- [ ] Create voice verification
- [ ] Use free verification
- [ ] Insufficient credits error

### Message Retrieval
- [ ] Check messages button
- [ ] SMS received within 2 minutes
- [ ] Multiple messages displayed
- [ ] Copy code functionality
- [ ] Auto-refresh messages

### Verification Management
- [ ] View active verifications
- [ ] Cancel verification
- [ ] Refund processed
- [ ] View history
- [ ] Export history CSV
- [ ] Filter by service
- [ ] Filter by status

### Number Rentals
- [ ] Create rental (7 days)
- [ ] View active rentals
- [ ] Check rental messages
- [ ] Extend rental
- [ ] Release rental early
- [ ] 50% refund received

### Admin Panel
- [ ] Login as admin
- [ ] View statistics
- [ ] Filter by time period
- [ ] View users list
- [ ] Search users
- [ ] Add credits to user
- [ ] View support tickets
- [ ] Export data CSV

---

## 🐛 Known Issues to Test

### Critical
- [ ] TextVerified API connection
- [ ] Payment gateway integration
- [ ] Refund processing
- [ ] Session management

### Medium
- [ ] Message polling frequency
- [ ] Auto-cancel after timeout
- [ ] Webhook delivery
- [ ] Email notifications (when SMTP configured)

### Low
- [ ] UI responsiveness
- [ ] Dark mode toggle
- [ ] Mobile gestures
- [ ] Offline queue

---

## 📊 Performance Testing

### Load Test
```
1. Create 10 verifications rapidly
2. Check all messages
3. Cancel 5 verifications
4. Verify refunds processed
5. Check system stability
```

### Stress Test
```
1. Multiple users simultaneously
2. Concurrent verifications
3. Payment processing
4. Database performance
5. API rate limiting
```

---

## 🔧 Testing Tools

### Browser DevTools
- Network tab → API calls
- Console → JavaScript errors
- Application → LocalStorage/Session

### API Testing
```bash
# Get auth token
curl -X POST https://namaskah.onrender.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}'

# Create verification
curl -X POST https://namaskah.onrender.com/verify/create \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"service_name":"whatsapp","capability":"sms"}'

# Check messages
curl https://namaskah.onrender.com/verify/{id}/messages \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 📝 Test Results Template

```
Date: ___________
Tester: ___________
Environment: Production / Staging

✅ PASSED:
- 
- 

❌ FAILED:
- 
- 

🐛 BUGS FOUND:
- 

💡 SUGGESTIONS:
- 
```

---

## 🎯 Priority Testing Order

1. **Authentication** (5 min)
   - Register, login, Google OAuth

2. **Free Verification** (5 min)
   - Use 1 free verification
   - Test SMS retrieval

3. **Payment** (10 min)
   - Fund wallet
   - Verify credits added

4. **Paid Verification** (5 min)
   - Create verification
   - Check deduction

5. **Cancel & Refund** (5 min)
   - Cancel verification
   - Verify refund

6. **History & Export** (5 min)
   - View history
   - Export CSV

**Total: ~35 minutes for complete test**

---

## 🚨 Critical Paths to Test

### Path 1: New User Journey
```
Register → Login → Use Free Verification → Get SMS → Success
```

### Path 2: Paying User Journey
```
Register → Fund Wallet → Create Verification → Get SMS → Success
```

### Path 3: Refund Journey
```
Create Verification → Cancel → Refund Received → Success
```

---

## 📞 Support During Testing

**Issues to Report**:
- API errors (500, 404, 403)
- Payment failures
- SMS not received
- Refund not processed
- UI bugs

**Where to Check**:
- Render logs: https://dashboard.render.com
- Browser console
- Network tab
- Database records

---

## ✅ Success Criteria

- [ ] Users can register and login
- [ ] Free verification works
- [ ] Payment processing works
- [ ] SMS received within 2 minutes
- [ ] Refunds processed correctly
- [ ] History displays correctly
- [ ] Admin panel accessible
- [ ] No critical errors

---

**Status**: Ready for testing
**URL**: https://namaskah.onrender.com
**Admin**: admin@namaskah.app / Admin@2024!
