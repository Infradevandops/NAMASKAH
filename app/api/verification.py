"""Verification API router for SMS/voice verification and number rentals."""
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.services import get_textverified_service, get_notification_service
from app.models.user import User
from app.models.verification import Verification, NumberRental
from app.schemas import (
    VerificationCreate, VerificationResponse, MessageResponse,
    NumberRentalRequest, NumberRentalResponse, ExtendRentalRequest,
    RetryVerificationRequest, VerificationHistoryResponse,
    SuccessResponse, 
)
from app.core.exceptions import InsufficientCreditsError, ExternalServiceError

router = APIRouter(prefix="/verify", tags=["Verification"])


@router.post("/create", response_model=VerificationResponse, status_code=status.HTTP_201_CREATED)
async def create_verification(
    verification_data: VerificationCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Create new SMS or voice verification."""
    textverified_service = get_textverified_service(db)

    # Get user and check credits
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Calculate cost (simplified pricing)
    base_cost = 1.0  # Base cost for SMS
    if verification_data.capability == "voice":
        base_cost += 0.25  # Voice premium
    if verification_data.area_code:
        base_cost += 4.0  # Area code premium
    if verification_data.carrier:
        base_cost += 6.0  # Carrier premium
    
    # Check if user has sufficient credits or free verifications
    if user.free_verifications > 0:
        cost = 0.0
        user.free_verifications -= 1
    elif user.credits >= base_cost:
        cost = base_cost
        user.credits -= cost
    else:
        raise InsufficientCreditsError(f"Insufficient credits. Need {base_cost}, have {user.credits}")
    
    try:
        # Create verification with TextVerified
        verification_id = await textverified_service.create_verification(
            service_name=verification_data.service_name,
            capability=verification_data.capability,
            area_code=verification_data.area_code,
            carrier=verification_data.carrier,
            available=True
        )
        
        # Get verification details
        details = await textverified_service.get_verification_status(verification_id)
        
        # Save verification to database
        verification = Verification(
            id=verification_id,
            user_id=user_id,
            service_name=verification_data.service_name,
            phone_number=details.get("number"),
            capability=verification_data.capability,
            status="pending",
            cost=cost,
            requested_carrier=verification_data.carrier,
            requested_area_code=verification_data.area_code,
            available=True
        )
        
        db.add(verification)
        db.commit()
        db.refresh(verification)
        
        return VerificationResponse.from_orm(verification)
        
    except ExternalServiceError as e:
        # Refund credits if verification creation failed
        if cost > 0:
            user.credits += cost
        else:
            user.free_verifications += 1
        db.commit()
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/{verification_id}", response_model=VerificationResponse)
async def get_verification_status(
    verification_id: str,
    db: Session = Depends(get_db)
):
    """Get verification status (no auth required for public access)."""
    verification = db.query(Verification).filter(Verification.id == verification_id).first()
    
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")
    
    # Update status from TextVerified
    textverified_service = get_textverified_service(db)
    try:
        details = await textverified_service.get_verification_status(verification_id)
        
        new_status = "completed" if details.get("state") == "verificationCompleted" else "pending"
        
        if verification.status == "pending" and new_status == "completed":
            verification.status = "completed"
            verification.completed_at = datetime.now(timezone.utc)
            db.commit()
            
            # Send success notification
            notification_service = get_notification_service(db)
            await notification_service.send_verification_success_notification(
                user_id=verification.user_id,
                verification_id=verification.id,
                service_name=verification.service_name,
                phone_number=verification.phone_number
            )
            return VerificationResponse.from_orm(verification)
    except Exception:
        pass  # Continue with current status if API call fails
    
    return VerificationResponse.from_orm(verification)


@router.get("/{verification_id}/messages", response_model=MessageResponse)
async def get_verification_messages(
    verification_id: str,
    db: Session = Depends(get_db)
):
    """Get SMS messages for verification (no auth required)."""
    verification = db.query(Verification).filter(Verification.id == verification_id).first()
    
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")
    
    textverified_service = get_textverified_service(db)
    try:
        messages = await textverified_service.get_messages(verification_id)
        return MessageResponse(verification_id=verification_id, messages=messages)
    except ExternalServiceError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/{verification_id}/retry", response_model=VerificationResponse)
async def retry_verification(
    verification_id: str,
    retry_data: RetryVerificationRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Retry verification with different options."""
    verification = db.query(Verification).filter(
        Verification.id == verification_id,
        Verification.user_id == user_id
    ).first()
    
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")
    
    textverified_service = get_textverified_service(db)
    
    try:
        if retry_data.retry_type == "voice":
            # Convert to voice verification
            verification.capability = "voice"
            verification.status = "pending"
            db.commit()
            db.refresh(verification)
            return VerificationResponse.from_orm(verification)
            
        elif retry_data.retry_type == "same":
            # Retry with same number
            verification.status = "pending"
            db.commit()
            db.refresh(verification)
            return VerificationResponse.from_orm(verification)
            
        elif retry_data.retry_type == "new":
            # Cancel current and create new
            await textverified_service.cancel_verification(verification_id)
            verification.status = "cancelled"
            
            # Create new verification
            new_verification_id = await textverified_service.create_verification(
                service_name=verification.service_name,
                capability=verification.capability
            )
            
            details = await textverified_service.get_verification_status(new_verification_id)
            
            new_verification = Verification(
                id=new_verification_id,
                user_id=user_id,
                service_name=verification.service_name,
                phone_number=details.get("number"),
                capability=verification.capability,
                status="pending",
                cost=0  # No additional cost for retry
            )
            
            db.add(new_verification)
            db.commit()
            db.refresh(new_verification)
            
            return VerificationResponse.from_orm(new_verification)
        
        db.refresh(verification)
        return VerificationResponse.from_orm(verification)
        
    except ExternalServiceError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.delete("/{verification_id}", response_model=SuccessResponse)
async def cancel_verification(
    verification_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Cancel verification and refund credits."""
    verification = db.query(Verification).filter(
        Verification.id == verification_id,
        Verification.user_id == user_id
    ).first()
    
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")
    
    if verification.status == "cancelled":
        raise HTTPException(status_code=400, detail="Already cancelled")
    
    # Cancel with TextVerified
    textverified_service = get_textverified_service(db)
    try:
        await textverified_service.cancel_verification(verification_id)
    except Exception:
        pass  # Continue with local cancellation even if API call fails
    
    # Refund credits
    user = db.query(User).filter(User.id == user_id).first()
    user.credits += verification.cost
    
    verification.status = "cancelled"
    db.commit()
    
    return SuccessResponse(
        message="Verification cancelled and refunded",
        data={"refunded": verification.cost, "new_balance": user.credits}
    )


@router.get("/history", response_model=VerificationHistoryResponse)
def get_verification_history(
    user_id: str = Depends(get_current_user_id),
    service: Optional[str] = Query(None, description="Filter by service name"),
    verification_status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, le=100, description="Number of results"),
    skip: int = Query(0, description="Number of results to skip"),
    db: Session = Depends(get_db)
):
    """Get user's verification history with filtering."""
    query = db.query(Verification).filter(Verification.user_id == user_id)
    
    if service:
        query = query.filter(Verification.service_name == service)
    if verification_status:
        query = query.filter(Verification.status == verification_status)
    
    total = query.count()
    verifications = query.order_by(Verification.created_at.desc()).offset(skip).limit(limit).all()
    
    return VerificationHistoryResponse(
        verifications=[VerificationResponse.from_orm(v) for v in verifications],
        total_count=total
    )


# Number Rental Endpoints

@router.post("/rentals", response_model=NumberRentalResponse, status_code=status.HTTP_201_CREATED)
async def create_number_rental(
    rental_data: NumberRentalRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Create long-term number rental."""
    # Calculate rental cost (simplified)
    hourly_rate = 0.5  # Base hourly rate
    if rental_data.service_name:
        hourly_rate = 0.6  # Service-specific rate
    if rental_data.mode == "manual":
        hourly_rate *= 0.7  # Manual mode discount
    
    total_cost = rental_data.duration_hours * hourly_rate
    
    # Check user credits
    user = db.query(User).filter(User.id == user_id).first()
    if user.credits < total_cost:
        raise InsufficientCreditsError(f"Insufficient credits. Need {total_cost}, have {user.credits}")
    
    # Deduct credits
    user.credits -= total_cost
    
    # Create rental (simplified - would integrate with TextVerified)
    
    rental = NumberRental(
        user_id=user_id,
        phone_number="+1234567890",  # Would come from TextVerified
        service_name=rental_data.service_name,
        duration_hours=rental_data.duration_hours,
        cost=total_cost,
        mode=rental_data.mode,
        status="active",
        started_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=rental_data.duration_hours),
        auto_extend=rental_data.auto_extend,
        available=False
    )
    
    db.add(rental)
    db.commit()
    db.refresh(rental)
    
    return NumberRentalResponse.from_orm(rental)


@router.get("/rentals", response_model=List[NumberRentalResponse])
def get_user_rentals(
    user_id: str = Depends(get_current_user_id),
    rental_status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db)
):
    """Get user's number rentals."""
    query = db.query(NumberRental).filter(NumberRental.user_id == user_id)
    
    if rental_status:
        query = query.filter(NumberRental.status == rental_status)
    
    rentals = query.order_by(NumberRental.created_at.desc()).all()
    
    return [NumberRentalResponse.from_orm(rental) for rental in rentals]


@router.post("/rentals/{rental_id}/extend", response_model=NumberRentalResponse)
def extend_rental(
    rental_id: str,
    extend_data: ExtendRentalRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Extend rental duration."""
    rental = db.query(NumberRental).filter(
        NumberRental.id == rental_id,
        NumberRental.user_id == user_id
    ).first()
    
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")
    
    if rental.status != "active":
        raise HTTPException(status_code=400, detail="Can only extend active rentals")
    
    # Calculate extension cost
    hourly_rate = rental.cost / rental.duration_hours
    extension_cost = extend_data.additional_hours * hourly_rate
    
    # Check user credits
    user = db.query(User).filter(User.id == user_id).first()
    if user.credits < extension_cost:
        raise InsufficientCreditsError(extension_cost, user.credits)
    
    # Extend rental
    user.credits -= extension_cost
    rental.duration_hours += extend_data.additional_hours
    rental.cost += extension_cost
    rental.expires_at += timedelta(hours=extend_data.additional_hours)
    
    db.commit()
    db.refresh(rental)
    
    return NumberRentalResponse.from_orm(rental)