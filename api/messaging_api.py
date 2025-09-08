#!/usr/bin/env python3
"""
Messaging API for CumApp Platform
Handles SMS sending and receiving functionality
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["messaging"])

class SMSRequest(BaseModel):
    to_number: str
    message: str
    from_number: Optional[str] = None

@router.post("/sms/send")
async def send_sms(request: SMSRequest):
    """Send SMS using configured provider"""
    try:
        # Import here to avoid circular imports
        from main import twilio_client, TWILIO_PHONE_NUMBER
        
        if not twilio_client:
            raise HTTPException(status_code=503, detail="SMS service not configured")
        
        from_number = request.from_number or TWILIO_PHONE_NUMBER
        message = twilio_client.messages.create(
            body=request.message,
            from_=from_number,
            to=request.to_number
        )
        
        logger.info(f"SMS sent to {request.to_number}. Message SID: {message.sid}")
        return {
            "status": "sent",
            "message_sid": message.sid,
            "to": request.to_number,
            "from": from_number,
            "message": "SMS sent successfully"
        }
    except Exception as e:
        logger.error(f"Failed to send SMS: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send SMS: {str(e)}")