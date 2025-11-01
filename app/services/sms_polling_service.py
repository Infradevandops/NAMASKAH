"""Real-time SMS polling service for verification updates."""
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.verification import Verification
from app.services.textverified_service import TextVerifiedService

class SMSPollingService:
    """Background service for polling SMS messages."""
    
    def __init__(self):
        self.textverified = TextVerifiedService()
        self.polling_interval = 5  # seconds
        self.max_poll_duration = 600  # 10 minutes
        self.active_verifications: Dict[str, datetime] = {}
    
    async def start_polling(self, verification_id: str):
        """Start polling for a specific verification."""
        self.active_verifications[verification_id] = datetime.now(timezone.utc)
        
        # Start background polling task
        asyncio.create_task(self._poll_verification(verification_id))
    
    async def _poll_verification(self, verification_id: str):
        """Poll for SMS messages for a verification."""
        start_time = datetime.now(timezone.utc)
        
        while verification_id in self.active_verifications:
            # Check if polling timeout reached
            if (datetime.now(timezone.utc) - start_time).seconds > self.max_poll_duration:
                await self._timeout_verification(verification_id)
                break
            
            try:
                # Check for messages
                messages_result = await self.textverified.get_sms(verification_id)
                
                if messages_result and "messages" in messages_result:
                    messages = messages_result["messages"]
                    if messages:
                        await self._complete_verification(verification_id, messages)
                        break
                
            except Exception as e:
                print(f"Polling error for {verification_id}: {e}")
            
            # Wait before next poll
            await asyncio.sleep(self.polling_interval)
        
        # Clean up
        self.active_verifications.pop(verification_id, None)
    
    async def _complete_verification(self, verification_id: str, messages: List):
        """Mark verification as completed."""
        db = SessionLocal()
        try:
            verification = db.query(Verification).filter(
                Verification.id == verification_id
            ).first()
            
            if verification and verification.status == "pending":
                verification.status = "completed"
                verification.completed_at = datetime.now(timezone.utc)
                db.commit()
                
        finally:
            db.close()
    
    async def _timeout_verification(self, verification_id: str):
        """Handle verification timeout."""
        db = SessionLocal()
        try:
            verification = db.query(Verification).filter(
                Verification.id == verification_id
            ).first()
            
            if verification and verification.status == "pending":
                verification.status = "timeout"
                db.commit()
                
                # Refund user credits
                from app.models.user import User
                user = db.query(User).filter(User.id == verification.user_id).first()
                if user:
                    user.credits += verification.cost
                    db.commit()
                
        finally:
            db.close()
    
    def stop_polling(self, verification_id: str):
        """Stop polling for a verification."""
        self.active_verifications.pop(verification_id, None)

# Global polling service instance
polling_service = SMSPollingService()