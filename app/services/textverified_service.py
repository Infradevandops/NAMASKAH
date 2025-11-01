"""TextVerified API integration service."""
import httpx
from typing import Dict, Any
from app.core.config import settings

class TextVerifiedService:
    def __init__(self):
        self.api_key = settings.textverified_api_key
        self.base_url = "https://www.textverified.com/api"
        
    async def get_services(self) -> Dict[str, Any]:
        """Get available services from TextVerified."""
        # Always try real API first if key exists
        if not self.api_key:
            # Return mock services for testing when API key not configured
            return {
                "services": [
                    {"id": 1, "name": "telegram", "price": 0.50},
                    {"id": 2, "name": "whatsapp", "price": 0.60},
                    {"id": 3, "name": "discord", "price": 0.45},
                    {"id": 4, "name": "instagram", "price": 0.55},
                    {"id": 5, "name": "twitter", "price": 0.50},
                    {"id": 6, "name": "google", "price": 0.65}
                ],
                "note": "Mock services - Configure TEXTVERIFIED_API_KEY for production"
            }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/Services",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=15
                )
                if response.status_code == 200:
                    return {"services": response.json()}
                else:
                    return {"error": f"API returned status {response.status_code}"}
            except Exception as e:
                return {"error": f"API request failed: {str(e)}"}
    
    async def get_number(self, service_id: int, country: str = "US") -> Dict[str, Any]:
        """Get a phone number for verification."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/GetNumber",
                headers={"Authorization": f"Bearer {self.api_key}"},
                params={
                    "service_id": service_id,
                    "country": country
                }
            )
            return response.json()
    
    async def get_sms(self, number_id: str) -> Dict[str, Any]:
        """Get SMS messages for a number."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/GetSMS",
                headers={"Authorization": f"Bearer {self.api_key}"},
                params={
                    "number_id": number_id
                }
            )
            return response.json()
    
    async def cancel_number(self, number_id: str) -> Dict[str, Any]:
        """Cancel a number if no SMS received."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/CancelNumber",
                headers={"Authorization": f"Bearer {self.api_key}"},
                params={
                    "number_id": number_id
                }
            )
            return response.json()
    
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