# PostgreSQL Migration Guide

## Quick Migration (5 minutes)

### Step 1: Create PostgreSQL Database on Render

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"PostgreSQL"**
3. Configure:
   - **Name**: `namaskah-db`
   - **Database**: `namaskah`
   - **User**: `namaskah`
   - **Region**: Same as your web service
   - **Plan**: **Free** (or Starter $7/month)
4. Click **"Create Database"**
5. Wait 2-3 minutes for provisioning

### Step 2: Get Connection URL
postgresql://namaskah:Y5eeFXLVbqmNAx8L6HuP37NtvvjLSMNA@dpg-d3nrteqdbo4c73d8futg-a/namaskah
After creation, copy the **Internal Database URL**:
```
postgresql://namaskah:password@dpg-xxxxx/namaskah
```

### Step 3: Update Environment Variable

1. Go to your **Web Service** on Render
2. Click **"Environment"** tab
3. Find `DATABASE_URL` variable
4. Update value to PostgreSQL URL from Step 2
5. Click **"Save Changes"**

### Step 4: Redeploy

Your app will automatically redeploy and migrate to PostgreSQL.

**Done!** ✅ SQLite → PostgreSQL migration complete.

---

## Verification

Check logs after deployment:
```
INFO:     Application startup complete.
```

Test health endpoint:
```bash
curl https://your-app.onrender.com/health
```

Should return:
```json
{
  "status": "healthy",
  "database": "connected",
  "version": "2.0.0"
}
```

---

## Enable Automated Backups

### Free Tier (Manual Backups)
```bash
# Backup command (run manually)
pg_dump $DATABASE_URL > backup.sql

# Restore command
psql $DATABASE_URL < backup.sql
```

### Paid Tier ($7/month - Recommended)
1. Upgrade to **Starter** plan
2. Automatic daily backups enabled
3. 7-day retention
4. Point-in-time recovery

---

## Rollback (If Needed)

If migration fails, revert to SQLite:

1. Update `DATABASE_URL` to: `sqlite:///./sms.db`
2. Redeploy
3. Check logs for errors

---

## Performance Comparison

| Feature | SQLite | PostgreSQL |
|---------|--------|------------|
| Concurrent writes | ❌ No | ✅ Yes |
| Production ready | ❌ No | ✅ Yes |
| Backups | Manual | Automated |
| Scalability | Limited | Unlimited |
| ACID compliance | Partial | Full |

---

## Troubleshooting

**"Connection refused"**
- Check DATABASE_URL is correct
- Ensure database is in same region as web service

**"Database does not exist"**
- Database name in URL must match created database
- Check spelling: `namaskah` vs `namaskah-db`

**"Too many connections"**
- Free tier: 97 connections max
- Upgrade to Starter for 500 connections

**Data not migrating**
- SQLite data doesn't auto-migrate
- Users will need to re-register (fresh start)
- Or export/import data manually

---

## Cost

- **Free Tier**: $0/month (90 days, then expires)
- **Starter**: $7/month (persistent, backups, 256MB)
- **Standard**: $20/month (1GB, better performance)

**Recommendation**: Start with Free, upgrade to Starter before 90 days.

---

## Next Steps

After PostgreSQL migration:

1. ✅ Enable automated backups (Starter plan)
2. ✅ Set up Redis for rate limiting
3. ✅ Configure Sentry for error tracking
4. ✅ Add monitoring (response times, uptime)

---

**Status**: Ready to migrate  
**Time**: 5 minutes  
**Downtime**: ~30 seconds during redeploy
