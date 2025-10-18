# Namaskah Affiliate Program Documentation

## Overview
The Namaskah Affiliate Program rewards users for referring new customers with a 10% commission on all referred user spending.

## How It Works

### For Affiliates (Referrers)
1. **Get Your Referral Code**: Every user receives a unique referral code upon registration
2. **Share Your Link**: Share your referral link with potential users
3. **Earn Commissions**: Earn 10% of everything your referrals spend (lifetime)

### For Referred Users
1. **Sign Up with Referral Code**: Use a referral link or enter code during registration
2. **Get Bonus**: Receive 1 free verification upon first funding (N2.50+ minimum)
3. **No Extra Cost**: Pay standard prices, affiliate commission comes from platform

## Commission Structure

### Affiliate Earnings
- **Commission Rate**: 10% of all referred user spending
- **Payment Type**: Credited as Namaskah coins (N) to wallet
- **Minimum Payout**: N1 (automatic credit to wallet)
- **Payment Timing**: Instant (credited when referred user makes purchase)
- **Lifetime Value**: Earn from all future purchases by referred users

### Referred User Bonus
- **Welcome Bonus**: 1 free verification (N1 value)
- **Activation**: Bonus granted when user funds N2.50+ for first time
- **Additional Benefit**: 1 extra free verification on signup (total 2 free)

## ROI Analysis

### For Affiliates

#### Scenario 1: Casual Referrer (5 referrals/month)
- **Referrals**: 5 users/month
- **Avg Spending per User**: N10/month
- **Monthly Commission**: 5 × N10 × 10% = N5/month
- **Annual Earnings**: N60/year
- **Effort**: Minimal (social media sharing)

#### Scenario 2: Active Promoter (20 referrals/month)
- **Referrals**: 20 users/month
- **Avg Spending per User**: N15/month
- **Monthly Commission**: 20 × N15 × 10% = N30/month
- **Annual Earnings**: N360/year
- **Effort**: Moderate (blog posts, forums)

#### Scenario 3: Professional Affiliate (100 referrals/month)
- **Referrals**: 100 users/month
- **Avg Spending per User**: N20/month
- **Monthly Commission**: 100 × N20 × 10% = N200/month
- **Annual Earnings**: N2,400/year ($4,800 USD)
- **Effort**: High (dedicated marketing, content creation)

#### Scenario 4: Enterprise Partner (500 referrals/month)
- **Referrals**: 500 users/month
- **Avg Spending per User**: N25/month
- **Monthly Commission**: 500 × N25 × 10% = N1,250/month
- **Annual Earnings**: N15,000/year ($30,000 USD)
- **Effort**: Full-time (API integration, white-label solutions)

### For Platform (Admin)

#### Revenue Impact Analysis
- **Gross Revenue per User**: N20/month average
- **Affiliate Commission**: N2/month (10%)
- **Net Revenue**: N18/month (90%)
- **Customer Acquisition Cost**: N2 (one-time via affiliate)
- **Break-even**: Month 1 (immediate profitability)

#### Growth Projections
- **Without Affiliates**: 100 new users/month (organic)
- **With Affiliates**: 300-500 new users/month (3-5x growth)
- **Commission Cost**: N600-1,000/month
- **Additional Revenue**: N6,000-10,000/month
- **Net Gain**: N5,400-9,000/month (540-900% ROI)

## Technical Implementation

### Database Schema
```sql
-- Referral tracking
referrals:
  - referrer_id: User who referred
  - referred_id: User who was referred
  - reward_amount: Total commissions earned
  - created_at: Referral date

-- User fields
users:
  - referral_code: Unique code (6 chars)
  - referred_by: ID of referrer
  - referral_earnings: Total earned from referrals
```

### Commission Calculation
```python
# When referred user makes purchase
referred_user_spending = transaction.amount  # e.g., N10
commission_rate = 0.10  # 10%
commission = referred_user_spending * commission_rate  # N1

# Credit affiliate
referrer.credits += commission
referrer.referral_earnings += commission
```

### Admin Controls

#### Credit User
```bash
POST /admin/credits/add
{
  "user_id": "user_123",
  "amount": 10.0,
  "reason": "Affiliate bonus"
}
```

#### Debit User
```bash
POST /admin/credits/deduct
{
  "user_id": "user_123",
  "amount": 5.0,
  "reason": "Refund reversal"
}
```

#### View Affiliate Stats
```bash
GET /admin/affiliates/stats
Response:
{
  "total_affiliates": 1250,
  "active_affiliates": 450,
  "total_commissions_paid": 15000,
  "top_affiliates": [...]
}
```

## Marketing Materials

### Referral Link Format
```
https://namaskah.app/app?ref=ABC123
```

### Email Template
```
Subject: Earn 10% Commission with Namaskah Affiliate Program

Hi [Name],

Start earning passive income by referring users to Namaskah SMS!

Your Referral Link: https://namaskah.app/app?ref=[CODE]

Benefits:
✅ 10% commission on all referral spending (lifetime)
✅ Instant payouts to your wallet
✅ No minimum payout threshold
✅ Professional marketing materials provided

Average Earnings:
- 10 referrals = N30/month
- 50 referrals = N150/month
- 100 referrals = N300/month

Get started: [Dashboard Link]
```

### Social Media Copy
```
💰 Earn money with Namaskah SMS!

Refer friends and earn 10% commission on everything they spend.

🎯 Lifetime commissions
💳 Instant payouts
📈 Unlimited earning potential

Join now: https://namaskah.app/app?ref=[CODE]
```

## Fraud Prevention

### Anti-Abuse Measures
1. **Email Verification**: Required for both referrer and referred
2. **Minimum Funding**: N2.50 minimum to activate referral bonus
3. **IP Tracking**: Detect self-referrals from same IP
4. **Device Fingerprinting**: Prevent multi-account abuse
5. **Manual Review**: Flag suspicious patterns (>50 referrals/day)

### Admin Monitoring
- **Suspicious Activity Alerts**: Auto-flag unusual patterns
- **Commission Holds**: 7-day hold for new affiliates
- **Refund Clawback**: Reverse commission if user refunds
- **Account Suspension**: Ban fraudulent affiliates

## Payout Methods

### Current: Wallet Credits
- **Type**: Namaskah coins (N)
- **Use**: Platform services only
- **Minimum**: N1 (no minimum)
- **Timing**: Instant

### Future: Cash Payouts (Planned)
- **Type**: Bank transfer, PayPal, crypto
- **Minimum**: N50 ($100 USD)
- **Timing**: Weekly/monthly
- **Fee**: 2% processing fee

## Reporting & Analytics

### Affiliate Dashboard
- **Total Referrals**: Count of referred users
- **Active Referrals**: Users who made purchases
- **Total Earnings**: Lifetime commission
- **Monthly Earnings**: Current month commission
- **Conversion Rate**: Signups → Paying customers
- **Top Performers**: Best converting referrals

### Admin Dashboard
- **Total Affiliates**: All users with referrals
- **Commission Paid**: Total platform cost
- **Revenue Generated**: Total from referred users
- **ROI**: Revenue / Commission ratio
- **Top Affiliates**: Highest earners
- **Fraud Alerts**: Suspicious activity

## Support & Resources

### For Affiliates
- **Help Center**: https://namaskah.app/affiliate-help
- **Marketing Kit**: Banners, logos, copy templates
- **API Documentation**: For advanced integrations
- **Email Support**: affiliates@namaskah.app

### For Admin
- **Admin Panel**: /admin/affiliates
- **Fraud Detection**: /admin/affiliates/fraud
- **Payout Management**: /admin/affiliates/payouts
- **Analytics**: /admin/affiliates/analytics

## Terms & Conditions

### Eligibility
- Must be 18+ years old
- Valid email address required
- Comply with platform terms of service
- No fraudulent activity

### Commission Rules
- 10% of gross spending (before discounts)
- Lifetime tracking (no expiration)
- Instant credit to wallet
- Non-transferable between users

### Termination
- Platform reserves right to terminate affiliates
- Fraudulent activity results in ban
- Unpaid commissions forfeited upon termination
- 30-day notice for policy changes

## Version History
- **v1.0** (2025-01-18): Initial affiliate program launch
- **v1.1** (Planned): Cash payout options
- **v1.2** (Planned): Tiered commission rates (10-15%)
