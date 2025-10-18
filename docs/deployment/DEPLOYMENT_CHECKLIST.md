# Deployment Checklist

## ✅ Pre-Deployment

- [x] Code refactored (modular JS)
- [x] Mobile features added (biometric, offline)
- [x] Admin panel improved (search, tickets, export)
- [x] Status page enhanced (stats, monitoring)
- [x] CI/CD workflows created
- [x] Documentation updated

## 🚀 Deploy to Production

### Option 1: Auto-Deploy (Recommended)
```bash
./deploy.sh
```

### Option 2: Manual
```bash
git add .
git commit -m "Production updates"
git push origin main
```

**Render auto-deploys on push to main**

---

## ✅ Post-Deployment Verification

### 1. Health Check (2 min)
```bash
curl https://namaskah.app/health
# Should return: {"status":"healthy"}
```

### 2. Test Key Features (5 min)

**Authentication**:
- [ ] Register new user
- [ ] Login works
- [ ] Google OAuth works

**Verification**:
- [ ] Create SMS verification
- [ ] Receive phone number
- [ ] Check messages works
- [ ] Cancel & refund works

**Payment**:
- [ ] Fund wallet (Paystack)
- [ ] Credits added correctly
- [ ] Transaction recorded

**Admin Panel**:
- [ ] Login as admin
- [ ] View statistics
- [ ] Search users works
- [ ] Support tickets load
- [ ] Export CSV works

**Status Page**:
- [ ] Services display
- [ ] API status shows
- [ ] Stats display
- [ ] Auto-refresh works

### 3. Mobile Features (3 min)
- [ ] PWA installs
- [ ] Biometric option shows
- [ ] Offline queue works
- [ ] Gestures work
- [ ] Bottom nav works

### 4. Monitor Logs (5 min)
```bash
# On Render dashboard
# Check for errors in logs
# Verify no crashes
```

---

## 🐛 Rollback Plan

If issues found:

### Render Dashboard
1. Go to dashboard.render.com
2. Select service
3. Click "Manual Deploy"
4. Select previous deployment
5. Click "Deploy"

### Git Revert
```bash
git revert HEAD
git push origin main
```

---

## 📊 Success Metrics

**Within 1 hour**:
- [ ] No 500 errors
- [ ] Health check passing
- [ ] All features working

**Within 24 hours**:
- [ ] 99%+ uptime
- [ ] <3s page load
- [ ] No user complaints

**Within 1 week**:
- [ ] 10+ new users
- [ ] $100+ revenue
- [ ] 50+ verifications

---

## 🔧 Environment Variables

Verify these are set on Render:

**Required**:
- `DATABASE_URL` - PostgreSQL connection
- `JWT_SECRET_KEY` - JWT signing
- `TEXTVERIFIED_API_KEY` - SMS API
- `TEXTVERIFIED_EMAIL` - SMS API email
- `PAYSTACK_SECRET_KEY` - Payment gateway

**Optional**:
- `GOOGLE_CLIENT_ID` - OAuth
- `SMTP_HOST` - Email
- `SMTP_USER` - Email
- `SMTP_PASSWORD` - Email
- `SENTRY_DSN` - Error tracking
- `REDIS_URL` - Rate limiting

---

## 📞 Support Contacts

**Render Support**: support@render.com  
**TextVerified**: support@textverified.com  
**Paystack**: support@paystack.com

---

## 🎯 Next Actions

After successful deployment:

1. **Monitor** (Day 1-3)
   - Check logs hourly
   - Watch for errors
   - Monitor uptime

2. **Test** (Day 1)
   - Create test verifications
   - Test all payment flows
   - Verify emails work

3. **Optimize** (Week 1)
   - Add Redis if needed
   - Optimize slow queries
   - Enable CDN

4. **Market** (Week 1+)
   - Social media posts
   - SEO optimization
   - Content marketing

---

**Deployment Date**: _____________  
**Deployed By**: _____________  
**Status**: ⏳ Pending
