# 🚨 PRODUCTION LOGIN FIX

## Issue Identified
The admin user was created with `is_verified=True` but the User model expects `email_verified=True`. This field name mismatch is causing the TypeError during login.

## Fix Applied
✅ Updated `app/api/setup.py` to use correct field name `email_verified=True`

## Next Steps

### Option 1: Deploy Fix (Recommended)
1. **Commit and push changes**:
   ```bash
   git add app/api/setup.py
   git commit -m "Fix admin user field name mismatch"
   git push origin main
   ```

2. **Render will auto-deploy** (if auto-deploy is enabled)
   - Or manually deploy in Render dashboard

3. **After deployment, recreate admin**:
   ```bash
   curl -X POST https://namaskahsms.onrender.com/setup/create-admin
   ```

### Option 2: Quick Database Fix (Alternative)
If you have direct database access, run:
```sql
UPDATE users SET email_verified = true WHERE email = 'admin@namaskah.app';
```

## Test After Fix
```bash
curl -X POST https://namaskahsms.onrender.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@namaskah.app","password":"Namaskah@Admin2024"}'
```

Should return a JWT token instead of the TypeError.

## Root Cause
- Admin user created with non-existent field `is_verified=True`
- User model has field named `email_verified`
- SQLAlchemy/Pydantic validation fails during authentication
- Results in TypeError: "unexpected keyword argument"

## Status
🔧 **Fix ready for deployment**