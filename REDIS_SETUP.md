# Redis Setup for Rate Limiting

## Why Redis?

Redis provides **persistent rate limiting** that survives server restarts, unlike in-memory storage.

## Local Development

### Install Redis

**macOS:**
```bash
brew install redis
brew services start redis
```

**Ubuntu/Debian:**
```bash
sudo apt-get install redis-server
sudo systemctl start redis
```

**Windows:**
```bash
# Use WSL or Docker
docker run -d -p 6379:6379 redis:alpine
```

### Configure

Add to `.env`:
```bash
REDIS_URL=redis://localhost:6379
```

## Production (Render)

### 1. Add Redis Service

1. Go to Render Dashboard
2. Click "New +" → "Redis"
3. Choose **Free tier** (25MB, perfect for rate limiting)
4. Click "Create Redis"

### 2. Get Connection URL

After creation, copy the **Internal Redis URL**:
```
redis://red-xxxxx:6379
```

### 3. Add to Environment Variables

In your web service:
1. Go to "Environment" tab
2. Add variable:
   - Key: `REDIS_URL`
   - Value: `redis://red-xxxxx:6379` (your internal URL)
3. Click "Save Changes"

### 4. Redeploy

Your app will automatically redeploy with Redis rate limiting enabled.

## Verification

Check if Redis is working:

```bash
# Local
redis-cli ping
# Should return: PONG

# In your app logs
# You should NOT see: "Redis not available, using in-memory rate limiting"
```

## Rate Limits

- **100 requests per minute** per user
- Applies to all API endpoints (except static files, health check)
- Persistent across server restarts
- Automatic cleanup of old requests

## Fallback Behavior

If Redis is unavailable:
- App continues to work
- Rate limiting is **disabled** (allows all requests)
- Warning logged: "Redis not available, using in-memory rate limiting"

## Cost

- **Render Free Tier**: $0/month (25MB)
- **Render Starter**: $7/month (256MB)
- **Local Development**: Free

## Testing Rate Limits

```bash
# Test rate limiting
for i in {1..110}; do
  curl -H "Authorization: Bearer YOUR_TOKEN" \
       http://localhost:8000/auth/me
done

# After 100 requests, you should see:
# {"detail": "Rate limit exceeded. Max 100 requests per minute."}
```

## Monitoring

Check Redis usage:
```bash
redis-cli info memory
redis-cli dbsize
```

## Troubleshooting

**"Connection refused"**
- Redis not running: `brew services start redis`
- Wrong URL: Check `REDIS_URL` in `.env`

**"Rate limiting not working"**
- Check logs for "Redis not available"
- Verify Redis connection: `redis-cli ping`
- Restart app after adding `REDIS_URL`

**"Out of memory"**
- Free tier is 25MB (enough for ~1M rate limit entries)
- Upgrade to Starter tier if needed
- Old entries auto-expire after 60 seconds

---

**Status**: ✅ Implemented, ready to deploy
