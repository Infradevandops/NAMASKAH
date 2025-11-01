"""TextVerified API integration service."""
import httpx
import asyncio
from typing import Dict, Any, Optional, List
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

class TextVerifiedService:
    def __init__(self):
        self.api_key = settings.textverified_api_key
        self.base_url = "https://www.textverified.com/api"
        
    async def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make authenticated request to TextVerified API."""
        if not self.api_key:
            return {"error": "TextVerified API key not configured"}
            
        request_params = {"bearer": self.api_key}
        if params:
            request_params.update(params)
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/{endpoint}",
                    params=request_params,
                    timeout=30
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"TextVerified API error: {response.status_code} - {response.text}")
                    return {"error": f"API returned status {response.status_code}"}
                    
            except Exception as e:
                logger.error(f"TextVerified request failed: {str(e)}")
                return {"error": f"Request failed: {str(e)}"}
    
    async def get_services(self) -> Dict[str, Any]:
        """Get available services from TextVerified."""
        if not self.api_key:
            return {
                "services": [
                    {"id": 1, "name": "telegram", "price": 0.50, "voice_supported": True},
                    {"id": 2, "name": "whatsapp", "price": 0.60, "voice_supported": False},
                    {"id": 3, "name": "discord", "price": 0.45, "voice_supported": True},
                    {"id": 4, "name": "instagram", "price": 0.55, "voice_supported": False},
                    {"id": 5, "name": "twitter", "price": 0.50, "voice_supported": True},
                    {"id": 6, "name": "google", "price": 0.65, "voice_supported": True},
                    {"id": 7, "name": "facebook", "price": 0.55, "voice_supported": False},
                    {"id": 8, "name": "microsoft", "price": 0.60, "voice_supported": True}
                ],
                "note": "Mock services - Configure TEXTVERIFIED_API_KEY for production"
            }
        
        result = await self._make_request("Services")
        if "error" not in result:
            return {"services": result}
        return result
    
    async def get_balance(self) -> Dict[str, Any]:
        """Get account balance."""
        return await self._make_request("GetBalance")
    
    async def get_number(self, service_id: int, country: str = "US", voice: bool = False) -> Dict[str, Any]:
        """Get a phone number for verification."""
        params = {
            "service_id": service_id,
            "country": country
        }
        if voice:
            params["voice"] = "1"
            
        return await self._make_request("GetNumber", params)
    
    async def get_sms(self, number_id: str) -> Dict[str, Any]:
        """Get SMS messages for a number."""
        return await self._make_request("GetSMS", {"number_id": number_id})
    
    async def get_voice(self, number_id: str) -> Dict[str, Any]:
        """Get voice verification for a number."""
        return await self._make_request("GetVoice", {"number_id": number_id})
    
    async def cancel_number(self, number_id: str) -> Dict[str, Any]:
        """Cancel a number if no SMS received."""
        return await self._make_request("CancelNumber", {"number_id": number_id})
    
    async def get_countries(self) -> Dict[str, Any]:
        """Get available countries."""
        return await self._make_request("GetCountries")
    
    async def poll_for_code(self, number_id: str, verification_type: str = "sms", max_attempts: int = 30) -> Dict[str, Any]:
        """Poll for verification code with timeout."""
        for attempt in range(max_attempts):
            if verification_type == "voice":
                result = await self.get_voice(number_id)
            else:
                result = await self.get_sms(number_id)
                
            if "error" not in result and result.get("sms"):
                return {"success": True, "code": result["sms"], "attempts": attempt + 1}
            elif "error" in result:
                return {"success": False, "error": result["error"]}
                
            await asyncio.sleep(2)  # Wait 2 seconds between attempts
            
        return {"success": False, "error": "Timeout waiting for verification code", "attempts": max_attempts}
    
    async def create_verification(self, service_name: str, country: str = "US") -> Dict[str, Any]:
        """Create verification by getting a phone number."""
        # Service name to ID mapping
        service_mapping = {
            "telegram": 1, "whatsapp": 2, "discord": 3, 
            "instagram": 4, "twitter": 5, "google": 6
        }
        
        service_id = service_mapping.get(service_name.lower())
        if not service_id:
            return {"error": f"Service {service_name} not supported"}
        
        # Get phone number from TextVerified
        number_result = await self.get_number(service_id, country)
        
        if "error" in number_result:
            return number_result
        
        return {
            "phone_number": number_result.get("number"),
            "number_id": number_result.get("id"),
            "service_id": service_id,
            "cost": 0.50
        }