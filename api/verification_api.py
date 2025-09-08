#!/usr/bin/env python3
"""
Verification Management API Endpoints
Provides REST API for verification request management with user association
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from database import get_db
from auth.jwt_handler import verify_jwt_token
from services.verification_service import VerificationService
from textverified_client import TextVerifiedClient
from models.user_models import User

# Initialize router and security
router = APIRouter(prefix="/api/verifications", tags=["verifications"])
security = HTTPBearer()

# Pydantic models for request/response
class CreateVerificationRequest(BaseModel):
    service_name: str = Field(..., description="Name of the service to verify")
    capability: str = Field(default="sms", description="Verification capability")

class VerificationResponse(BaseModel):
    id: str
    service_name: str
    phone_number: Optional[str]
    status: str
    verification_code: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
    expires_at: Optional[datetime]

class VerificationListResponse(BaseModel):
    verifications: List[VerificationResponse]
    total_count: int
    page: int
    page_size: int

class VerificationCodesResponse(BaseModel):
    verification_id: str
    messages: List[str]
    extracted_codes: List[str]
    auto_completed: bool

class VerificationStatsResponse(BaseModel):
    period_days: int
    total_verifications: int
    completed_verifications: int
    success_rate: float
    status_breakdown: Dict[str, int]
    service_usage: Dict[str, int]

# Dependency to get current user from JWT token
async def get_current_user(token: str = Depends(security), db: Session = Depends(get_db)) -> User:
    """Extract and validate user from JWT token"""
    try:
        payload = verify_jwt_token(token.credentials)
        user_id = payload.get("user_id")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found or inactive")
        
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid authentication")

# Dependency to get verification service
def get_verification_service(db: Session = Depends(get_db)) -> VerificationService:
    """Get verification service instance"""
    textverified_client = TextVerifiedClient()  # Initialize with config
    return VerificationService(db, textverified_client)

@router.get("", response_model=VerificationListResponse)
async def get_verifications(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    service_name: Optional[str] = Query(None, description="Filter by service name"),
    status: Optional[str] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search query"),
    date_from: Optional[datetime] = Query(None, description="Filter from date"),
    date_to: Optional[datetime] = Query(None, description="Filter to date"),
    current_user: User = Depends(get_current_user),
    verification_service: VerificationService = Depends(get_verification_service)
):
    """
    Get verification history for the authenticated user with filtering and search
    """
    try:
        # Build filters
        filters = {}
        if service_name:
            filters['service_name'] = service_name
        if status:
            filters['status'] = status
        if date_from:
            filters['date_from'] = date_from
        if date_to:
            filters['date_to'] = date_to
        
        # Get verifications based on search or filters
        if search:
            verifications = await verification_service.search_verifications(
                user_id=current_user.id,
                search_query=search,
                filters=filters
            )
        else:
            verifications = await verification_service.get_verification_history(
                user_id=current_user.id,
                filters=filters
            )
        
        # Apply pagination
        total_count = len(verifications)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_verifications = verifications[start_idx:end_idx]
        
        # Convert to response format
        verification_responses = [
            VerificationResponse(
                id=v.id,
                service_name=v.service_name,
                phone_number=v.phone_number,
                status=v.status,
                verification_code=v.verification_code,
                created_at=v.created_at,
                completed_at=v.completed_at,
                expires_at=v.expires_at
            )
            for v in paginated_verifications
        ]
        
        return VerificationListResponse(
            verifications=verification_responses,
            total_count=total_count,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get verifications: {str(e)}")

@router.post("/create", response_model=VerificationResponse)
async def create_verification(
    request: CreateVerificationRequest,
    current_user: User = Depends(get_current_user),
    verification_service: VerificationService = Depends(get_verification_service)
):
    """
    Create a new verification request associated with the authenticated user
    """
    try:
        verification = await verification_service.create_verification(
            user_id=current_user.id,
            service_name=request.service_name,
            capability=request.capability
        )
        
        return VerificationResponse(
            id=verification.id,
            service_name=verification.service_name,
            phone_number=verification.phone_number,
            status=verification.status,
            verification_code=verification.verification_code,
            created_at=verification.created_at,
            completed_at=verification.completed_at,
            expires_at=verification.expires_at
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create verification: {str(e)}")

@router.get("/{verification_id}", response_model=VerificationResponse)
async def get_verification(
    verification_id: str = Path(..., description="Verification ID"),
    current_user: User = Depends(get_current_user),
    verification_service: VerificationService = Depends(get_verification_service)
):
    """
    Get details of a specific verification request
    """
    try:
        verification = await verification_service._get_user_verification(
            user_id=current_user.id,
            verification_id=verification_id
        )
        
        return VerificationResponse(
            id=verification.id,
            service_name=verification.service_name,
            phone_number=verification.phone_number,
            status=verification.status,
            verification_code=verification.verification_code,
            created_at=verification.created_at,
            completed_at=verification.completed_at,
            expires_at=verification.expires_at
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get verification: {str(e)}")

@router.get("/{verification_id}/codes", response_model=VerificationCodesResponse)
async def get_verification_codes(
    verification_id: str = Path(..., description="Verification ID"),
    current_user: User = Depends(get_current_user),
    verification_service: VerificationService = Depends(get_verification_service)
):
    """
    Get SMS messages and automatically extracted verification codes
    """
    try:
        # Get verification to ensure user owns it
        verification = await verification_service._get_user_verification(
            user_id=current_user.id,
            verification_id=verification_id
        )
        
        # Check for messages and extract codes
        messages = await verification_service.check_verification_messages(
            user_id=current_user.id,
            verification_id=verification_id
        )
        
        # Extract codes from all messages
        from services.verification_service import CodeExtractionService
        all_codes = []
        for message in messages:
            codes = CodeExtractionService.extract_verification_codes(
                message, verification.service_name
            )
            all_codes.extend(codes)
        
        # Remove duplicates
        unique_codes = list(set(all_codes))
        
        # Check if verification was auto-completed
        verification_service.db.refresh(verification)
        auto_completed = verification.status == "completed" and verification.verification_code is not None
        
        return VerificationCodesResponse(
            verification_id=verification_id,
            messages=messages,
            extracted_codes=unique_codes,
            auto_completed=auto_completed
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get verification codes: {str(e)}")

@router.delete("/{verification_id}")
async def delete_verification(
    verification_id: str = Path(..., description="Verification ID"),
    current_user: User = Depends(get_current_user),
    verification_service: VerificationService = Depends(get_verification_service)
):
    """
    Cancel/delete a verification request with proper authorization
    """
    try:
        # Verify user owns the verification and cancel it
        success = await verification_service.cancel_verification(
            user_id=current_user.id,
            verification_id=verification_id
        )
        
        if success:
            return {"message": "Verification cancelled successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to cancel verification")
        
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel verification: {str(e)}")

@router.get("/{verification_id}/phone", response_model=Dict[str, str])
async def get_verification_phone(
    verification_id: str = Path(..., description="Verification ID"),
    current_user: User = Depends(get_current_user),
    verification_service: VerificationService = Depends(get_verification_service)
):
    """
    Get the phone number assigned to a verification request
    """
    try:
        phone_number = await verification_service.get_verification_number(
            user_id=current_user.id,
            verification_id=verification_id
        )
        
        return {"phone_number": phone_number}
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get phone number: {str(e)}")

@router.get("/stats/summary", response_model=VerificationStatsResponse)
async def get_verification_statistics(
    period_days: int = Query(30, ge=1, le=365, description="Statistics period in days"),
    current_user: User = Depends(get_current_user),
    verification_service: VerificationService = Depends(get_verification_service)
):
    """
    Get verification statistics for the authenticated user
    """
    try:
        stats = await verification_service.get_verification_statistics(
            user_id=current_user.id,
            period_days=period_days
        )
        
        return VerificationStatsResponse(
            period_days=stats['period_days'],
            total_verifications=stats['total_verifications'],
            completed_verifications=stats['completed_verifications'],
            success_rate=stats['success_rate'],
            status_breakdown=stats['status_breakdown'],
            service_usage=stats['service_usage']
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

@router.get("/export/data")
async def export_verification_data(
    format_type: str = Query("json", regex="^(json|csv)$", description="Export format"),
    service_name: Optional[str] = Query(None, description="Filter by service name"),
    status: Optional[str] = Query(None, description="Filter by status"),
    date_from: Optional[datetime] = Query(None, description="Filter from date"),
    date_to: Optional[datetime] = Query(None, description="Filter to date"),
    current_user: User = Depends(get_current_user),
    verification_service: VerificationService = Depends(get_verification_service)
):
    """
    Export verification data in JSON or CSV format
    """
    try:
        # Build filters
        filters = {}
        if service_name:
            filters['service_name'] = service_name
        if status:
            filters['status'] = status
        if date_from:
            filters['date_from'] = date_from
        if date_to:
            filters['date_to'] = date_to
        
        # Export data
        export_result = await verification_service.export_verification_data(
            user_id=current_user.id,
            format_type=format_type,
            filters=filters
        )
        
        if format_type == "csv":
            from fastapi.responses import Response
            return Response(
                content=export_result['csv_content'],
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=verifications_{current_user.id}_{datetime.now().strftime('%Y%m%d')}.csv"}
            )
        else:
            return export_result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export data: {str(e)}")