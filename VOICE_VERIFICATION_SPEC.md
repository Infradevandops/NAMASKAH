# 📞 Voice Verification - Specification

## Overview

Add voice call verification capability alongside SMS verification for services that require phone call authentication.

---

## 🎯 Use Cases

- **Banking apps**: Require voice verification for security
- **Government services**: Voice-only verification
- **Enterprise apps**: Two-factor authentication via call
- **SMS delivery issues**: Fallback when SMS fails
- **User preference**: Some users prefer voice over SMS

---

## 💰 Pricing

| Capability | Price | Notes |
|------------|-------|-------|
| SMS | ₵0.50 | Default, most common |
| Voice | ₵0.75 | 50% premium for voice calls |

**Why higher?** Voice calls cost more from providers and have longer duration.

---

## 🔌 API Changes

### Create Verification (Updated)

```http
POST /verify/create
Authorization: Bearer TOKEN
Content-Type: application/json

{
  "service_name": "whatsapp",
  "capability": "voice"  // "sms" or "voice"
}
```

**Response:**
```json
{
  "id": "12345",
  "service_name": "whatsapp",
  "phone_number": "+1234567890",
  "capability": "voice",
  "status": "pending",
  "cost": 0.75,
  "remaining_credits": 4.25
}
```

### Get Voice Call Details

```http
GET /verify/{verification_id}/voice
Authorization: Bearer TOKEN
```

**Response:**
```json
{
  "verification_id": "12345",
  "phone_number": "+1234567890",
  "capability": "voice",
  "call_status": "completed",
  "call_duration": 45,
  "transcription": "Your verification code is 1 2 3 4 5 6",
  "audio_url": "https://textverified.com/audio/12345.mp3",
  "received_at": "2024-01-15T10:30:00Z"
}
```

---

## 🗄️ Database Changes

### Update `verifications` Table

```sql
ALTER TABLE verifications 
ADD COLUMN capability VARCHAR DEFAULT 'sms';

ALTER TABLE verifications 
ADD COLUMN call_duration INTEGER;

ALTER TABLE verifications 
ADD COLUMN transcription TEXT;

ALTER TABLE verifications 
ADD COLUMN audio_url VARCHAR;
```

---

## 🎨 Frontend Changes

### Service Selection UI

```html
<!-- Add capability toggle -->
<div class="verification-type">
  <label>
    <input type="radio" name="capability" value="sms" checked>
    📱 SMS (₵0.50)
  </label>
  <label>
    <input type="radio" name="capability" value="voice">
    📞 Voice Call (₵0.75)
  </label>
</div>
```

### Voice Call Display

```html
<div class="voice-verification">
  <h3>📞 Voice Call Received</h3>
  <p><strong>Duration:</strong> 45 seconds</p>
  <p><strong>Transcription:</strong> Your verification code is 1 2 3 4 5 6</p>
  <audio controls>
    <source src="https://textverified.com/audio/12345.mp3" type="audio/mpeg">
  </audio>
  <button onclick="copyCode('123456')">Copy Code</button>
</div>
```

### JavaScript Updates

```javascript
async function createVerification(serviceName, capability = 'sms') {
  const response = await fetch('/verify/create', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      service_name: serviceName,
      capability: capability
    })
  });
  return response.json();
}

async function getVoiceCall(verificationId) {
  const response = await fetch(`/verify/${verificationId}/voice`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return response.json();
}
```

---

## 🔧 Backend Implementation

### Updated Verification Model

```python
class Verification(Base):
    __tablename__ = "verifications"
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    service_name = Column(String, nullable=False)
    phone_number = Column(String)
    capability = Column(String, default="sms")  # NEW
    status = Column(String, default="pending")
    verification_code = Column(String)
    cost = Column(Float, default=VERIFICATION_COST)
    call_duration = Column(Integer)  # NEW (seconds)
    transcription = Column(String)  # NEW
    audio_url = Column(String)  # NEW
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime)
```

### Updated Create Endpoint

```python
@app.post("/verify/create", tags=["Verification"])
def create_verification(
    req: CreateVerificationRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Determine cost based on capability
    if req.capability == "voice":
        cost = 0.75
    else:
        cost = 0.50  # SMS default
    
    # Check credits
    if user.credits < cost:
        raise HTTPException(
            status_code=402,
            detail=f"Insufficient credits. Need ₵{cost}, have ₵{user.credits}"
        )
    
    # Deduct credits
    user.credits -= cost
    
    # Create verification with TextVerified
    verification_id = tv_client.create_verification(
        req.service_name,
        req.capability
    )
    details = tv_client.get_verification(verification_id)
    
    verification = Verification(
        id=verification_id,
        user_id=user.id,
        service_name=req.service_name,
        phone_number=details.get("number"),
        capability=req.capability,
        status="pending",
        cost=cost
    )
    db.add(verification)
    db.commit()
    
    return {
        "id": verification.id,
        "service_name": verification.service_name,
        "phone_number": verification.phone_number,
        "capability": verification.capability,
        "status": verification.status,
        "cost": verification.cost,
        "remaining_credits": user.credits
    }
```

### New Voice Endpoint

```python
@app.get("/verify/{verification_id}/voice", tags=["Verification"])
def get_voice_call(
    verification_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verification = db.query(Verification).filter(
        Verification.id == verification_id,
        Verification.user_id == user.id,
        Verification.capability == "voice"
    ).first()
    
    if not verification:
        raise HTTPException(status_code=404, detail="Voice verification not found")
    
    # Get voice call details from TextVerified
    try:
        voice_data = tv_client.get_voice_call(verification_id)
        
        # Update verification with voice data
        verification.call_duration = voice_data.get("duration")
        verification.transcription = voice_data.get("transcription")
        verification.audio_url = voice_data.get("audio_url")
        verification.status = "completed" if voice_data else "pending"
        db.commit()
        
        return {
            "verification_id": verification.id,
            "phone_number": verification.phone_number,
            "capability": "voice",
            "call_status": verification.status,
            "call_duration": verification.call_duration,
            "transcription": verification.transcription,
            "audio_url": verification.audio_url,
            "received_at": verification.completed_at
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### TextVerified Client Update

```python
class TextVerifiedClient:
    # ... existing methods ...
    
    def get_voice_call(self, verification_id: str):
        """Get voice call details"""
        headers = {"Authorization": f"Bearer {self.get_token()}"}
        r = requests.get(
            f"{self.base_url}/api/pub/v2/voice?reservationId={verification_id}",
            headers=headers
        )
        r.raise_for_status()
        data = r.json().get("data", [])
        
        if data:
            call = data[0]
            return {
                "duration": call.get("duration"),
                "transcription": call.get("transcription"),
                "audio_url": call.get("audioUrl"),
                "received_at": call.get("receivedAt")
            }
        return None
```

---

## 📊 Analytics Updates

### Voice vs SMS Metrics

```python
@app.get("/analytics/verification-types")
def get_verification_types(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sms_count = db.query(Verification).filter(
        Verification.user_id == user.id,
        Verification.capability == "sms"
    ).count()
    
    voice_count = db.query(Verification).filter(
        Verification.user_id == user.id,
        Verification.capability == "voice"
    ).count()
    
    return {
        "sms": {
            "count": sms_count,
            "percentage": round(sms_count / (sms_count + voice_count) * 100, 1)
        },
        "voice": {
            "count": voice_count,
            "percentage": round(voice_count / (sms_count + voice_count) * 100, 1)
        }
    }
```

---

## 🎨 UI/UX Enhancements

### Capability Badge

```css
.capability-badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.capability-sms {
  background: #3b82f6;
  color: white;
}

.capability-voice {
  background: #10b981;
  color: white;
}
```

### Verification History Display

```html
<div class="verification-item">
  <span class="capability-badge capability-voice">📞 VOICE</span>
  <span>WhatsApp</span>
  <span>+1234567890</span>
  <span>₵0.75</span>
  <span>Completed</span>
</div>
```

---

## 🔔 Notification Updates

### Voice Call Received Email

```html
<h2>📞 Voice Call Received!</h2>
<p>Your voice verification for <strong>WhatsApp</strong> has received a call.</p>
<p><strong>Phone Number:</strong> +1234567890</p>
<p><strong>Duration:</strong> 45 seconds</p>
<p><strong>Transcription:</strong> Your verification code is 1 2 3 4 5 6</p>
<p><a href="https://namaskah.app/verify/12345">Listen to Recording</a></p>
```

---

## 🚀 Implementation Phases

### Phase 1: Backend (3 days)
- [ ] Update Verification model with voice fields
- [ ] Add capability parameter to create endpoint
- [ ] Implement voice call retrieval endpoint
- [ ] Update TextVerified client for voice API
- [ ] Database migration

### Phase 2: Frontend (2 days)
- [ ] Add SMS/Voice toggle to service selection
- [ ] Voice call display component
- [ ] Audio player integration
- [ ] Update verification history UI
- [ ] Capability badges

### Phase 3: Testing (2 days)
- [ ] Test voice verification flow
- [ ] Test audio playback
- [ ] Test transcription display
- [ ] Test pricing calculation
- [ ] Cross-browser audio compatibility

### Phase 4: Documentation (1 day)
- [ ] Update API docs
- [ ] Add voice examples to API_EXAMPLES.md
- [ ] Update README with voice capability
- [ ] User guide for voice verification

---

## 📈 Expected Impact

### User Benefits
- **Flexibility**: Choose SMS or voice based on preference
- **Reliability**: Fallback when SMS fails
- **Compatibility**: Support voice-only services
- **Accessibility**: Audio playback for verification codes

### Business Benefits
- **Revenue**: 50% higher price per voice verification
- **Differentiation**: Competitive advantage over SMS-only services
- **Coverage**: Support more services (voice-required apps)
- **Retention**: Users stay for comprehensive verification options

### Metrics
- **Adoption**: 15-20% of verifications use voice
- **Revenue**: +10% from voice premium pricing
- **Satisfaction**: Higher ratings for flexibility
- **Support**: Fewer "SMS not received" tickets

---

## 🔒 Technical Considerations

### Audio Storage
- Store audio URLs from TextVerified (no local storage needed)
- URLs expire after 7 days (TextVerified policy)
- Display expiry warning to users

### Transcription Accuracy
- Transcription provided by TextVerified
- May have errors (display audio as primary source)
- Add "Listen to verify" disclaimer

### Browser Compatibility
- HTML5 audio player (95%+ browser support)
- Fallback: Direct download link
- Mobile-friendly audio controls

---

**Status**: 📋 Specification Complete - Ready for Implementation  
**Estimated Time**: 1-2 weeks  
**Priority**: Medium (after number rental service)
