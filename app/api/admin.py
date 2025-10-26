"""Admin API router for user management and system monitoring."""
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.dependencies import get_admin_user_id
from app.models.user import User
from app.models.verification import Verification
from app.models.transaction import Transaction
from app.models.system import SupportTicket
from app.schemas import (
    UserResponse, SuccessResponse, SupportTicketResponse,
    PaginationResponse, AnalyticsResponse
)

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users", response_model=PaginationResponse[UserResponse])
def get_all_users(
    admin_id: str = Depends(get_admin_user_id),
    search: Optional[str] = Query(None, description="Search by email or ID"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db)
):
    """Get all users with pagination and search (admin only)."""
    query = db.query(User)
    
    # Search filter
    if search:
        query = query.filter(
            (User.email.contains(search)) | (User.id.contains(search))
        )
    
    # Get total count
    total = query.count()
    
    # Pagination
    offset = (page - 1) * size
    users = query.order_by(User.created_at.desc()).offset(offset).limit(size).all()
    
    # Calculate pages
    pages = (total + size - 1) // size
    
    return PaginationResponse(
        items=[UserResponse.from_orm(user) for user in users],
        total=total,
        page=page,
        size=size,
        pages=pages
    )


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user_details(
    user_id: str,
    admin_id: str = Depends(get_admin_user_id),
    db: Session = Depends(get_db)
):
    """Get detailed user information (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse.from_orm(user)


@router.post("/users/{user_id}/credits", response_model=SuccessResponse)
def manage_user_credits(
    user_id: str,
    amount: float = Body(..., description="Amount to add or deduct"),
    operation: str = Body(..., description="Operation: add or deduct"),
    admin_id: str = Depends(get_admin_user_id),
    db: Session = Depends(get_db)
):
    """Add or deduct credits from user account (admin only)."""
    if operation not in ["add", "deduct"]:
        raise HTTPException(status_code=400, detail="Operation must be 'add' or 'deduct'")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if operation == "deduct" and user.credits < amount:
        raise HTTPException(status_code=400, detail=f"Insufficient balance. User has {user.credits}")
    
    # Update credits
    if operation == "add":
        user.credits += amount
        transaction_amount = amount
        description = f"Admin added credits"
    else:
        user.credits -= amount
        transaction_amount = -amount
        description = f"Admin deducted credits"
    
    # Create transaction record
    transaction = Transaction(
        user_id=user_id,
        amount=transaction_amount,
        type="credit" if operation == "add" else "debit",
        description=description
    )
    
    db.add(transaction)
    db.commit()
    
    return SuccessResponse(
        message=f"Successfully {operation}ed {amount} credits",
        data={"new_balance": user.credits}
    )


@router.post("/users/{user_id}/suspend", response_model=SuccessResponse)
def suspend_user(
    user_id: str,
    admin_id: str = Depends(get_admin_user_id),
    db: Session = Depends(get_db)
):
    """Suspend user account (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.is_admin:
        raise HTTPException(status_code=403, detail="Cannot suspend admin account")
    
    user.is_active = False
    db.commit()
    
    return SuccessResponse(message=f"User {user.email} suspended")


@router.post("/users/{user_id}/activate", response_model=SuccessResponse)
def activate_user(
    user_id: str,
    admin_id: str = Depends(get_admin_user_id),
    db: Session = Depends(get_db)
):
    """Activate suspended user account (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = True
    db.commit()
    
    return SuccessResponse(message=f"User {user.email} activated")


@router.get("/stats", response_model=AnalyticsResponse)
def get_platform_stats(
    admin_id: str = Depends(get_admin_user_id),
    period: int = Query(7, description="Period in days"),
    db: Session = Depends(get_db)
):
    """Get platform-wide statistics (admin only)."""
    
    start_date = datetime.now(timezone.utc) - timedelta(days=period)
    
    # Total users
    total_users = db.query(User).count()
    new_users = db.query(User).filter(User.created_at >= start_date).count()
    
    # Verifications
    total_verifications = db.query(Verification).filter(
        Verification.created_at >= start_date
    ).count()
    
    completed_verifications = db.query(Verification).filter(
        Verification.created_at >= start_date,
        Verification.status == "completed"
    ).count()
    
    success_rate = (completed_verifications / total_verifications * 100) if total_verifications > 0 else 0
    
    # Revenue
    total_spent = db.query(func.sum(Transaction.amount)).filter(
        Transaction.type == "debit",
        Transaction.created_at >= start_date
    ).scalar() or 0
    
    # Popular services
    popular_services = db.query(
        Verification.service_name,
        func.count(Verification.id).label('count')
    ).filter(
        Verification.created_at >= start_date
    ).group_by(Verification.service_name).order_by(
        func.count(Verification.id).desc()
    ).limit(10).all()
    
    # Daily usage
    daily_usage = []
    for i in range(period):
        day = datetime.now(timezone.utc) - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        day_verifications = db.query(Verification).filter(
            Verification.created_at >= day_start,
            Verification.created_at < day_end
        ).count()
        
        daily_usage.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "count": day_verifications
        })
    
    return AnalyticsResponse(
        total_verifications=total_verifications,
        success_rate=round(success_rate, 1),
        total_spent=abs(total_spent),
        popular_services=[{"service": s[0], "count": s[1]} for s in popular_services],
        daily_usage=list(reversed(daily_usage))
    )


@router.get("/support/tickets", response_model=List[SupportTicketResponse])
def get_support_tickets(
    admin_id: str = Depends(get_admin_user_id),
    ticket_status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, le=100, description="Number of results"),
    db: Session = Depends(get_db)
):
    """Get all support tickets (admin only)."""
    query = db.query(SupportTicket)
    
    if ticket_status:
        query = query.filter(SupportTicket.status == ticket_status)
    
    tickets = query.order_by(SupportTicket.created_at.desc()).limit(limit).all()
    
    return [SupportTicketResponse.from_orm(ticket) for ticket in tickets]


@router.post("/support/{ticket_id}/respond", response_model=SuccessResponse)
async def respond_to_ticket(
    ticket_id: str,
    response_text: str = Body(..., description="Admin response to the ticket"),
    admin_id: str = Depends(get_admin_user_id),
    db: Session = Depends(get_db)
):
    """Respond to support ticket (admin only)."""
    from app.services import get_notification_service
    
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Update ticket
    ticket.admin_response = response_text
    ticket.status = "resolved"
    ticket.updated_at = datetime.now(timezone.utc)
    db.commit()
    
    # Send response email
    notification_service = get_notification_service(db)
    await notification_service.send_email(
        to_email=ticket.email,
        subject=f"Re: Support Request #{ticket.id} - Namaskah SMS",
        body=f"""
        <h2>Support Response</h2>
        <p>Hi {ticket.name},</p>
        <p>We've reviewed your support request regarding <strong>{ticket.category}</strong>.</p>
        <p><strong>Your Message:</strong></p>
        <p>{ticket.message}</p>
        <p><strong>Our Response:</strong></p>
        <p>{response_text}</p>
        <p>If you need further assistance, please reply to this email.</p>
        <p>Best regards,<br>Namaskah Support Team</p>
        """
    )
    
    return SuccessResponse(message="Response sent successfully")


@router.get("/verifications/active")
def get_active_verifications(
    admin_id: str = Depends(get_admin_user_id),
    limit: int = Query(100, le=500, description="Number of results"),
    db: Session = Depends(get_db)
):
    """Get all active verifications system-wide (admin only)."""
    verifications = db.query(Verification).filter(
        Verification.status == "pending"
    ).order_by(Verification.created_at.desc()).limit(limit).all()
    
    result = []
    for v in verifications:
        user = db.query(User).filter(User.id == v.user_id).first()
        result.append({
            "id": v.id,
            "user_email": user.email if user else "Unknown",
            "service_name": v.service_name,
            "phone_number": v.phone_number,
            "cost": v.cost,
            "created_at": v.created_at.isoformat()
        })
    
    return {"verifications": result, "total_count": len(result)}


@router.post("/verifications/{verification_id}/cancel", response_model=SuccessResponse)
async def admin_cancel_verification(
    verification_id: str,
    admin_id: str = Depends(get_admin_user_id),
    db: Session = Depends(get_db)
):
    """Cancel any verification and refund user (admin only)."""
    from app.services import get_textverified_service
    
    verification = db.query(Verification).filter(Verification.id == verification_id).first()
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")
    
    if verification.status == "cancelled":
        raise HTTPException(status_code=400, detail="Already cancelled")
    
    # Cancel with TextVerified
    textverified_service = get_textverified_service(db)
    try:
        await textverified_service.cancel_verification(verification_id)
    except Exception:
        pass  # Continue with local cancellation
    
    # Refund user
    user = db.query(User).filter(User.id == verification.user_id).first()
    if user:
        user.credits += verification.cost
        
        # Create refund transaction
        transaction = Transaction(
            user_id=user.id,
            amount=verification.cost,
            type="credit",
            description=f"Admin cancelled verification {verification_id}"
        )
        db.add(transaction)
    
    verification.status = "cancelled"
    db.commit()
    
    return SuccessResponse(
        message="Verification cancelled and refunded",
        data={"refunded": verification.cost}
    )


@router.get("/system/health")
def get_system_health(
    admin_id: str = Depends(get_admin_user_id),
    db: Session = Depends(get_db)
):
    """Get comprehensive system health status (admin only)."""
    # Database health
    try:
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"
    
    # User statistics
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    
    # Verification statistics
    total_verifications = db.query(Verification).count()
    pending_verifications = db.query(Verification).filter(
        Verification.status == "pending"
    ).count()
    
    # Transaction statistics
    total_transactions = db.query(Transaction).count()
    
    return {
        "system_status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "statistics": {
            "total_users": total_users,
            "active_users": active_users,
            "total_verifications": total_verifications,
            "pending_verifications": pending_verifications,
            "total_transactions": total_transactions
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/transactions")
def get_all_transactions(
    admin_id: str = Depends(get_admin_user_id),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    transaction_type: Optional[str] = Query(None, description="Filter by type"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db)
):
    """Get all transactions with filtering (admin only)."""
    query = db.query(Transaction)
    
    # Apply filters
    if user_id:
        query = query.filter(Transaction.user_id == user_id)
    if transaction_type:
        query = query.filter(Transaction.type == transaction_type)
    
    # Get total count
    total = query.count()
    
    # Pagination
    offset = (page - 1) * size
    transactions = query.order_by(Transaction.created_at.desc()).offset(offset).limit(size).all()
    
    # Calculate pages
    pages = (total + size - 1) // size
    
    # Format response
    items = []
    for transaction in transactions:
        user = db.query(User).filter(User.id == transaction.user_id).first()
        items.append({
            "id": transaction.id,
            "user_id": transaction.user_id,
            "user_email": user.email if user else "Unknown",
            "amount": transaction.amount,
            "type": transaction.type,
            "description": transaction.description,
            "created_at": transaction.created_at.isoformat()
        })
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }


@router.post("/broadcast", response_model=SuccessResponse)
async def broadcast_notification(
    title: str = Body(..., description="Notification title"),
    message: str = Body(..., description="Notification message"),
    notification_type: str = Body("info", description="Notification type"),
    target_users: Optional[List[str]] = Body(None, description="Target user IDs (all if empty)"),
    admin_id: str = Depends(get_admin_user_id),
    db: Session = Depends(get_db)
):
    """Broadcast notification to users (admin only)."""
    from app.services import get_notification_service
    
    # Get target users
    if target_users:
        users = db.query(User).filter(User.id.in_(target_users)).all()
    else:
        users = db.query(User).filter(User.is_active == True).all()
    
    if not users:
        raise HTTPException(status_code=404, detail="No target users found")
    
    # Send notifications
    notification_service = get_notification_service(db)
    sent_count = 0
    
    for user in users:
        try:
            await notification_service.send_email(
                to_email=user.email,
                subject=title,
                body=f"""
                <h2>{title}</h2>
                <p>{message}</p>
                <p>Best regards,<br>Namaskah Team</p>
                """
            )
            sent_count += 1
        except Exception:
            continue  # Skip failed sends
    
    return SuccessResponse(
        message=f"Notification sent to {sent_count} users",
        data={"sent_count": sent_count, "total_users": len(users)}
    )