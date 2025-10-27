"""Analytics API router for user analytics and reporting."""
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.verification import Verification
from app.models.transaction import Transaction
from app.schemas import AnalyticsResponse

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/usage", response_model=AnalyticsResponse)
def get_user_analytics(
    user_id: str = Depends(get_current_user_id),
    period: int = Query(30, description="Period in days"),
    db: Session = Depends(get_db)
):
    """Get user's usage analytics."""
    start_date = datetime.now(timezone.utc) - timedelta(days=period)
    
    # User verifications
    total_verifications = db.query(Verification).filter(
        Verification.user_id == user_id,
        Verification.created_at >= start_date
    ).count()
    
    completed_verifications = db.query(Verification).filter(
        Verification.user_id == user_id,
        Verification.created_at >= start_date,
        Verification.status == "completed"
    ).count()
    
    success_rate = (completed_verifications / total_verifications * 100) if total_verifications > 0 else 0
    
    # Total spent
    total_spent = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id,
        Transaction.type == "debit",
        Transaction.created_at >= start_date
    ).scalar() or 0
    
    # Popular services
    popular_services = db.query(
        Verification.service_name,
        func.count(Verification.id).label('count')
    ).filter(
        Verification.user_id == user_id,
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
            Verification.user_id == user_id,
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


@router.get("/costs")
def get_cost_analysis(
    user_id: str = Depends(get_current_user_id),
    period: int = Query(30, description="Period in days"),
    db: Session = Depends(get_db)
):
    """Get detailed cost analysis."""
    start_date = datetime.now(timezone.utc) - timedelta(days=period)
    
    # Cost by service
    service_costs = db.query(
        Verification.service_name,
        func.sum(Verification.cost).label('total_cost'),
        func.count(Verification.id).label('count'),
        func.avg(Verification.cost).label('avg_cost')
    ).filter(
        Verification.user_id == user_id,
        Verification.created_at >= start_date
    ).group_by(Verification.service_name).all()
    
    # Monthly spending trend
    monthly_spending = []
    for i in range(6):  # Last 6 months
        month_start = datetime.now(timezone.utc).replace(day=1) - timedelta(days=30*i)
        month_end = month_start + timedelta(days=32)
        month_end = month_end.replace(day=1) - timedelta(days=1)
        
        month_spent = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.type == "debit",
            Transaction.created_at >= month_start,
            Transaction.created_at <= month_end
        ).scalar() or 0
        
        monthly_spending.append({
            "month": month_start.strftime("%Y-%m"),
            "amount": abs(month_spent)
        })
    
    return {
        "service_costs": [
            {
                "service": cost[0],
                "total_cost": float(cost[1] or 0),
                "count": cost[2],
                "avg_cost": float(cost[3] or 0)
            }
            for cost in service_costs
        ],
        "monthly_spending": list(reversed(monthly_spending)),
        "period_days": period
    }


@router.get("/export")
def export_data(
    user_id: str = Depends(get_current_user_id),
    data_type: str = Query("verifications", description="Data type: verifications or transactions"),
    output_format: str = Query("json", description="Format: json or csv"),
    date_from: Optional[datetime] = Query(None, description="Start date"),
    date_to: Optional[datetime] = Query(None, description="End date"),
    db: Session = Depends(get_db)
):
    """Export user data."""
    # Set default date range if not provided
    if not date_from:
        date_from = datetime.now(timezone.utc) - timedelta(days=30)
    if not date_to:
        date_to = datetime.now(timezone.utc)
    
    if data_type == "verifications":
        verifications = db.query(Verification).filter(
            Verification.user_id == user_id,
            Verification.created_at >= date_from,
            Verification.created_at <= date_to
        ).order_by(Verification.created_at.desc()).all()
        
        data = [
            {
                "id": v.id,
                "service_name": v.service_name,
                "phone_number": v.phone_number,
                "status": v.status,
                "cost": v.cost,
                "created_at": v.created_at.isoformat(),
                "completed_at": v.completed_at.isoformat() if v.completed_at else None
            }
            for v in verifications
        ]
    
    elif data_type == "transactions":
        transactions = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.created_at >= date_from,
            Transaction.created_at <= date_to
        ).order_by(Transaction.created_at.desc()).all()
        
        data = [
            {
                "id": t.id,
                "amount": t.amount,
                "type": t.type,
                "description": t.description,
                "created_at": t.created_at.isoformat()
            }
            for t in transactions
        ]
    
    else:
        return {"error": "Invalid data_type. Use 'verifications' or 'transactions'"}
    
    return {
        "data": data,
        "format": output_format,
        "count": len(data),
        "date_range": {
            "from": date_from.isoformat(),
            "to": date_to.isoformat()
        }
    }