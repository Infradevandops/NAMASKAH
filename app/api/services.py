"""Services API router for TextVerified integration."""
from fastapi import APIRouter, HTTPException
from app.services.textverified_service import TextVerifiedService

router = APIRouter(prefix="/verify", tags=["Services"])

@router.get("/services")
async def get_available_services():
    """Get available services from TextVerified."""
    textverified = TextVerifiedService()
    result = await textverified.get_services()
    
    if "error" in result:
        raise HTTPException(status_code=503, detail=result["error"])
    
    # Format services for frontend
    services = result.get("services", [])
    formatted_services = []
    
    for service in services:
        if isinstance(service, dict):
            formatted_services.append({
                "id": service.get("id"),
                "name": service.get("name", "").lower(),
                "display_name": service.get("name", ""),
                "price": service.get("price", 0.50),
                "available": True
            })
    
    return {"services": formatted_services}