# Quick Start Guide - Admin Panel

## 🚀 Getting Started

### 1. Start the Server
```bash
cd "Namaskah. app"
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Access Admin Panel
Open your browser and navigate to:
```
http://localhost:8000/admin
```

### 3. Login
**Default Admin Credentials:**
- Email: `admin@namaskah.app`
- Password: `Namaskah@Admin2024`

⚠️ **Change these credentials immediately after first login!**

## 📋 Feature Overview

### User Management
1. **View All Users**: Scroll to "All Users" section
2. **Filter Users**: Use balance filter (High/Medium/Low/Zero)
3. **Search Users**: Type email in search box
4. **Add Credits**: Click "Add Credits" button on any user
5. **Debit Credits**: Use User Account Management section
6. **Suspend/Activate**: Use User Account Management section
7. **Delete User**: Use User Account Management section (⚠️ Permanent!)

### Service Pricing
1. **View Pricing**: Click "View Pricing" in Service Pricing Management
2. **Set Single Price**: 
   - Click "Set Price"
   - Enter service name (e.g., "whatsapp")
   - Enter price (e.g., 1.50)
   - Check "popular" if needed
   - Click "Set Price"
3. **Bulk Update**:
   - Click "Bulk Update"
   - Enter one service per line: `service_name=price`
   - Example:
     ```
     whatsapp=1.00
     telegram=1.00
     instagram=1.25
     ```
   - Click "Update All"

### Verification Management
1. **View Active**: Click "Active Verifications"
2. **Cancel & Refund**: Click "Cancel & Refund" on any verification
3. **View Failed**: Click "Failed" button

### Rental Management
1. **View Active Rentals**: Click "Active Rentals"
2. **Force Release**: Click "Force Release" on any rental
3. **Expiring Soon**: Click "Expiring Soon" for rentals ending within 24h

### System Configuration
1. **View Config**: Click "View Config"
2. **Set Config**:
   - Click "Set Config"
   - Enter key (e.g., "maintenance_mode")
   - Enter value (e.g., "false")
   - Add description (optional)
   - Click "Set Config"

### Support Tickets
1. **View All**: Default view shows all tickets
2. **Filter**: Click "Open" or "Resolved"
3. **Respond**:
   - Click "Respond" on any ticket
   - Type your response
   - Click "Send Response"
   - User receives email automatically

### Analytics & Reports
1. **Change Period**: Use dropdown (7, 14, 30, 60, 90 days, or all time)
2. **View Stats**: See total users, verifications, revenue
3. **Popular Services**: Top 10 services by usage
4. **Success Rate**: Verification completion percentage
5. **Export Data**: Click "Export CSV" for users or transactions

## 🎯 Common Tasks

### Task 1: Add Credits to User
1. Find user in "All Users" section
2. Click "Add Credits" button
3. Enter amount (e.g., 10.00)
4. Click "Add Credits"
5. ✅ User receives credits instantly

### Task 2: Set Custom Price for Service
1. Go to "Service Pricing Management"
2. Click "Set Price"
3. Enter service name: `whatsapp`
4. Enter price: `1.50`
5. Check "Mark as popular service"
6. Click "Set Price"
7. ✅ New price applies to all future verifications

### Task 3: Suspend Problematic User
1. Copy user ID from "All Users" section
2. Go to "User Account Management"
3. Click "Suspend/Activate"
4. Paste user ID
5. Click "Suspend"
6. ✅ User account suspended

### Task 4: Respond to Support Ticket
1. Go to "Support Tickets" section
2. Click "Respond" on ticket
3. Read user's message
4. Type your response
5. Click "Send Response"
6. ✅ User receives email with your response

### Task 5: Cancel Verification & Refund
1. Go to "Verification Management"
2. Click "Active Verifications"
3. Find verification to cancel
4. Click "Cancel & Refund"
5. Confirm action
6. ✅ Verification cancelled, user refunded

## 🔍 Monitoring

### Growth Dashboard
- **User Acquisition**: Track progress to 500 users
- **Monthly Growth**: Average new users per month
- **Months to Target**: Estimated time to reach goal
- **Subscription Rate**: Percentage on paid plans

### Affiliate Program
- **Active Affiliates**: Users earning commissions
- **Total Referrals**: All referred users
- **Commissions Paid**: Total paid to affiliates
- **ROI**: Return on investment percentage
- **Top Affiliates**: Leaderboard of top earners

### Verification Report
- **Successful**: Completed verifications
- **Failed/Cancelled**: Unsuccessful attempts
- **Pending**: Currently active
- **Success Rate**: Percentage completed

## 💡 Tips & Best Practices

### Pricing Strategy
- Popular services (WhatsApp, Telegram, Instagram): N1.00 - N1.25
- General services: N1.25 - N1.50
- Premium services: N1.50 - N2.00
- Voice verification: +N0.25 additional

### User Management
- Monitor high-balance users for fraud
- Suspend suspicious accounts immediately
- Review failed verifications regularly
- Respond to support tickets within 24 hours

### System Health
- Check active verifications daily
- Monitor success rate (target: >90%)
- Review popular services weekly
- Adjust pricing based on demand

### Revenue Optimization
- Analyze popular services
- Set competitive pricing
- Monitor conversion rates
- Track affiliate ROI

## 🚨 Troubleshooting

### Can't Login
- Verify credentials: `admin@namaskah.app` / `Namaskah@Admin2024`
- Check if admin flag is set in database
- Try emergency reset: `POST /emergency-admin-reset?secret=NAMASKAH_EMERGENCY_2024`

### Features Not Loading
- Check browser console for errors
- Verify JWT token is valid
- Refresh page (Ctrl+R or Cmd+R)
- Clear browser cache

### Pricing Not Applying
- Verify service name is lowercase
- Check if custom pricing is set
- Refresh pricing: Click "View Pricing"
- Test with new verification

### Users Not Showing
- Check search filter
- Clear balance filter (set to "All Balances")
- Click "Refresh" button
- Verify database connection

## 📱 Mobile Access

The admin panel is fully responsive and works on mobile devices:
- Touch-friendly buttons (44px minimum)
- Swipeable modals
- Responsive grids
- Mobile-optimized layouts

## 🔐 Security

### Best Practices
- Change default admin password immediately
- Use strong passwords (12+ characters)
- Don't share admin credentials
- Log out when finished
- Monitor admin activity logs

### Access Control
- Only admins can access admin panel
- All actions are logged
- Failed login attempts tracked
- JWT tokens expire after 30 days

## 📊 Keyboard Shortcuts

- `Ctrl/Cmd + R`: Refresh page
- `Ctrl/Cmd + F`: Search users
- `Esc`: Close modals
- `Tab`: Navigate between fields

## 🆘 Support

If you need help:
1. Check this guide first
2. Review `ADMIN_FEATURES.md` for detailed documentation
3. Check server logs for errors
4. Contact technical support

## 📈 Performance Tips

- Use period filters to reduce data load
- Export large datasets to CSV
- Clear browser cache regularly
- Use search instead of scrolling
- Filter users by balance for faster loading

---

**Happy Administrating! 🎉**

Version: 2.2.0  
Last Updated: 2025-01-19
