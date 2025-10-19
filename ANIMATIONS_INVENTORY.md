# Animations Inventory

## CSS Animations (static/css/)

### style.css
1. **fadeIn** (line 205)
   - Used on: Header elements
   - Duration: 0.5s
   - Effect: Fade from opacity 0 to 1

2. **slideUp** (line 200)
   - Used on: Cards
   - Duration: 0.3s
   - Effect: Slide up from 30px below with fade

3. **slideIn** (line 490)
   - Used on: Notifications
   - Duration: 0.3s
   - Effect: Slide in from right (400px) with fade

4. **spin** (line 518)
   - Used on: Loading spinner
   - Duration: 1s linear infinite
   - Effect: 360° rotation

5. **pulse** (line 523)
   - Used on: Various elements
   - Duration: Variable
   - Effect: Scale and box-shadow pulse

### mobile.css
1. **slideUpModal** (line 44)
   - Used on: Mobile modals
   - Duration: 0.3s
   - Effect: Slide up from bottom (100%)

2. **slideInLeft** (line 267)
   - Used on: Mobile menu items
   - Duration: 0.3s
   - Effect: Slide from left with fade

3. **slideInRight** (line 278)
   - Used on: Mobile menu items
   - Duration: 0.3s
   - Effect: Slide from right with fade

4. **loading** (line 389)
   - Used on: Skeleton loaders
   - Duration: 1.5s infinite
   - Effect: Background gradient shift

5. **spin** (line 251)
   - Used on: Pull-to-refresh indicator
   - Duration: 1s linear infinite
   - Effect: 360° rotation

### cookie-consent.css
1. **slideUp** (line 15)
   - Used on: Cookie banner
   - Duration: 0.4s
   - Effect: Slide up from bottom

### landing-improvements.css
1. **pulse-glow** (line 171)
   - Used on: CTA buttons
   - Duration: 4s infinite
   - Effect: Glow effect with opacity change

## HTML Template Animations (templates/)

### landing.html
1. **slideIn** (line 25)
   - Used on: Feature cards
   - Duration: Variable
   - Effect: Slide from left with fade

2. **phoneRing** (line 29)
   - Used on: Phone icon
   - Duration: Variable
   - Effect: Rotation shake animation

3. **pulse** (line 35)
   - Used on: CTA buttons
   - Duration: 2s infinite
   - Effect: Scale pulse with box-shadow

4. **scroll-left** (line 299)
   - Used on: Announcement banner
   - Duration: 15s linear infinite
   - Effect: Horizontal scroll marquee

5. **float** (line 370)
   - Used on: Floating icons in hero
   - Duration: 6s infinite
   - Effect: Vertical float with rotation

6. **pulse** (circles) (line 392)
   - Used on: Background circles
   - Duration: 4s infinite
   - Effect: Scale and opacity pulse

7. **fadeInUp** (line 612)
   - Used on: Feature cards
   - Duration: 0.6s
   - Effect: Fade in with upward movement
   - Staggered delays: 0.1s, 0.2s, 0.3s, etc.

### index.html
- Uses animations from style.css and mobile.css
- No inline animations defined

## Animation Locations by Page

### Landing Page (/)
- ✅ Announcement banner scroll
- ✅ Hero floating icons (8 icons)
- ✅ Hero background circles (3 circles)
- ✅ CTA button pulse
- ✅ Feature cards fade-in-up (staggered)
- ✅ Logo underline wave animation

### Main App (/app)
- ✅ Card slide-up on load
- ✅ Header fade-in
- ✅ Notification slide-in
- ✅ Loading spinner
- ✅ Mobile modal slide-up
- ✅ Pull-to-refresh spin

### All Pages
- ✅ Cookie consent slide-up
- ✅ Theme toggle transition
- ✅ Button hover effects
- ✅ Skeleton loading (mobile)

## Performance Notes

### Heavy Animations:
1. **Landing page hero** - 11 animated elements simultaneously
   - 8 floating icons
   - 3 pulsing circles
   - Impact: Medium (GPU accelerated)

2. **Announcement banner** - Infinite scroll
   - Impact: Low (transform-based)

3. **Feature cards** - 6 staggered animations
   - Impact: Low (one-time on load)

### Optimized Animations:
- All use `transform` and `opacity` (GPU accelerated)
- No layout-triggering properties (width, height, top, left)
- Proper `will-change` hints where needed

## Animation Triggers

### On Page Load:
- fadeIn (header)
- slideUp (cards)
- fadeInUp (feature cards)

### On User Action:
- slideIn (notifications)
- spin (loading)
- pulse (button hover)

### Continuous:
- scroll-left (banner)
- float (hero icons)
- pulse (circles, CTA)
- pulse-glow (landing CTA)

## Browser Compatibility

All animations use:
- Standard CSS3 animations
- Vendor prefixes where needed (-webkit-)
- Fallback to no animation on older browsers

---

**Total Animations**: 17 unique keyframe animations  
**Most Animated Page**: Landing page (11 simultaneous)  
**Performance Impact**: Low to Medium (all GPU accelerated)
