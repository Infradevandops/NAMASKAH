# 📱 Number Rental Service - Specification

## Overview

Extend Namaskah SMS to support **long-term number rentals** in addition to one-time verifications.

---

## 🎯 Use Cases

- **Developers**: Testing SMS flows repeatedly
- **Businesses**: Temporary customer support lines
- **Privacy**: Anonymous phone number for services
- **Multi-account**: Managing multiple accounts on same platform

---

## 💰 Pricing Tiers

| Duration | Price | Use Case |
|----------|-------|----------|
| 1 hour | ₵2.00 | Quick testing |
| 6 hours | ₵8.00 | Development session |
| 24 hours | ₵10.00 | Daily testing |
| 7 days | ₵50.00 | Project sprint |
| 30 days | ₵150.00 | Long-term use |

**Savings**: Weekly/monthly plans offer 20-30% discount vs hourly.

---

## 📊 Database Schema

### New Table: `number_rentals`

```sql
CREATE TABLE number_rentals (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    phone_number VARCHAR NOT NULL,
    service_name VARCHAR,
    duration_hours INTEGER NOT NULL,
    cost FLOAT NOT NULL,
    status VARCHAR DEFAULT 'active',  -- active, expired, released
    started_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    released_at TIMESTAMP,
    auto_extend BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_rentals_user ON number_rentals(user_id);
CREATE INDEX idx_rentals_status ON number_rentals(status);
CREATE INDEX idx_rentals_expires ON number_rentals(expires_at);
```

---

## 🔌 API Endpoints

### Create Rental

```http
POST /rentals/create
Authorization: Bearer TOKEN
Content-Type: application/json

{
  "service_name": "whatsapp",
  "duration_hours": 24,
  "auto_extend": false
}
```

**Response:**
```json
{
  "id": "rental_123",
  "phone_number": "+1234567890",
  "duration_hours": 24,
  "cost": 10.0,
  "expires_at": "2024-01-16T10:30:00Z",
  "remaining_credits": 40.0,
  "status": "active"
}
```

### Get Rental Status

```http
GET /rentals/{rental_id}
Authorization: Bearer TOKEN
```

**Response:**
```json
{
  "id": "rental_123",
  "phone_number": "+1234567890",
  "service_name": "whatsapp",
  "status": "active",
  "started_at": "2024-01-15T10:30:00Z",
  "expires_at": "2024-01-16T10:30:00Z",
  "time_remaining": "23h 45m",
  "messages_received": 12
}
```

### Get Rental Messages

```http
GET /rentals/{rental_id}/messages
Authorization: Bearer TOKEN
```

**Response:**
```json
{
  "rental_id": "rental_123",
  "phone_number": "+1234567890",
  "messages": [
    {
      "id": "msg_1",
      "content": "Your code is 123456",
      "received_at": "2024-01-15T11:00:00Z",
      "sender": "WhatsApp"
    }
  ],
  "total_count": 12
}
```

### Extend Rental

```http
POST /rentals/{rental_id}/extend
Authorization: Bearer TOKEN
Content-Type: application/json

{
  "additional_hours": 24
}
```

**Response:**
```json
{
  "id": "rental_123",
  "new_expires_at": "2024-01-17T10:30:00Z",
  "cost": 10.0,
  "remaining_credits": 30.0
}
```

### Release Rental Early

```http
POST /rentals/{rental_id}/release
Authorization: Bearer TOKEN
```

**Response:**
```json
{
  "id": "rental_123",
  "status": "released",
  "refund": 5.0,
  "remaining_credits": 45.0,
  "message": "Refunded ₵5.00 for unused 12 hours"
}
```

### List Active Rentals

```http
GET /rentals/active
Authorization: Bearer TOKEN
```

**Response:**
```json
{
  "rentals": [
    {
      "id": "rental_123",
      "phone_number": "+1234567890",
      "service_name": "whatsapp",
      "expires_at": "2024-01-16T10:30:00Z",
      "time_remaining": "23h 45m"
    }
  ]
}
```

---

## 🎨 Frontend Features

### Rental Dashboard

```
┌─────────────────────────────────────────┐
│ 📱 Active Rentals                       │
├─────────────────────────────────────────┤
│ WhatsApp: +1234567890                   │
│ ⏱️  23h 45m remaining                    │
│ 📨 12 messages received                  │
│ [View Messages] [Extend] [Release]      │
├─────────────────────────────────────────┤
│ Telegram: +9876543210                   │
│ ⏱️  6h 12m remaining                     │
│ 📨 3 messages received                   │
│ [View Messages] [Extend] [Release]      │
└─────────────────────────────────────────┘
```

### Rental Creation Modal

```
┌─────────────────────────────────────────┐
│ 🏠 Rent Phone Number                    │
├─────────────────────────────────────────┤
│ Service: [WhatsApp ▼]                   │
│                                         │
│ Duration:                               │
│ ○ 1 hour    - ₵2.00                     │
│ ○ 6 hours   - ₵8.00                     │
│ ● 24 hours  - ₵10.00 (Best Value)       │
│ ○ 7 days    - ₵50.00 (Save 30%)         │
│ ○ 30 days   - ₵150.00 (Save 38%)        │
│                                         │
│ ☑️ Auto-extend when expiring             │
│                                         │
│ Total: ₵10.00                            │
│ Balance: ₵45.00 → ₵35.00                 │
│                                         │
│ [Cancel] [Rent Number]                  │
└─────────────────────────────────────────┘
```

### Countdown Timer

```javascript
// Real-time countdown
function updateRentalTimer(expiresAt) {
  const remaining = new Date(expiresAt) - new Date();
  const hours = Math.floor(remaining / 3600000);
  const minutes = Math.floor((remaining % 3600000) / 60000);
  return `${hours}h ${minutes}m`;
}
```

---

## 🔔 Notifications

### Expiry Warnings

- **1 hour before**: Email + in-app notification
- **15 minutes before**: Email + in-app notification
- **Expired**: Email notification with option to re-rent

### Email Template

```html
<h2>⏰ Rental Expiring Soon</h2>
<p>Your rented number <strong>+1234567890</strong> for <strong>WhatsApp</strong> expires in <strong>1 hour</strong>.</p>
<p><a href="https://namaskah.app/rentals/rental_123/extend">Extend Rental</a></p>
<p>Current balance: ₵35.00</p>
```

---

## 🤖 Background Jobs

### Expiry Checker (runs every 5 minutes)

```python
async def check_rental_expiry():
    now = datetime.now(timezone.utc)
    
    # Find expiring rentals (1 hour warning)
    expiring_soon = db.query(Rental).filter(
        Rental.status == 'active',
        Rental.expires_at <= now + timedelta(hours=1),
        Rental.expires_at > now,
        Rental.warning_sent == False
    ).all()
    
    for rental in expiring_soon:
        send_expiry_warning(rental)
        rental.warning_sent = True
    
    # Find expired rentals
    expired = db.query(Rental).filter(
        Rental.status == 'active',
        Rental.expires_at <= now
    ).all()
    
    for rental in expired:
        if rental.auto_extend and user.credits >= rental.cost:
            extend_rental(rental)
        else:
            release_rental(rental)
```

---

## 💡 Business Logic

### Refund Calculation

```python
def calculate_refund(rental):
    """Refund 50% of unused time (minimum 1 hour used)"""
    total_hours = rental.duration_hours
    used_hours = (datetime.now(timezone.utc) - rental.started_at).total_seconds() / 3600
    
    if used_hours < 1:
        used_hours = 1  # Minimum 1 hour charge
    
    unused_hours = max(0, total_hours - used_hours)
    hourly_rate = rental.cost / total_hours
    refund = (unused_hours * hourly_rate) * 0.5  # 50% refund
    
    return round(refund, 2)
```

### Auto-Extend Logic

```python
def auto_extend_rental(rental):
    """Extend rental by same duration if credits available"""
    if rental.auto_extend and user.credits >= rental.cost:
        user.credits -= rental.cost
        rental.expires_at += timedelta(hours=rental.duration_hours)
        
        # Create transaction
        create_transaction(
            user_id=rental.user_id,
            amount=-rental.cost,
            description=f"Auto-extended rental {rental.id}"
        )
        
        send_email(user.email, "Rental Auto-Extended", ...)
        return True
    return False
```

---

## 📈 Analytics

### Rental Metrics

```python
@app.get("/analytics/rentals")
def get_rental_analytics(user: User = Depends(get_current_user)):
    return {
        "total_rentals": count_user_rentals(user.id),
        "active_rentals": count_active_rentals(user.id),
        "total_spent_rentals": sum_rental_spending(user.id),
        "average_rental_duration": avg_rental_duration(user.id),
        "most_rented_service": get_popular_rental_service(user.id),
        "total_messages_received": count_rental_messages(user.id)
    }
```

---

## 🚀 Implementation Phases

### Phase 1: Backend (Week 1)
- [ ] Database schema migration
- [ ] Rental CRUD endpoints
- [ ] Pricing logic
- [ ] Refund calculation
- [ ] Background expiry checker

### Phase 2: Frontend (Week 2)
- [ ] Rental creation modal
- [ ] Active rentals dashboard
- [ ] Countdown timers
- [ ] Message viewer
- [ ] Extend/release actions

### Phase 3: Notifications (Week 3)
- [ ] Email templates
- [ ] Expiry warnings (1hr, 15min)
- [ ] Auto-extend logic
- [ ] In-app notifications

### Phase 4: Polish (Week 4)
- [ ] Analytics dashboard
- [ ] Admin rental management
- [ ] Usage reports
- [ ] Performance optimization

---

## 🎯 Success Metrics

- **Adoption**: 30% of users try rentals in first month
- **Revenue**: Rentals generate 40% of total revenue
- **Retention**: Rental users have 3x higher retention
- **Satisfaction**: 4.5+ star rating for rental feature

---

## 🔒 Security Considerations

- Validate rental duration limits (max 30 days)
- Prevent rental abuse (max 5 active rentals per user)
- Rate limit rental creation (10 per hour)
- Secure refund logic against exploitation
- Monitor for unusual rental patterns

---

**Status**: 📋 Specification Complete - Ready for Implementation
