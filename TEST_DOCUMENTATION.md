# Test Documentation - Namaskah SMS

## Test Suite for All Features

### 1. SMS Verification Flow

#### Test 1.1: Create SMS Verification
**Endpoint:** `POST /verify/create`
```json
{
  "service_name": "whatsapp",
  "capability": "sms"
}
```
**Expected:**
- ✅ Returns verification ID
- ✅ Returns phone number
- ✅ Deducts N1.0 from credits
- ✅ Status: "pending"

**Status:** ⏳ PENDING

---

#### Test 1.2: SMS Code Arrival & Copy Button
**Steps:**
1. Create verification
2. Wait for SMS (60-120s)
3. Check messages endpoint
4. Verify code extraction (4-8 digits)
5. Click copy button
6. Verify notification shows "Code XXXX copied"

**Expected:**
- ✅ Code extracted from message
- ✅ Copy button visible
- ✅ Notification displays copied code
- ✅ Code in clipboard

**Status:** ⏳ PENDING

---

#### Test 1.3: Countdown Timer Expiry
**Steps:**
1. Create verification
2. Wait for countdown to reach 0
3. Verify retry modal appears

**Expected:**
- ✅ Timer counts down from service-specific duration
- ✅ Modal shows 3 options: Voice / Same / New
- ✅ No auto-cancel (modal replaces old behavior)

**Status:** ⏳ PENDING

---

#### Test 1.4: Retry with Voice
**Endpoint:** `POST /verify/{id}/retry?retry_type=voice`

**Expected:**
- ✅ Original SMS cost refunded (N1.0)
- ✅ New voice verification created
- ✅ Voice cost charged (N1.25)
- ✅ Transaction log shows refund + new charge
- ✅ Returns new verification ID

**Status:** ⏳ PENDING

---

#### Test 1.5: Retry with Same Number
**Endpoint:** `POST /verify/{id}/retry?retry_type=same`

**Expected:**
- ✅ Original cost refunded
- ✅ Same number reused
- ✅ New cost charged
- ✅ Verification status reset to "pending"

**Status:** ⏳ PENDING

---

#### Test 1.6: Retry with New Number
**Endpoint:** `POST /verify/{id}/retry?retry_type=new`

**Expected:**
- ✅ Original cost refunded
- ✅ New phone number assigned
- ✅ New cost charged
- ✅ Old number added to banned list
- ✅ Returns new verification ID

**Status:** ⏳ PENDING

---

### 2. Voice Verification Flow

#### Test 2.1: Create Voice Verification
**Endpoint:** `POST /verify/create`
```json
{
  "service_name": "telegram",
  "capability": "voice"
}
```

**Expected:**
- ✅ Returns verification ID
- ✅ Returns phone number
- ✅ Deducts N1.25 (SMS + N0.25)
- ✅ Capability: "voice"

**Status:** ⏳ PENDING

---

#### Test 2.2: Voice Call Details & Copy Button
**Endpoint:** `GET /verify/{id}/voice`

**Expected:**
- ✅ Returns transcription
- ✅ Code extracted from transcription
- ✅ Copy button visible
- ✅ Audio URL (if available)
- ✅ Call duration displayed

**Status:** ⏳ PENDING

---

#### Test 2.3: Voice Verification Refund
**Steps:**
1. Create voice verification
2. Wait for timer expiry
3. Retry with new number

**Expected:**
- ✅ Voice cost refunded (N1.25)
- ✅ New verification charged
- ✅ Transaction log accurate

**Status:** ⏳ PENDING

---

### 3. Any Service (Unlisted) Flow

#### Test 3.1: Create Unlisted Service Verification
**Endpoint:** `POST /verify/create`
```json
{
  "service_name": "discord",
  "capability": "sms"
}
```

**Expected:**
- ✅ Works with any service name
- ✅ Deducts N1.25 (general pricing)
- ✅ Returns phone number
- ✅ Copy button works same as regular SMS

**Status:** ⏳ PENDING

---

### 4. Rental Number Flow

#### Test 4.1: Create Rental
**Endpoint:** `POST /rentals/create`
```json
{
  "service_name": "telegram",
  "duration_hours": 168,
  "mode": "always_ready"
}
```

**Expected:**
- ✅ Returns rental ID
- ✅ Returns phone number
- ✅ Deducts N5.0 (7 days)
- ✅ Expires_at set correctly

**Status:** ❌ FAILING (500 error)

---

#### Test 4.2: Rental SMS Messages & Copy Button
**Endpoint:** `GET /rentals/{id}/messages`

**Expected:**
- ✅ Returns all SMS messages
- ✅ Code extracted from each message
- ✅ Copy button for each code
- ✅ Full message in collapsible details

**Status:** ⏳ PENDING

---

#### Test 4.3: Extend Rental
**Endpoint:** `POST /rentals/{id}/extend`
```json
{
  "additional_hours": 168
}
```

**Expected:**
- ✅ Extends expiry date
- ✅ Charges additional cost
- ✅ Updates duration_hours

**Status:** ⏳ PENDING

---

#### Test 4.4: Release Rental (Early Refund)
**Endpoint:** `POST /rentals/{id}/release`

**Expected:**
- ✅ Calculates unused time
- ✅ Refunds 50% of unused time
- ✅ Status changed to "released"
- ✅ Transaction log shows refund

**Status:** ⏳ PENDING

---

### 5. Banned Number Tracking

#### Test 5.1: Number Added to Banned List
**Steps:**
1. Create verification
2. Wait for timer expiry
3. Retry with new number

**Expected:**
- ✅ Old number added to banned_numbers table
- ✅ Service name recorded
- ✅ Area code extracted (first 3 digits)
- ✅ Carrier info saved (if available)
- ✅ Fail count = 1

**Status:** ⏳ PENDING

---

#### Test 5.2: Admin View Banned Numbers
**Endpoint:** `GET /admin/banned-numbers`

**Expected:**
- ✅ Returns list of banned numbers
- ✅ Shows phone, service, area code, carrier
- ✅ Shows fail count
- ✅ Statistics by service and carrier

**Status:** ⏳ PENDING

---

#### Test 5.3: Filter Banned Numbers
**Endpoint:** `GET /admin/banned-numbers?service=whatsapp&min_fails=2`

**Expected:**
- ✅ Filters by service name
- ✅ Filters by area code
- ✅ Filters by carrier
- ✅ Filters by minimum fail count

**Status:** ⏳ PENDING

---

### 6. Auto-Refund System

#### Test 6.1: SMS Verification Auto-Refund
**Scenario:** SMS not received, retry with voice

**Expected:**
- ✅ Original SMS cost (N1.0) refunded immediately
- ✅ Transaction created: "Refund for failed whatsapp verification"
- ✅ Credits updated before voice charge
- ✅ Voice cost (N1.25) charged after
- ✅ Net change: -N0.25

**Status:** ⏳ PENDING

---

#### Test 6.2: Voice Verification Auto-Refund
**Scenario:** Voice not received, retry with new number

**Expected:**
- ✅ Original voice cost (N1.25) refunded
- ✅ New SMS cost (N1.0) charged
- ✅ Net change: +N0.25 (refund)

**Status:** ⏳ PENDING

---

#### Test 6.3: Multiple Retry Refunds
**Scenario:** Retry 3 times with different options

**Expected:**
- ✅ Each retry refunds previous cost
- ✅ Each retry charges new cost
- ✅ Transaction log shows all refunds
- ✅ Final balance accurate

**Status:** ⏳ PENDING

---

### 7. Copy Button Functionality

#### Test 7.1: SMS Code Copy
**Steps:**
1. Receive SMS: "Your code is 123456"
2. Click copy button

**Expected:**
- ✅ Extracts "123456"
- ✅ Copies to clipboard
- ✅ Shows notification: "Code 123456 copied to clipboard"

**Status:** ⏳ PENDING

---

#### Test 7.2: Voice Transcription Copy
**Steps:**
1. Receive voice call
2. Transcription: "Your verification code is 7 8 9 0 1 2"
3. Click copy button

**Expected:**
- ✅ Extracts "789012"
- ✅ Copies to clipboard
- ✅ Shows notification with code

**Status:** ⏳ PENDING

---

#### Test 7.3: Rental SMS Copy
**Steps:**
1. Rental receives SMS
2. View messages
3. Click copy on each message

**Expected:**
- ✅ Each message has copy button
- ✅ Code extracted correctly
- ✅ Notification for each copy

**Status:** ⏳ PENDING

---

## Test Execution Plan

### Phase 1: Backend API Tests (Automated)
```bash
python3 test_all_features.py
```

### Phase 2: Frontend UI Tests (Manual)
1. Create verification
2. Wait for SMS
3. Test copy button
4. Test retry modal
5. Verify notifications

### Phase 3: Integration Tests
1. End-to-end SMS flow
2. End-to-end Voice flow
3. End-to-end Rental flow
4. Retry scenarios
5. Refund accuracy

---

## Current Status Summary

| Feature | Status | Notes |
|---------|--------|-------|
| SMS Verification | ✅ PASS | Creates successfully, Cost: N1.0 |
| Voice Verification | ✅ PASS | Creates successfully, Cost: N1.25 |
| Any Service | ✅ PASS | Creates successfully, Cost: N1.25 |
| Rental Creation | ❌ FAIL | 500 error - needs debugging |
| Copy Button (SMS) | ⏳ PENDING | Code implemented, needs SMS to test |
| Copy Button (Voice) | ⏳ PENDING | Code implemented, needs call to test |
| Copy Button (Rental) | ⏳ PENDING | Code implemented, needs SMS to test |
| Retry Modal | ⏳ PENDING | Code implemented, needs timer expiry |
| Retry with Voice | ✅ PASS | Refunds SMS, charges voice |
| Retry with Same | ✅ PASS | Reuses same number |
| Retry with New | ❌ FAIL | TextVerified API 400 (rate limit) |
| Auto-Refund | ✅ PASS | 2 refunds confirmed in transactions |
| Banned Numbers | ✅ PASS | 3 numbers tracked |
| Admin View | ✅ PASS | Returns banned list with stats |

---

## Known Issues

1. **Rental Creation Failing** - 500 error, needs debugging
2. **TextVerified Rate Limiting** - API blocks rapid requests (normal)
3. **Balance Low** - $20 remaining (10-20 verifications)

---

## Next Steps

1. Fix rental creation bug
2. Run automated test suite
3. Wait for actual SMS/Voice to test copy buttons
4. Document all test results
5. Update status for each test
