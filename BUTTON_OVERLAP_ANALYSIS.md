# Button Overlap Analysis

## Identified Overlapping Elements

### Z-Index Hierarchy (Current State)

```
10000 - Cookie Consent Banner (cookie-consent.css)
 2001 - Mobile Menu Drawer (mobile.css)
 2000 - Mobile Menu Overlay (mobile.css)
 2000 - Modal Background (style.css)
 2000 - Loading Spinner (style.css)
 1000 - Bottom Navigation (mobile.css)
 1000 - Notification (style.css)
 1000 - Admin Notification (admin.html inline)
  999 - Pull to Refresh (mobile.css)
  999 - PWA Install Prompt (mobile.css)
  999 - Landing CTA Button (landing.html inline)
  100 - Top Navigation (style.css)
  100 - Landing Hero Section (landing.html inline)
   10 - Landing Improvements (landing-improvements.css)
    1 - Reviews (reviews.html inline)
```

## Overlapping Issues Found

### 1. **PWA Install Prompt vs Bottom Navigation** ⚠️
- **Location**: Mobile devices
- **Issue**: PWA install prompt (z-index: 999) positioned at `bottom: calc(70px + env(safe-area-inset-bottom))` overlaps with bottom navigation (z-index: 1000)
- **Impact**: Install prompt appears behind bottom nav on mobile
- **Fix**: Increase PWA prompt z-index to 1001

### 2. **Pull to Refresh vs Top Navigation** ⚠️
- **Location**: Mobile devices
- **Issue**: Pull to refresh indicator (z-index: 999) at `top: 60px` can overlap with sticky top nav (z-index: 100)
- **Impact**: Visual conflict during pull gesture
- **Fix**: Increase pull-to-refresh z-index to 1001

### 3. **Notification vs Modal** ⚠️
- **Location**: All devices
- **Issue**: Notification (z-index: 1000) appears behind modals (z-index: 2000)
- **Impact**: Users can't see notifications when modal is open
- **Status**: This is actually correct behavior - notifications should be behind modals

### 4. **Landing Page CTA Button** ⚠️
- **Location**: Landing page
- **Issue**: CTA button has z-index: 999 which is lower than notifications (1000)
- **Impact**: Notification can cover CTA button
- **Fix**: Remove inline z-index or increase to 1001

### 5. **Cookie Consent Banner** ✅
- **Location**: All pages
- **Issue**: None - correctly has highest z-index (10000)
- **Status**: Working as intended

## Recommended Z-Index Structure

```
10000 - Cookie Consent (must be on top)
 3000 - Mobile Menu Drawer
 2999 - Mobile Menu Overlay
 2000 - Modals & Loading Spinner
 1500 - Notifications (visible over most UI)
 1001 - PWA Install Prompt
 1001 - Pull to Refresh
 1000 - Bottom Navigation
  500 - Top Navigation (sticky)
  100 - Landing Hero/CTA
   10 - General content layers
    1 - Base content
```

## Files to Fix

1. `static/css/mobile.css` - Lines 85, 241, 312
2. `templates/landing.html` - Line 76
3. `static/css/style.css` - Line 467 (optional)

## Mobile-Specific Issues

### Bottom Navigation Overlap
- Bottom nav adds `padding-bottom: calc(70px + env(safe-area-inset-bottom))` to body
- PWA prompt positioned at same height
- Both compete for same space

### Safe Area Insets
- iPhone notch/home indicator areas properly handled
- No overlap with system UI

## Desktop-Specific Issues

None identified - desktop layout has proper spacing and no fixed overlapping elements.

---

**Priority**: Medium  
**Impact**: Mobile UX  
**Effort**: Low (CSS z-index adjustments)
