# Button Layout Reference

## Quick Visual Guide to Button Organization

### 1. User Info Section (Top)
```
┌─────────────────────────────────────────────┐
│ user@email.com                              │
│ Wallet: N10.50                              │
│ 🎁 2 Free Verifications                     │
│                                             │
│ [💰 Fund Wallet]  [💬 Support]             │
└─────────────────────────────────────────────┘
```

---

### 2. Create Verification Section
```
┌─────────────────────────────────────────────┐
│ Create Verification                         │
│                                             │
│ [🏠 Rent Number]  [🌐 Other Service]       │
│                                             │
│ [Search services...]                        │
│                                             │
│ ○ 📱 SMS (N0.50)  ○ 📞 Voice (N0.75)       │
│                                             │
│ [Create Verification]                       │
└─────────────────────────────────────────────┘
```

---

### 3. Verification Details (Active)
```
┌─────────────────────────────────────────────┐
│ Verification Details                        │
│                                             │
│ Phone: +1234567890  [Copy]                  │
│ Service: WhatsApp                           │
│ Status: Pending                             │
│ Time: 60s                                   │
│                                             │
│ ┌─────────────────────────────────────────┐ │
│ │ 📨 Check Messages                       │ │
│ ├──────────────────┬──────────────────────┤ │
│ │ 🔄 Retry         │ ❌ Cancel            │ │
│ └──────────────────┴──────────────────────┘ │
└─────────────────────────────────────────────┘
```

---

### 4. Recent Verifications
```
┌─────────────────────────────────────────────┐
│ Recent Verifications                        │
│                                             │
│ [📄 Export]  [🔄 Refresh]                  │
│                                             │
│ [List of verifications...]                  │
└─────────────────────────────────────────────┘
```

---

### 5. Transaction History
```
┌─────────────────────────────────────────────┐
│ 💳 Transaction History                      │
│                                             │
│ [📄 Export]  [🔄 Refresh]                  │
│                                             │
│ [List of transactions...]                   │
└─────────────────────────────────────────────┘
```

---

### 6. Settings Section
```
┌─────────────────────────────────────────────┐
│ ⚙️ Settings                                 │
│                                             │
│ [🔓 Show Advanced]                          │
│                                             │
│ API keys, webhooks, notifications, support  │
│                                             │
│ ┌─────────────────────────────────────────┐ │
│ │ 📱 Install App                          │ │
│ │ Install for faster access               │ │
│ │ [⬇️ Install Now]                        │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ ┌─────────────────────────────────────────┐ │
│ │ 💬 Support                              │ │
│ │ Need help? Contact support              │ │
│ │ [Contact Support]                       │ │
│ └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

---

## Button Priority Order

### Primary Actions (First/Left)
1. **Create** - Main action
2. **Export** - Data export
3. **Rent** - Premium feature
4. **Fund** - Add money
5. **Install** - PWA install

### Secondary Actions (Second/Right)
1. **Refresh** - Reload data
2. **Support** - Get help
3. **Other** - Alternative options
4. **Cancel** - Abort action
5. **Hide** - Collapse section

---

## Color Scheme

| Color | Hex | Usage |
|-------|-----|-------|
| 🟢 Green | #10b981 | Positive (Fund, Export) |
| 🔵 Blue | #667eea | Primary (Support, Settings) |
| 🟣 Purple | #8b5cf6 | Special (Rent) |
| 🟠 Orange | #f59e0b | Alternative (Other Service) |
| 🔴 Red | #ef4444 | Destructive (Cancel, Hide) |
| ⚫ Gray | #6b7280 | Neutral (Disabled) |

---

## Icon Reference

| Icon | Meaning | Usage |
|------|---------|-------|
| 💰 | Money | Fund Wallet |
| 💬 | Chat | Support |
| 🏠 | Home | Rent Number |
| 🌐 | Globe | Other Service |
| 📱 | Phone | SMS/App |
| 📞 | Call | Voice |
| 📨 | Mail | Check Messages |
| 🔄 | Refresh | Retry/Reload |
| ❌ | Cross | Cancel |
| 📄 | Document | Export |
| ⚙️ | Gear | Settings |
| 🔓 | Unlock | Show |
| 🔒 | Lock | Hide |
| ⬇️ | Down | Install |

---

## Mobile Layout (< 768px)

### Stacked Buttons
```
┌─────────────────┐
│ [Primary Btn]   │
├─────────────────┤
│ [Secondary Btn] │
└─────────────────┘
```

### Grid Layout (Actions)
```
┌─────────────────────────┐
│ [Full Width Button]     │
├────────────┬────────────┤
│ [Button 1] │ [Button 2] │
└────────────┴────────────┘
```

---

## Desktop Layout (> 768px)

### Horizontal Buttons
```
┌──────────────────────────────────┐
│ [Button 1]  [Button 2]  [Button 3] │
└──────────────────────────────────┘
```

### Split Layout
```
┌─────────────────────────────────┐
│ Title          [Btn1]  [Btn2]   │
└─────────────────────────────────┘
```

---

## Accessibility

### Touch Targets
- **Minimum Size:** 44x44px
- **Spacing:** 8px gap between buttons
- **Padding:** 8-16px internal padding

### Visual Feedback
- **Hover:** Slight brightness increase
- **Active:** Scale down (0.98)
- **Disabled:** 50% opacity
- **Focus:** Blue outline

### Haptic Feedback
- **Light:** Button taps
- **Medium:** Important actions
- **Heavy:** Destructive actions

---

## Button States

### Normal
```css
background: #667eea;
color: white;
cursor: pointer;
```

### Hover
```css
background: #5568d3;
transform: translateY(-1px);
```

### Active
```css
transform: scale(0.98);
```

### Disabled
```css
opacity: 0.5;
cursor: not-allowed;
```

### Loading
```css
opacity: 0.7;
cursor: wait;
/* Show spinner */
```

---

## Responsive Breakpoints

| Breakpoint | Width | Layout |
|------------|-------|--------|
| Mobile | < 768px | Stacked |
| Tablet | 768-1024px | Mixed |
| Desktop | > 1024px | Horizontal |

---

## Quick Reference

### Most Common Patterns

**1. Header with Actions**
```html
<div style="display: flex; justify-content: space-between;">
  <h2>Title</h2>
  <div style="display: flex; gap: 8px;">
    <button>Action 1</button>
    <button>Action 2</button>
  </div>
</div>
```

**2. Grid Actions**
```html
<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
  <button style="grid-column: 1 / -1;">Full Width</button>
  <button>Left</button>
  <button>Right</button>
</div>
```

**3. Stacked Buttons**
```html
<div style="display: flex; flex-direction: column; gap: 10px;">
  <button>Button 1</button>
  <button>Button 2</button>
</div>
```

---

**Last Updated:** 2024  
**Version:** 2.4.0  
**Status:** Production Ready ✅
