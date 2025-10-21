# Namaskah Pricing Integration & Rollout Plan

## Integration Plan (4 Weeks)

### Week 1: Backend Core (Days 1-7)

#### Day 1-2: Database Schema Updates
```sql
-- Add new columns to existing tables
ALTER TABLE verifications ADD COLUMN tier VARCHAR(10);
ALTER TABLE verifications ADD COLUMN base_price FLOAT;
ALTER TABLE verifications ADD COLUMN plan_discount FLOAT DEFAULT 0.0;
ALTER TABLE verifications ADD COLUMN volume_discount FLOAT DEFAULT 0.0;
ALTER TABLE verifications ADD COLUMN addon_costs FLOAT DEFAULT 0.0;

ALTER TABLE users ADD COLUMN monthly_verification_count INT DEFAULT 0;
ALTER TABLE users ADD COLUMN count_reset_date DATETIME;

ALTER TABLE subscriptions ADD COLUMN billing_cycle VARCHAR(20) DEFAULT 'monthly';
ALTER TABLE subscriptions ADD COLUMN next_billing_date DATETIME;
```

**Tasks:**
- [ ] Create migration script
- [ ] Backup production database
- [ ] Test migration on staging
- [ ] Run migration on production
- [ ] Verify data integrity

**Time**: 8 hours | **Risk**: Low

---

#### Day 3-4: Backend Integration
```python
# main.py updates

# 1. Import pricing config
from pricing_config import (
    SERVICE_TIERS, SUBSCRIPTION_PLANS, 
    get_service_tier, get_service_price, 
    calculate_rental_cost, PREMIUM_ADDONS
)

# 2. Update verification endpoint
@app.post("/verify/create")
def create_verification(req, user, db):
    # Get user plan
    subscription = get_user_subscription(user.id, db)
    user_plan = subscription.plan if subscription else 'starter'
    
    # Get monthly count
    monthly_count = get_monthly_count(user.id, db)
    
    # Calculate price
    cost = get_service_price(req.service_name, user_plan, monthly_count)
    
    # Add voice premium
    if req.capability == 'voice':
        cost += VOICE_PREMIUM
    
    # Add addons
    if req.area_code:
        cost += PREMIUM_ADDONS['custom_area_code']
    if req.carrier:
        cost += PREMIUM_ADDONS['guaranteed_carrier']
    
    # Process verification...

# 3. Update subscription endpoint
@app.post("/subscription/subscribe")
def subscribe(req, user, db):
    plan_data = SUBSCRIPTION_PLANS[req.plan]
    cost = plan_data['price']
    
    # Create subscription...

# 4. Update rental endpoint
@app.post("/rentals/create")
def create_rental(req, user, db):
    cost = calculate_rental_cost(
        req.duration_hours,
        req.service_name,
        req.mode,
        req.auto_extend
    )
    
    # Create rental...
```

**Tasks:**
- [ ] Update all pricing endpoints
- [ ] Add helper functions
- [ ] Update cost calculations
- [ ] Add tier tracking
- [ ] Test all endpoints

**Time**: 16 hours | **Risk**: Medium

---

#### Day 5-6: API Endpoints
```python
# New endpoints

@app.get("/pricing/tiers")
def get_pricing_tiers():
    """Get all pricing tiers"""
    return {
        "tiers": SERVICE_TIERS,
        "subscriptions": SUBSCRIPTION_PLANS,
        "addons": PREMIUM_ADDONS
    }

@app.get("/pricing/calculate")
def calculate_price(service: str, user: User, db: Session):
    """Calculate price for user"""
    subscription = get_user_subscription(user.id, db)
    monthly_count = get_monthly_count(user.id, db)
    
    return {
        "service": service,
        "tier": get_service_tier(service),
        "base_price": get_service_price(service, subscription.plan, monthly_count),
        "your_plan": subscription.plan,
        "discount": SUBSCRIPTION_PLANS[subscription.plan]['discount']
    }

@app.get("/user/pricing-summary")
def get_user_pricing_summary(user: User, db: Session):
    """Get personalized pricing for user"""
    # Return all prices based on user's plan
```

**Tasks:**
- [ ] Create pricing info endpoints
- [ ] Add price calculator endpoint
- [ ] Add user pricing summary
- [ ] Test API responses
- [ ] Update API documentation

**Time**: 8 hours | **Risk**: Low

---

#### Day 7: Testing & Validation
```bash
# Test suite
pytest tests/test_pricing.py
pytest tests/test_subscriptions.py
pytest tests/test_rentals.py
pytest tests/test_addons.py

# Manual testing
curl -X POST /verify/create -d '{"service_name":"whatsapp"}'
curl -X GET /pricing/calculate?service=whatsapp
curl -X POST /subscription/subscribe -d '{"plan":"pro"}'
```

**Tasks:**
- [ ] Unit tests for pricing functions
- [ ] Integration tests for endpoints
- [ ] Manual testing all scenarios
- [ ] Fix bugs found
- [ ] Document test results

**Time**: 8 hours | **Risk**: Low

---

### Week 2: Frontend Updates (Days 8-14)

#### Day 8-9: Service Selection UI
```html
<!-- templates/index.html -->
<div class="service-selector">
    <div class="tier-filter">
        <button class="tier-btn active" data-tier="all">All Services</button>
        <button class="tier-btn" data-tier="tier1">🔥 Popular ($1.50)</button>
        <button class="tier-btn" data-tier="tier2">⭐ Standard ($2.00)</button>
        <button class="tier-btn" data-tier="tier3">💎 Premium ($3.00)</button>
        <button class="tier-btn" data-tier="tier4">🌐 General ($4.00)</button>
    </div>
    
    <select id="service-select">
        <option value="whatsapp" data-tier="tier1">
            📱 WhatsApp - $1.50
        </option>
        <option value="instagram" data-tier="tier2">
            📸 Instagram - $2.00
        </option>
        <!-- ... -->
    </select>
    
    <div class="price-display">
        <span class="base-price">$2.00</span>
        <span class="your-price">Your price: $1.70</span>
        <span class="discount-badge">15% off</span>
    </div>
</div>
```

**Tasks:**
- [ ] Add tier badges to services
- [ ] Show dynamic pricing
- [ ] Add tier filter buttons
- [ ] Update service dropdown
- [ ] Show user's discount

**Time**: 12 hours | **Risk**: Low

---

#### Day 10-11: Subscription Cards
```html
<!-- Subscription comparison -->
<div class="subscription-plans">
    <div class="plan-card starter">
        <h3>Starter</h3>
        <div class="price">Free</div>
        <ul class="features">
            <li>✓ 1 free verification</li>
            <li>✓ 5 verifications/month</li>
            <li>✓ Basic support</li>
        </ul>
        <button>Current Plan</button>
    </div>
    
    <div class="plan-card pro recommended">
        <div class="badge">RECOMMENDED</div>
        <h3>Pro</h3>
        <div class="price">$20.99<span>/month</span></div>
        <ul class="features">
            <li>✓ 15% discount</li>
            <li>✓ 5 free verifications/month</li>
            <li>✓ API access (100/day)</li>
            <li>✓ Email support</li>
        </ul>
        <button>Upgrade Now</button>
    </div>
    
    <div class="plan-card turbo">
        <h3>Turbo</h3>
        <div class="price">$35.99<span>/month</span></div>
        <ul class="features">
            <li>✓ 25% discount</li>
            <li>✓ 15 free verifications/month</li>
            <li>✓ API access (500/day)</li>
            <li>✓ Priority support</li>
        </ul>
        <button>Upgrade Now</button>
    </div>
    
    <div class="plan-card enterprise">
        <h3>Enterprise</h3>
        <div class="price">$55.99<span>/month</span></div>
        <ul class="features">
            <li>✓ 40% discount</li>
            <li>✓ 50 free verifications/month</li>
            <li>✓ Unlimited API</li>
            <li>✓ 24/7 support</li>
        </ul>
        <button>Contact Sales</button>
    </div>
</div>
```

**Tasks:**
- [ ] Create subscription comparison cards
- [ ] Add recommended badge
- [ ] Show savings calculator
- [ ] Add upgrade buttons
- [ ] Mobile responsive design

**Time**: 12 hours | **Risk**: Low

---

#### Day 12-13: Premium Add-ons UI
```html
<!-- Add-ons during verification -->
<div class="premium-addons">
    <h4>Premium Options</h4>
    
    <label class="addon-option">
        <input type="checkbox" name="area_code" value="1">
        <div class="addon-info">
            <span class="addon-name">📍 Custom Area Code</span>
            <span class="addon-price">+$10</span>
        </div>
        <p class="addon-desc">Select specific area code</p>
    </label>
    
    <label class="addon-option">
        <input type="checkbox" name="carrier" value="1">
        <div class="addon-info">
            <span class="addon-name">📡 Guaranteed Carrier</span>
            <span class="addon-price">+$25</span>
        </div>
        <p class="addon-desc">Choose area code + ISP (Verizon, AT&T, T-Mobile)</p>
    </label>
    
    <label class="addon-option">
        <input type="checkbox" name="priority" value="1">
        <div class="addon-info">
            <span class="addon-name">⚡ Priority Queue</span>
            <span class="addon-price">+$5</span>
        </div>
        <p class="addon-desc">Faster processing</p>
    </label>
</div>

<div class="total-price">
    <span>Total:</span>
    <span class="amount">$2.00</span>
</div>
```

**Tasks:**
- [ ] Add addon checkboxes
- [ ] Show real-time price updates
- [ ] Add area code selector
- [ ] Add carrier selector
- [ ] Update total dynamically

**Time**: 12 hours | **Risk**: Medium

---

#### Day 14: Rental Duration Selector
```html
<!-- Rental options -->
<div class="rental-duration">
    <h4>Select Duration</h4>
    
    <div class="duration-tabs">
        <button class="tab active" data-type="hourly">Hourly</button>
        <button class="tab" data-type="weekly">Weekly</button>
        <button class="tab" data-type="monthly">Monthly</button>
        <button class="tab" data-type="annual">Annual</button>
    </div>
    
    <div class="duration-options hourly">
        <label><input type="radio" name="duration" value="1"> 1 hour - $2</label>
        <label><input type="radio" name="duration" value="6"> 6 hours - $3</label>
        <label><input type="radio" name="duration" value="12"> 12 hours - $4</label>
        <label><input type="radio" name="duration" value="24"> 24 hours - $5</label>
    </div>
    
    <div class="rental-type">
        <label>
            <input type="radio" name="type" value="service" checked>
            Service-Specific (Lower price)
        </label>
        <label>
            <input type="radio" name="type" value="general">
            General Use (Any service, always active)
        </label>
    </div>
</div>
```

**Tasks:**
- [ ] Add duration selector
- [ ] Add rental type toggle
- [ ] Show price comparison
- [ ] Add savings calculator
- [ ] Mobile optimization

**Time**: 8 hours | **Risk**: Low

---

### Week 3: Testing & Optimization (Days 15-21)

#### Day 15-16: Integration Testing
```bash
# Test scenarios
1. New user signup → Starter plan
2. Create verification → Tier 1 pricing
3. Upgrade to Pro → 15% discount applied
4. Create 10 verifications → Volume discount
5. Add area code → +$10 addon
6. Create rental → Hourly pricing
7. Upgrade to Enterprise → 40% discount
```

**Tasks:**
- [ ] Test all user flows
- [ ] Test pricing calculations
- [ ] Test subscription upgrades
- [ ] Test addon combinations
- [ ] Test rental scenarios
- [ ] Fix bugs found

**Time**: 16 hours | **Risk**: Medium

---

#### Day 17-18: Performance Optimization
```python
# Add caching
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_service_tier_cached(service_name):
    return get_service_tier(service_name)

# Add database indexes
CREATE INDEX idx_verifications_user_created ON verifications(user_id, created_at);
CREATE INDEX idx_subscriptions_user_status ON subscriptions(user_id, status);

# Optimize queries
def get_monthly_count(user_id, db):
    # Use cached count
    cache_key = f"monthly_count:{user_id}"
    cached = redis.get(cache_key)
    if cached:
        return int(cached)
    
    count = db.query(Verification).filter(...).count()
    redis.setex(cache_key, 3600, count)
    return count
```

**Tasks:**
- [ ] Add caching layer
- [ ] Optimize database queries
- [ ] Add database indexes
- [ ] Load testing
- [ ] Performance monitoring

**Time**: 12 hours | **Risk**: Low

---

#### Day 19-21: Documentation & Training
```markdown
# User Documentation
- Pricing tiers explained
- Subscription comparison
- How to use add-ons
- Rental options guide

# Admin Documentation
- Pricing configuration
- How to adjust prices
- Monitoring metrics
- Troubleshooting guide

# API Documentation
- New pricing endpoints
- Request/response examples
- Error codes
- Rate limits
```

**Tasks:**
- [ ] Update user documentation
- [ ] Create admin guide
- [ ] Update API docs
- [ ] Create video tutorials
- [ ] Train support team

**Time**: 12 hours | **Risk**: Low

---

### Week 4: Gradual Rollout (Days 22-28)

#### Phase 1: Internal Testing (Day 22-23)
```
Target: Admin accounts + test users
Users: 5-10 accounts
Duration: 2 days
```

**Checklist:**
- [ ] Admin accounts test all features
- [ ] Create test verifications
- [ ] Test all subscription tiers
- [ ] Test all add-ons
- [ ] Test all rental durations
- [ ] Monitor for errors
- [ ] Collect feedback

**Success Criteria:**
- Zero critical bugs
- All features working
- Positive feedback

---

#### Phase 2: Beta Users (Day 24-25)
```
Target: 10% of active users (opt-in)
Users: 50-100 accounts
Duration: 2 days
```

**Implementation:**
```python
# Feature flag
BETA_USERS = ['user_123', 'user_456', ...]

def use_new_pricing(user_id):
    return user_id in BETA_USERS or user.beta_opt_in

@app.post("/verify/create")
def create_verification(req, user, db):
    if use_new_pricing(user.id):
        # New pricing
        cost = get_service_price(...)
    else:
        # Old pricing
        cost = SMS_PRICING['popular']
```

**Checklist:**
- [ ] Send beta invitation emails
- [ ] Enable new pricing for beta users
- [ ] Monitor usage patterns
- [ ] Track conversion rates
- [ ] Collect user feedback
- [ ] Fix issues found

**Success Criteria:**
- <5% error rate
- >80% positive feedback
- No revenue drop

---

#### Phase 3: Soft Launch (Day 26)
```
Target: 50% of users (random)
Users: 500-1000 accounts
Duration: 1 day
```

**Implementation:**
```python
def use_new_pricing(user_id):
    # 50% rollout
    return hash(user_id) % 2 == 0
```

**Checklist:**
- [ ] Enable for 50% of users
- [ ] Monitor revenue metrics
- [ ] Track error rates
- [ ] Monitor support tickets
- [ ] A/B test results
- [ ] Adjust if needed

**Success Criteria:**
- Revenue stable or increased
- <2% error rate
- Support tickets manageable

---

#### Phase 4: Full Launch (Day 27-28)
```
Target: 100% of users
Users: All accounts
Duration: 2 days
```

**Implementation:**
```python
def use_new_pricing(user_id):
    return True  # Everyone
```

**Checklist:**
- [ ] Enable for all users
- [ ] Send announcement email
- [ ] Update website pricing page
- [ ] Monitor all metrics
- [ ] Respond to feedback
- [ ] Celebrate launch! 🎉

**Success Criteria:**
- Revenue increased
- User satisfaction maintained
- System stable

---

## Rollout Communication Plan

### Week Before Launch
**Email 1: Announcement**
```
Subject: 🎉 New Pricing Coming Soon - Better Value for You!

Hi [Name],

We're excited to announce new pricing that gives you more flexibility and better value:

✨ Lower prices on popular services (WhatsApp, Telegram: $1.50)
✨ New hourly rentals starting at $2
✨ More subscription options ($20.99, $35.99, $55.99)
✨ Premium add-ons (custom area code, guaranteed carrier)

Your current plan and pricing are protected for 3 months.

Learn more: [link]
```

---

### Launch Day
**Email 2: Launch**
```
Subject: 🚀 New Pricing is Live!

The new pricing is now available:

🔥 Popular services: $1.50 (was $2.00)
💎 Premium services: $3.00 (banking, finance)
⏰ Hourly rentals: $2-$5 (NEW)
📊 4 subscription tiers to choose from

Explore new pricing: [link]
```

---

### Week After Launch
**Email 3: Migration Reminder**
```
Subject: ⏰ Migrate to New Pricing - Save Up to 40%

You're still on the old pricing. Switch to save:

Pro Plan ($20.99/mo): Save 15% on all verifications
Turbo Plan ($35.99/mo): Save 25%
Enterprise ($55.99/mo): Save 40%

Upgrade now: [link]
```

---

## Monitoring & Metrics

### Key Metrics to Track

**Revenue Metrics:**
- [ ] Daily revenue
- [ ] Revenue by tier
- [ ] Revenue by subscription
- [ ] Revenue by add-ons
- [ ] Average order value

**User Metrics:**
- [ ] New signups
- [ ] Subscription conversions
- [ ] Plan upgrades
- [ ] Churn rate
- [ ] User satisfaction

**Technical Metrics:**
- [ ] API response times
- [ ] Error rates
- [ ] Database performance
- [ ] Cache hit rates
- [ ] Server load

**Business Metrics:**
- [ ] Profit margin
- [ ] Customer lifetime value
- [ ] Cost per acquisition
- [ ] Return on investment

---

## Rollback Plan

### If Issues Arise

**Minor Issues (<5% error rate):**
1. Fix bugs immediately
2. Continue rollout
3. Monitor closely

**Major Issues (>5% error rate):**
1. Pause rollout at current phase
2. Fix critical bugs
3. Resume after 24 hours stable

**Critical Issues (>10% error rate or revenue drop):**
1. Immediate rollback to old pricing
2. Investigate root cause
3. Fix all issues
4. Restart rollout from Phase 1

**Rollback Command:**
```python
# Set feature flag
NEW_PRICING_ENABLED = False

# All users revert to old pricing
def use_new_pricing(user_id):
    return NEW_PRICING_ENABLED
```

---

## Success Criteria

### Week 1 (Integration)
- [ ] All endpoints working
- [ ] Zero critical bugs
- [ ] Tests passing

### Week 2 (Frontend)
- [ ] UI updates complete
- [ ] Mobile responsive
- [ ] User testing positive

### Week 3 (Testing)
- [ ] All scenarios tested
- [ ] Performance optimized
- [ ] Documentation complete

### Week 4 (Rollout)
- [ ] Beta successful
- [ ] Soft launch stable
- [ ] Full launch complete

### Month 1 (Post-Launch)
- [ ] Revenue: $35,000+
- [ ] 300+ paid subscriptions
- [ ] <5% churn rate
- [ ] >80% user satisfaction

---

## Timeline Summary

| Week | Phase | Focus | Risk | Time |
|------|-------|-------|------|------|
| 1 | Backend | Core integration | Medium | 40h |
| 2 | Frontend | UI updates | Low | 44h |
| 3 | Testing | QA & optimization | Medium | 40h |
| 4 | Rollout | Gradual launch | Low | 20h |

**Total Time**: 144 hours (18 days)
**Total Cost**: $7,200 ($50/hour)
**Expected ROI**: 400% in Month 1

---

**Status**: Ready to Execute
**Start Date**: [Set date]
**Launch Date**: [Set date + 28 days]
