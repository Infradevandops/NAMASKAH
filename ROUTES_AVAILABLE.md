# 🛣️ Available Routes - Namaskah SMS

## **📱 Main Application Routes**

### **Public Pages (No Authentication Required)**
- `GET /` - Landing page with service information
- `GET /app` - Main dashboard/application page
- `GET /services` - List of supported services
- `GET /pricing` - Pricing information
- `GET /about` - About page
- `GET /contact` - Contact information

### **🔐 Authentication Routes (`/auth`)**
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `POST /auth/google` - Google OAuth login
- `GET /auth/me` - Get current user info
- `POST /auth/forgot-password` - Request password reset
- `POST /auth/reset-password` - Reset password with token
- `POST /auth/verify-email` - Verify email address
- `POST /auth/api-keys` - Create API key
- `GET /auth/api-keys` - List user's API keys
- `DELETE /auth/api-keys/{key_id}` - Delete API key

### **📱 SMS Verification Routes (`/verify`)**
- `POST /verify/create` - Create new SMS verification
- `GET /verify/{verification_id}` - Get verification status
- `GET /verify/{verification_id}/messages` - Get SMS messages
- `POST /verify/{verification_id}/retry` - Retry verification
- `DELETE /verify/{verification_id}` - Cancel verification
- `GET /verify/history` - Get verification history
- `POST /verify/rentals` - Create number rental
- `GET /verify/rentals` - Get user rentals
- `POST /verify/rentals/{rental_id}/extend` - Extend rental

### **💰 Wallet & Payment Routes (`/wallet`)**
- `GET /wallet/balance` - Get wallet balance
- `POST /wallet/paystack/initialize` - Initialize payment
- `POST /wallet/paystack/verify` - Verify payment
- `POST /wallet/paystack/webhook` - Payment webhook
- `GET /wallet/transactions` - Transaction history

### **👑 Admin Routes (`/admin`)**
- `GET /admin/users` - List all users
- `GET /admin/users/{user_id}` - Get specific user
- `PUT /admin/users/{user_id}` - Update user
- `DELETE /admin/users/{user_id}` - Delete user
- `GET /admin/stats` - Admin statistics
- `GET /admin/support/tickets` - Support tickets
- `POST /admin/support/tickets/{ticket_id}/respond` - Respond to ticket

### **📊 Analytics Routes (`/analytics`)**
- `GET /analytics/dashboard` - Analytics dashboard
- `GET /analytics/users` - User analytics
- `GET /analytics/revenue` - Revenue analytics
- `GET /analytics/services` - Service usage analytics

### **🏥 System & Health Routes (`/system`)**
- `GET /system/health` - Comprehensive health check
- `GET /system/health/readiness` - Kubernetes readiness probe
- `GET /system/health/liveness` - Kubernetes liveness probe
- `GET /system/status` - Service status summary
- `GET /system/info` - System information
- `GET /system/config` - Public configuration
- `GET /system/metrics` - System metrics
- `GET /system/metrics/business` - Business metrics
- `GET /system/metrics/prometheus` - Prometheus metrics
- `GET /system/metrics/application` - Application metrics

### **📚 Documentation Routes**
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation (ReDoc)
- `GET /openapi.json` - OpenAPI specification

### **📁 Static Files**
- `GET /static/*` - Static files (CSS, JS, images)

## **🔒 Authentication Requirements**

### **No Authentication Required:**
- Landing page (`/`)
- Health checks (`/system/health`)
- Documentation (`/docs`, `/redoc`)
- Static files (`/static/*`)
- Public pages (`/about`, `/contact`, `/pricing`)

### **User Authentication Required:**
- Dashboard (`/app`)
- Verification operations (`/verify/*`)
- Wallet operations (`/wallet/*`)
- User profile (`/auth/me`)
- API key management (`/auth/api-keys`)

### **Admin Authentication Required:**
- Admin panel (`/admin/*`)
- System management
- User management

## **🚨 Common 404 Scenarios**

If you're getting 404 errors, check:

1. **Route exists**: Verify the route is in the list above
2. **Authentication**: Some routes require login
3. **Method**: Ensure you're using the correct HTTP method (GET/POST/PUT/DELETE)
4. **Prefix**: Routes have prefixes (`/auth`, `/verify`, etc.)

## **🔧 Troubleshooting**

### **Route Not Found (404)**
```bash
# Check if route exists
curl https://namaskahsms.onrender.com/system/health

# Check authentication
curl -H "Authorization: Bearer YOUR_TOKEN" https://namaskahsms.onrender.com/auth/me
```

### **Method Not Allowed (405)**
- Check if you're using the correct HTTP method
- POST routes need request body
- GET routes don't accept request body

### **Unauthorized (401)**
- Route requires authentication
- Token might be expired
- Use `/auth/login` to get new token

### **Forbidden (403)**
- Route requires admin privileges
- User doesn't have required permissions

## **📞 Support**

If you encounter issues with any routes:
- Check this documentation first
- Visit `/docs` for interactive API testing
- Contact support via `/contact`
- Check system status at `/system/health`