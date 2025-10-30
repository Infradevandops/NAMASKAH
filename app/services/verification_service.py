"""SMS verification service using TextVerified API."""
import asyncio
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.verification import Verification
from app.services.textverified_service import TextVerifiedService
from app.core.database import get_db

class VerificationService:
    def __init__(self):
        self.textverified = TextVerifiedService()
    
    async def create_verification(self, user_id: str, service_name: str, db: Session) -> Dict[str, Any]:
        """Create a new SMS verification."""
        try:
            # Get services to find service_id
            services = await self.textverified.get_services()
            service_id = self._find_service_id(services, service_name)
            
            if not service_id:
                return {"error": "Service not found"}
            
            # Get phone number
            number_result = await self.textverified.get_number(service_id)
            
            if "number" not in number_result:
                return {"error": "Failed to get phone number"}
            
            # Create verification record
            verification = Verification(
                user_id=user_id,
                service_name=service_name,
                phone_number=number_result["number"],
                status="pending",
                cost=0.20  # Default cost
            )
            
            db.add(verification)
            db.commit()
            db.refresh(verification)
            
            return {
                "id": verification.id,
                "phone_number": verification.phone_number,
                "service_name": service_name,
                "status": "pending"
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def get_sms_messages(self, verification_id: str, db: Session) -> Dict[str, Any]:
        """Get SMS messages for a verification."""
        verification = db.query(Verification).filter(Verification.id == verification_id).first()
        
        if not verification:
            return {"error": "Verification not found"}
        
        try:
            # Get SMS from TextVerified
            sms_result = await self.textverified.get_sms(verification_id)
            
            if "sms" in sms_result:
                verification.verification_code = sms_result["sms"]
                verification.status = "completed"
                db.commit()
                
                return {
                    "sms": sms_result["sms"],
                    "status": "completed"
                }
            
            return {"status": "pending", "message": "No SMS received yet"}
            
        except Exception as e:
            return {"error": str(e)}
    
    def _find_service_id(self, services: Dict[str, Any], service_name: str) -> Optional[int]:
        """Find service ID by name."""
        if "services" in services:
            for service in services["services"]:
                if service.get("name", "").lower() == service_name.lower():
                    return service.get("id")
        return None