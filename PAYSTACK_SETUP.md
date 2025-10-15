# Paystack Setup Guide

## Get Secret Key (2 minutes)

### Step 1: Create Paystack Account
1. Go to [paystack.com](https://paystack.com)
2. Click **"Get Started"**
3. Sign up with email
4. Verify email

### Step 2: Get Secret Key
1. Login to [Paystack Dashboard](https://dashboard.paystack.com)
2. Click **"Settings"** (bottom left)
3. Click **"API Keys & Webhooks"**
4. Copy **"Secret Key"** (starts with `sk_test_` or `sk_live_`)

### Step 3: Add to Render
1. Go to Render Web Service
2. Click **"Environment"** tab
3. Add variable:
   - Key: `PAYSTACK_SECRET_KEY`
   - Value: `sk_test_xxxxxxxxxxxxx`
4. Click **"Save Changes"**

### Step 4: Add Webhook URL
1. Back in Paystack Dashboard → **"API Keys & Webhooks"**
2. Scroll to **"Webhook URL"**
3. Enter: `https://your-app.onrender.com/wallet/paystack/webhook`
4. Click **"Save Changes"**

**Done!** ✅ Paystack integrated.

---

## Test Payment

1. Fund wallet on your app
2. Select Paystack payment
3. Use test card: `5060666666666666666`
4. CVV: `123`, Expiry: Any future date
5. OTP: `123456`

---

## Go Live

### Switch to Live Mode:
1. Complete Paystack verification (business details)
2. Get **Live Secret Key** (`sk_live_xxxxx`)
3. Update `PAYSTACK_SECRET_KEY` on Render
4. Update webhook URL to production domain

---

## Webhook Events

Your app handles:
- `charge.success` - Credits user wallet automatically

---

## Troubleshooting

**"Invalid signature"**
- Webhook secret mismatch
- Check `PAYSTACK_SECRET_KEY` is correct

**"Payment not credited"**
- Check webhook URL is correct
- Verify webhook is active in Paystack dashboard
- Check app logs for errors

**Test mode not working**
- Use test secret key (`sk_test_`)
- Use test cards only

---

**Status**: Ready to integrate  
**Time**: 2 minutes  
**Cost**: Free (2.9% + ₦100 per transaction)
