"""TextVerified API integration service."""
import httpx
from typing import Dict, Any, Optional
from app.core.config import settings

class TextVerifiedService:
    def __init__(self):
        self.api_key = settings.textverified_api_key
        self.base_url = "https://www.textverified.com/api"
        
    async def get_services(self) -> Dict[str, Any]:
        """Get available services from TextVerified."""
        if not self.api_key:
            return {"error": "TextVerified API key not configured"}
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/Services",
                    params={"bearer": self.api_key}
                )
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": f"API returned status {response.status_code}: {response.text}"}
            except Exception as e:
                return {"error": f"API request failed: {str(e)}"}
    
    async def get_number(self, service_id: int, country: str = "US") -> Dict[str, Any]:
        """Get a phone number for verification."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/GetNumber",
                params={
                    "bearer": self.api_key,
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
                params={
                    "bearer": self.api_key,
                    "number_id": number_id
                }
            )
            return response.json()
    
    async def cancel_number(self, number_id: str) -> Dict[str, Any]:
        """Cancel a number if no SMS received."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/CancelNumber",
                params={
                    "bearer": self.api_key,
                    "number_id": number_id
                }
            )
            return response.json()