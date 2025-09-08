#!/usr/bin/env python3
"""
Phone Number Management API endpoints for CumApp Platform
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from typing import Optional, List
import logging
from decimal import Decimal

from database import get_db
from models.user_models import User, PhoneNumber
from services.phone_number_service import PhoneNumberService
from services.auth_service import get_current_active_user
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/numbers", tags=["phone-numbers"])

# Pydantic models for API
class PhoneNumberSearchRequest(BaseModel):
    country_code: str
    area_code: Optional[str] = None
    capabilities: List[str] = ["sms"]
    limit: int = 20

class PhoneNumberPurchaseRequest(BaseModel):
    phone_number: str
    auto_renew: bool = True

class PhoneNumberRenewalRequest(BaseModel):
    renewal_months: int = 1
    auto_renew: Optional[bool] = None

class AvailableNumberResponse(BaseModel):
    phone_number: str
    country_code: str
    area_code: Optional[str]
    region: str
    provider: str
    monthly_cost: str
    sms_cost_per_message: str
    voice_cost_per_minute: str
    setup_fee: str
    capabilities: List[str]

class OwnedNumberResponse(BaseModel):
    id: str
    phone_number: str
    country_code: str
    area_code: Optional[str]
    region: Optional[str]
    provider: str
    status: str
    monthly_cost: str
    purchased_at: str
    expires_at: Optional[str]
    auto_renew: bool
    total_sms_sent: int
    total_sms_received: int
    monthly_sms_sent: int

class UsageStatsResponse(BaseModel):
    phone_number_id: str
    phone_number: str
    period_start: str
    period_end: str
    usage: dict
    costs: dict
    subscription: dict

# API Endpoints

@router.get("/available/{country_code}")
async def get_available_numbers(
    country_code: str = Path(..., description="Country code (e.g., US, GB, CA)"),
    area_code: Optional[str] = Query(None, description="Area code filter"),
    capabilities: Optional[str] = Query("sms", description="Comma-separated capabilities (sms,voice,mms)"),
    limit: int = Query(20, ge=1, le=100, description="Number of results to return"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get available phone numbers for purchase by country
    """
    try:
        phone_service = PhoneNumberService(db)
        
        # Parse capabilities
        capability_list = [cap.strip() for cap in capabilities.split(",")]
        
        # Search for available numbers
        numbers, total_count = await phone_service.search_available_numbers(
            country_code=country_code.upper(),
            area_code=area_code,
            capabilities=capability_list,
            limit=limit
        )
        
        # Convert to response format
        available_numbers = []
        for number in numbers:
            available_numbers.append(AvailableNumberResponse(
                phone_number=number["phone_number"],
                country_code=number["country_code"],
                area_code=number["area_code"],
                region=number["region"],
                provider=number["provider"],
                monthly_cost=str(number["monthly_cost"]),
                sms_cost_per_message=str(number["sms_cost_per_message"]),
                voice_cost_per_minute=str(number["voice_cost_per_minute"]),
                setup_fee=str(number["setup_fee"]),
                capabilities=number["capabilities"]
            ))
        
        return {
            "success": True,
            "country_code": country_code.upper(),
            "area_code": area_code,
            "total_count": total_count,
            "numbers": available_numbers
        }
        
    except Exception as e:
        logger.error(f"Error getting available numbers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get available numbers"
        )

@router.post("/purchase")
async def purchase_phone_number(
    purchase_request: PhoneNumberPurchaseRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Purchase a phone number with subscription validation
    """
    try:
        phone_service = PhoneNumberService(db)
        
        # Purchase the number
        result = await phone_service.purchase_phone_number(
            user_id=current_user.id,
            phone_number=purchase_request.phone_number,
            auto_renew=purchase_request.auto_renew
        )
        
        if result["success"]:
            phone_number = result["phone_number"]
            
            return {
                "success": True,
                "message": result["message"],
                "transaction_id": result["transaction_id"],
                "phone_number": OwnedNumberResponse(
                    id=phone_number.id,
                    phone_number=phone_number.phone_number,
                    country_code=phone_number.country_code,
                    area_code=phone_number.area_code,
                    region=phone_number.region,
                    provider=phone_number.provider,
                    status=phone_number.status,
                    monthly_cost=phone_number.monthly_cost,
                    purchased_at=phone_number.purchased_at.isoformat(),
                    expires_at=phone_number.expires_at.isoformat() if phone_number.expires_at else None,
                    auto_renew=phone_number.auto_renew,
                    total_sms_sent=phone_number.total_sms_sent,
                    total_sms_received=phone_number.total_sms_received,
                    monthly_sms_sent=phone_number.monthly_sms_sent
                )
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Purchase failed")
            )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error purchasing phone number: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to purchase phone number"
        )

@router.get("/owned")
async def get_owned_numbers(
    include_inactive: bool = Query(False, description="Include inactive numbers"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get phone numbers owned by the current user with usage statistics
    """
    try:
        phone_service = PhoneNumberService(db)
        
        # Get owned numbers
        numbers, total_count = await phone_service.get_owned_numbers(
            user_id=current_user.id,
            include_inactive=include_inactive
        )
        
        # Convert to response format
        owned_numbers = []
        total_monthly_cost = Decimal("0.00")
        active_count = 0
        
        for number in numbers:
            if number.status == "active":
                active_count += 1
                total_monthly_cost += Decimal(number.monthly_cost or "0.00")
            
            owned_numbers.append(OwnedNumberResponse(
                id=number.id,
                phone_number=number.phone_number,
                country_code=number.country_code,
                area_code=number.area_code,
                region=number.region,
                provider=number.provider,
                status=number.status,
                monthly_cost=number.monthly_cost,
                purchased_at=number.purchased_at.isoformat(),
                expires_at=number.expires_at.isoformat() if number.expires_at else None,
                auto_renew=number.auto_renew,
                total_sms_sent=number.total_sms_sent,
                total_sms_received=number.total_sms_received,
                monthly_sms_sent=number.monthly_sms_sent
            ))
        
        return {
            "success": True,
            "total_count": total_count,
            "active_count": active_count,
            "total_monthly_cost": str(total_monthly_cost),
            "numbers": owned_numbers
        }
        
    except Exception as e:
        logger.error(f"Error getting owned numbers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get owned numbers"
        )

@router.put("/{phone_number_id}/renew")
async def renew_phone_number(
    phone_number_id: str = Path(..., description="Phone number ID"),
    renewal_request: PhoneNumberRenewalRequest = PhoneNumberRenewalRequest(),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Renew a phone number subscription
    """
    try:
        phone_service = PhoneNumberService(db)
        
        # Renew the number
        result = await phone_service.renew_phone_number(
            user_id=current_user.id,
            phone_number_id=phone_number_id,
            renewal_months=renewal_request.renewal_months
        )
        
        if result["success"]:
            phone_number = result["phone_number"]
            
            # Update auto_renew if specified
            if renewal_request.auto_renew is not None:
                phone_number.auto_renew = renewal_request.auto_renew
                db.commit()
            
            return {
                "success": True,
                "message": result["message"],
                "transaction_id": result["transaction_id"],
                "total_cost": str(result["total_cost"]),
                "new_expires_at": result["new_expires_at"].isoformat(),
                "phone_number": OwnedNumberResponse(
                    id=phone_number.id,
                    phone_number=phone_number.phone_number,
                    country_code=phone_number.country_code,
                    area_code=phone_number.area_code,
                    region=phone_number.region,
                    provider=phone_number.provider,
                    status=phone_number.status,
                    monthly_cost=phone_number.monthly_cost,
                    purchased_at=phone_number.purchased_at.isoformat(),
                    expires_at=phone_number.expires_at.isoformat() if phone_number.expires_at else None,
                    auto_renew=phone_number.auto_renew,
                    total_sms_sent=phone_number.total_sms_sent,
                    total_sms_received=phone_number.total_sms_received,
                    monthly_sms_sent=phone_number.monthly_sms_sent
                )
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Renewal failed")
            )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error renewing phone number: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to renew phone number"
        )

@router.delete("/{phone_number_id}")
async def cancel_phone_number(
    phone_number_id: str = Path(..., description="Phone number ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Cancel a phone number subscription
    """
    try:
        phone_service = PhoneNumberService(db)
        
        # Cancel the number
        result = await phone_service.cancel_phone_number(
            user_id=current_user.id,
            phone_number_id=phone_number_id
        )
        
        if result["success"]:
            return {
                "success": True,
                "message": result["message"]
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Cancellation failed")
            )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error cancelling phone number: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel phone number"
        )

@router.get("/{phone_number_id}/usage")
async def get_phone_number_usage(
    phone_number_id: str = Path(..., description="Phone number ID"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get usage statistics for a phone number
    """
    try:
        phone_service = PhoneNumberService(db)
        
        # Parse dates if provided
        start_datetime = None
        end_datetime = None
        
        if start_date:
            from datetime import datetime
            start_datetime = datetime.fromisoformat(start_date)
        
        if end_date:
            from datetime import datetime
            end_datetime = datetime.fromisoformat(end_date)
        
        # Get usage statistics
        stats = await phone_service.get_usage_statistics(
            user_id=current_user.id,
            phone_number_id=phone_number_id,
            start_date=start_datetime,
            end_date=end_datetime
        )
        
        return {
            "success": True,
            "phone_number_id": stats["phone_number_id"],
            "phone_number": stats["phone_number"],
            "period_start": stats["period_start"].isoformat(),
            "period_end": stats["period_end"].isoformat(),
            "usage": stats["usage"],
            "costs": {
                "sms_cost": str(stats["costs"]["sms_cost"]),
                "voice_cost": str(stats["costs"]["voice_cost"]),
                "monthly_fee": str(stats["costs"]["monthly_fee"]),
                "total_cost": str(stats["costs"]["total_cost"])
            },
            "subscription": stats["subscription"]
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting usage statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get usage statistics"
        )

@router.get("/countries")
async def get_supported_countries(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get list of supported countries for phone number purchase
    """
    try:
        # Mock supported countries for demo
        countries = [
            {
                "code": "US",
                "name": "United States",
                "flag": "🇺🇸",
                "currency": "USD",
                "available_capabilities": ["sms", "voice", "mms"]
            },
            {
                "code": "GB", 
                "name": "United Kingdom",
                "flag": "🇬🇧",
                "currency": "GBP",
                "available_capabilities": ["sms", "voice"]
            },
            {
                "code": "CA",
                "name": "Canada", 
                "flag": "🇨🇦",
                "currency": "CAD",
                "available_capabilities": ["sms", "voice", "mms"]
            },
            {
                "code": "FR",
                "name": "France",
                "flag": "🇫🇷", 
                "currency": "EUR",
                "available_capabilities": ["sms"]
            },
            {
                "code": "DE",
                "name": "Germany",
                "flag": "🇩🇪",
                "currency": "EUR", 
                "available_capabilities": ["sms"]
            },
            {
                "code": "AU",
                "name": "Australia",
                "flag": "🇦🇺",
                "currency": "AUD",
                "available_capabilities": ["sms", "voice"]
            }
        ]
        
        return {
            "success": True,
            "countries": countries
        }
        
    except Exception as e:
        logger.error(f"Error getting supported countries: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get supported countries"
        )

@router.get("/health")
async def phone_number_health_check():
    """
    Health check for phone number service
    """
    return {
        "status": "healthy",
        "service": "phone_numbers",
        "version": "1.1.0",
        "features": [
            "number_marketplace",
            "number_purchasing",
            "subscription_management",
            "usage_tracking",
            "cost_calculation",
            "multi_provider_support"
        ]
    }