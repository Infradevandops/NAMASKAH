"""
API Improvements & Integration Module
Enhanced endpoints, better error handling, and advanced features
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Union
from datetime import datetime, timezone
import asyncio
import json
import csv
import io
from sqlalchemy.orm import Session

# Import our enhanced modules
from textverified_optimization import EnhancedTextVerifiedClient, VerificationRequest, CarrierFilter
from service_optimization import ServiceOptimizer, SmartServiceRouter
from enhanced_pricing import EnhancedPricingEngine, SubscriptionPricingManager
from advanced_analytics import AdvancedAnalytics

# Enhanced request models
class EnhancedVerificationRequest(BaseModel):
    service_name: str = Field(..., description="Service name for verification")
    capability: str = Field("sms", description="Verification type: sms or voice")
    carrier_preference: Optional[str] = Field(None, description="Preferred carrier")
    area_code: Optional[str] = Field(None, description="Preferred area code")
    state: Optional[str] = Field(None, description="Preferred state")
    exclude_voip: bool = Field(True, description="Exclude VOIP numbers")
    priority: bool = Field(False, description="Priority processing")
    webhook_url: Optional[str] = Field(None, description="Webhook URL for notifications")
    
    @validator('service_name')
    def validate_service_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Service name cannot be empty')
        return v.strip().lower()

class BulkVerificationRequest(BaseModel):
    verifications: List[EnhancedVerificationRequest] = Field(..., max_items=10)
    batch_webhook_url: Optional[str] = Field(None, description="Webhook for batch completion")

class SmartVerificationRequest(BaseModel):
    service_name: str
    user_preferences: Dict = Field(default_factory=dict)
    auto_optimize: bool = Field(True, description="Enable automatic optimization")
    fallback_services: List[str] = Field(default_factory=list)

class PricingAnalysisRequest(BaseModel):
    service_name: str
    monthly_usage: int = Field(0, ge=0)
    user_plan: str = Field("starter")
    include_forecast: bool = Field(False)

# Enhanced response models
class EnhancedVerificationResponse(BaseModel):
    id: str
    service_name: str
    phone_number: Optional[str]
    status: str
    cost: float
    estimated_delivery: int  # seconds
    carrier_info: Dict
    location_info: Dict
    routing_info: Dict
    created_at: datetime

class BulkVerificationResponse(BaseModel):
    batch_id: str
    total_requested: int
    successful: int
    failed: int
    verifications: List[Union[EnhancedVerificationResponse, Dict]]
    total_cost: float
    estimated_completion: datetime

class PricingAnalysisResponse(BaseModel):
    current_price: float
    base_price: float
    tier: str
    discounts: List[str]
    surcharges: List[str]
    savings: float
    timing_optimization: Dict
    forecast: Optional[List[Dict]] = None

# Create enhanced API router
enhanced_api = APIRouter(prefix="/api/v2", tags=["Enhanced API"])

@enhanced_api.post("/verify/smart", response_model=EnhancedVerificationResponse)
async def create_smart_verification(
    request: SmartVerificationRequest,
    background_tasks: BackgroundTasks,
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Smart verification with automatic optimization and routing
    
    Features:
    - Automatic service optimization based on success rates
    - Intelligent carrier selection
    - Dynamic pricing
    - Fallback service routing
    """
    
    # Initialize optimization components
    optimizer = ServiceOptimizer(db)
    router = SmartServiceRouter(optimizer)
    pricing_engine = EnhancedPricingEngine()
    
    # Route to optimal service
    optimal_service, routing_info = await router.route_verification_request(
        request.service_name,
        request.user_preferences,
        len(request.fallback_services) or 3
    )
    
    # Get user context for pricing
    user_context = {
        'plan': getattr(user, 'subscription_plan', 'starter'),
        'monthly_count': get_user_monthly_count(user.id, db),
        'success_rate': 95.0  # Could be calculated from user history
    }
    
    # Calculate optimized pricing
    pricing_result = pricing_engine.calculate_dynamic_price(
        service_name=optimal_service,
        user_plan=user_context['plan'],
        monthly_count=user_context['monthly_count'],
        carrier_preference=request.user_preferences.get('carrier_preference'),
        priority=request.user_preferences.get('priority', False)
    )
    
    # Check if user has sufficient credits
    if user.credits < pricing_result.final_price:
        raise HTTPException(
            status_code=402,
            detail=f"Insufficient credits. Need N{pricing_result.final_price}, have N{user.credits}"
        )
    
    # Create enhanced verification request
    carrier_filter = CarrierFilter(
        carrier=request.user_preferences.get('carrier_preference'),
        area_code=request.user_preferences.get('area_code'),
        exclude_voip=request.user_preferences.get('exclude_voip', True)
    )
    
    verification_request = VerificationRequest(
        service_name=optimal_service,
        capability=request.user_preferences.get('capability', 'sms'),
        carrier_filter=carrier_filter,
        priority=request.user_preferences.get('priority', False)
    )
    
    # Create verification using enhanced client
    tv_client = EnhancedTextVerifiedClient(
        api_key=os.getenv("TEXTVERIFIED_API_KEY"),
        email=os.getenv("TEXTVERIFIED_EMAIL")
    )
    
    try:
        verification_id, verification_data = await tv_client.create_verification_enhanced(
            verification_request
        )
        
        # Deduct credits
        user.credits -= pricing_result.final_price
        
        # Create database record
        from main import Verification, Transaction
        
        verification = Verification(
            id=verification_id,
            user_id=user.id,
            service_name=optimal_service,
            phone_number=verification_data.get("phone_number"),
            capability=verification_request.capability,
            status="pending",
            cost=pricing_result.final_price,
            requested_carrier=carrier_filter.carrier,
            requested_area_code=carrier_filter.area_code
        )
        db.add(verification)
        
        # Create transaction
        transaction = Transaction(
            id=f"txn_{datetime.now(timezone.utc).timestamp()}",
            user_id=user.id,
            amount=-pricing_result.final_price,
            type="debit",
            description=f"Smart verification: {optimal_service}"
        )
        db.add(transaction)
        db.commit()
        
        # Schedule background monitoring
        background_tasks.add_task(
            monitor_verification_progress,
            verification_id,
            user.id,
            db
        )
        
        return EnhancedVerificationResponse(
            id=verification_id,
            service_name=optimal_service,
            phone_number=verification_data.get("phone_number"),
            status="pending",
            cost=pricing_result.final_price,
            estimated_delivery=routing_info.get("estimated_delivery", 30),
            carrier_info=verification_data.get("carrier_info", {}),
            location_info=verification_data.get("location_info", {}),
            routing_info=routing_info,
            created_at=datetime.now(timezone.utc)
        )
        
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Verification creation failed: {str(e)}")

@enhanced_api.post("/verify/bulk", response_model=BulkVerificationResponse)
async def create_bulk_verifications(
    request: BulkVerificationRequest,
    background_tasks: BackgroundTasks,
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create multiple verifications efficiently with batch processing
    
    Features:
    - Concurrent processing
    - Batch optimization
    - Partial success handling
    - Cost estimation
    """
    
    if len(request.verifications) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 verifications per batch")
    
    # Initialize components
    tv_client = EnhancedTextVerifiedClient(
        api_key=os.getenv("TEXTVERIFIED_API_KEY"),
        email=os.getenv("TEXTVERIFIED_EMAIL")
    )
    pricing_engine = EnhancedPricingEngine()
    
    # Calculate total cost first
    total_cost = 0
    verification_requests = []
    
    for req in request.verifications:
        # Calculate cost for each verification
        pricing_result = pricing_engine.calculate_dynamic_price(
            service_name=req.service_name,
            user_plan=getattr(user, 'subscription_plan', 'starter'),
            monthly_count=get_user_monthly_count(user.id, db),
            carrier_preference=req.carrier_preference,
            priority=req.priority
        )
        
        total_cost += pricing_result.final_price
        
        # Prepare verification request
        carrier_filter = CarrierFilter(
            carrier=req.carrier_preference,
            area_code=req.area_code,
            state=req.state,
            exclude_voip=req.exclude_voip
        )
        
        verification_requests.append((req, VerificationRequest(
            service_name=req.service_name,
            capability=req.capability,
            carrier_filter=carrier_filter,
            priority=req.priority,
            webhook_url=req.webhook_url
        ), pricing_result.final_price))
    
    # Check total cost
    if user.credits < total_cost:
        raise HTTPException(
            status_code=402,
            detail=f"Insufficient credits for batch. Need N{total_cost}, have N{user.credits}"
        )
    
    # Process bulk verifications
    batch_id = f"batch_{datetime.now(timezone.utc).timestamp()}"
    results = await tv_client.bulk_create_verifications([vr[1] for vr in verification_requests])
    
    successful_verifications = []
    failed_verifications = []
    actual_cost = 0
    
    from main import Verification, Transaction
    
    for i, (result, (original_req, verification_req, cost)) in enumerate(zip(results, verification_requests)):
        if isinstance(result, tuple) and result[0]:  # Successful
            verification_id, verification_data = result
            
            # Create database record
            verification = Verification(
                id=verification_id,
                user_id=user.id,
                service_name=verification_req.service_name,
                phone_number=verification_data.get("phone_number"),
                capability=verification_req.capability,
                status="pending",
                cost=cost
            )
            db.add(verification)
            
            successful_verifications.append(EnhancedVerificationResponse(
                id=verification_id,
                service_name=verification_req.service_name,
                phone_number=verification_data.get("phone_number"),
                status="pending",
                cost=cost,
                estimated_delivery=30,
                carrier_info=verification_data.get("carrier_info", {}),
                location_info=verification_data.get("location_info", {}),
                routing_info={},
                created_at=datetime.now(timezone.utc)
            ))
            
            actual_cost += cost
            
        else:  # Failed
            error_msg = str(result) if isinstance(result, Exception) else "Unknown error"
            failed_verifications.append({
                "service_name": verification_req.service_name,
                "error": error_msg,
                "original_request": original_req.dict()
            })
    
    # Deduct only actual cost
    user.credits -= actual_cost
    
    # Create batch transaction
    if actual_cost > 0:
        transaction = Transaction(
            id=f"txn_{batch_id}",
            user_id=user.id,
            amount=-actual_cost,
            type="debit",
            description=f"Bulk verification batch: {len(successful_verifications)} verifications"
        )
        db.add(transaction)
    
    db.commit()
    
    # Schedule batch monitoring
    if successful_verifications:
        background_tasks.add_task(
            monitor_batch_progress,
            batch_id,
            [v.id for v in successful_verifications],
            user.id,
            request.batch_webhook_url
        )
    
    return BulkVerificationResponse(
        batch_id=batch_id,
        total_requested=len(request.verifications),
        successful=len(successful_verifications),
        failed=len(failed_verifications),
        verifications=successful_verifications + failed_verifications,
        total_cost=actual_cost,
        estimated_completion=datetime.now(timezone.utc) + timedelta(minutes=5)
    )

@enhanced_api.get("/pricing/analysis", response_model=PricingAnalysisResponse)
async def get_pricing_analysis(
    request: PricingAnalysisRequest = Depends(),
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive pricing analysis with optimization recommendations
    """
    
    pricing_engine = EnhancedPricingEngine()
    
    # Get user context
    monthly_count = get_user_monthly_count(user.id, db) if request.monthly_usage == 0 else request.monthly_usage
    
    # Calculate current pricing
    result = pricing_engine.calculate_dynamic_price(
        service_name=request.service_name,
        user_plan=request.user_plan,
        monthly_count=monthly_count
    )
    
    # Get timing optimization
    timing_opt = pricing_engine.optimize_timing_for_cost(request.service_name)
    
    response = PricingAnalysisResponse(
        current_price=result.final_price,
        base_price=result.base_price,
        tier=result.tier.value,
        discounts=result.discounts_applied,
        surcharges=result.surcharges_applied,
        savings=result.savings,
        timing_optimization=timing_opt
    )
    
    # Add forecast if requested
    if request.include_forecast:
        response.forecast = pricing_engine.get_pricing_forecast(request.service_name, 24)
    
    return response

@enhanced_api.get("/analytics/dashboard")
async def get_analytics_dashboard(
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive analytics dashboard
    """
    
    analytics = AdvancedAnalytics(db)
    
    if user.is_admin:
        # Admin gets full dashboard
        return analytics.generate_executive_dashboard()
    else:
        # Regular users get personal analytics
        return get_user_analytics(user.id, db)

@enhanced_api.get("/services/recommendations")
async def get_service_recommendations(
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get personalized service recommendations
    """
    
    # Get user's verification history
    from main import Verification
    
    user_history = db.query(Verification.service_name).filter(
        Verification.user_id == user.id
    ).limit(50).all()
    
    history_list = [v.service_name for v in user_history]
    
    from service_optimization import get_service_recommendations
    recommendations = get_service_recommendations(db, history_list)
    
    return {
        "recommendations": recommendations,
        "based_on_usage": len(history_list),
        "personalized": len(history_list) > 5
    }

@enhanced_api.get("/services/health")
async def get_services_health_report(
    admin = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive service health report (admin only)
    """
    
    optimizer = ServiceOptimizer(db)
    return optimizer.get_service_health_report()

@enhanced_api.post("/verify/{verification_id}/optimize")
async def optimize_existing_verification(
    verification_id: str,
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Optimize an existing verification (retry with better options)
    """
    
    from main import Verification
    
    verification = db.query(Verification).filter(
        Verification.id == verification_id,
        Verification.user_id == user.id
    ).first()
    
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")
    
    if verification.status != "pending":
        raise HTTPException(status_code=400, detail="Can only optimize pending verifications")
    
    # Get optimization recommendations
    optimizer = ServiceOptimizer(db)
    issues = optimizer.detect_service_issues(verification.service_name)
    
    if not issues:
        return {"message": "Verification is already optimal", "issues": []}
    
    # Get alternatives
    alternatives = optimizer.recommend_service_alternatives(verification.service_name, 3)
    
    return {
        "current_service": verification.service_name,
        "issues_detected": [issue["message"] for issue in issues],
        "alternatives": alternatives,
        "recommendation": "Consider switching to an alternative service" if alternatives else "No better alternatives available"
    }

@enhanced_api.get("/export/analytics")
async def export_analytics_report(
    format: str = "json",
    admin = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Export comprehensive analytics report
    """
    
    from advanced_analytics import export_analytics_report
    
    if format not in ["json", "csv"]:
        raise HTTPException(status_code=400, detail="Format must be 'json' or 'csv'")
    
    report_data = export_analytics_report(db, format)
    
    if format == "json":
        return StreamingResponse(
            io.StringIO(report_data),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=analytics_report_{datetime.now().strftime('%Y%m%d')}.json"}
        )
    
    # For CSV format, we'd need to flatten the JSON data
    # This is a simplified version
    return StreamingResponse(
        io.StringIO(report_data),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=analytics_report_{datetime.now().strftime('%Y%m%d')}.csv"}
    )

# Background task functions
async def monitor_verification_progress(verification_id: str, user_id: str, db: Session):
    """Monitor verification progress and send updates"""
    
    tv_client = EnhancedTextVerifiedClient(
        api_key=os.getenv("TEXTVERIFIED_API_KEY"),
        email=os.getenv("TEXTVERIFIED_EMAIL")
    )
    
    max_attempts = 60  # 5 minutes with 5-second intervals
    attempt = 0
    
    while attempt < max_attempts:
        try:
            details = await tv_client.get_verification_details(verification_id)
            
            if details["status"] in ["completed", "failed", "expired", "cancelled"]:
                # Update database
                from main import Verification
                verification = db.query(Verification).filter(Verification.id == verification_id).first()
                if verification:
                    verification.status = details["status"]
                    if details["status"] == "completed":
                        verification.completed_at = datetime.now(timezone.utc)
                    db.commit()
                
                # Send webhook notification if configured
                # This would be implemented based on user's webhook settings
                
                break
            
            await asyncio.sleep(5)  # Wait 5 seconds before next check
            attempt += 1
            
        except Exception as e:
            logger.error(f"Error monitoring verification {verification_id}: {e}")
            await asyncio.sleep(5)
            attempt += 1

async def monitor_batch_progress(batch_id: str, verification_ids: List[str], user_id: str, webhook_url: Optional[str]):
    """Monitor batch verification progress"""
    
    # This would implement batch monitoring logic
    # For now, it's a placeholder
    
    completed_count = 0
    total_count = len(verification_ids)
    
    # Monitor each verification
    tasks = [
        monitor_verification_progress(vid, user_id, SessionLocal())
        for vid in verification_ids
    ]
    
    # Wait for all to complete or timeout
    try:
        await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=300)
    except asyncio.TimeoutError:
        logger.warning(f"Batch {batch_id} monitoring timed out")
    
    # Send batch completion webhook if configured
    if webhook_url:
        # Implementation would send POST request to webhook_url
        pass

# Utility functions
def get_user_monthly_count(user_id: str, db: Session) -> int:
    """Get user's verification count for current month"""
    from main import Verification
    from datetime import datetime, timezone
    
    month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0)
    
    return db.query(Verification).filter(
        Verification.user_id == user_id,
        Verification.created_at >= month_start
    ).count()

def get_user_analytics(user_id: str, db: Session) -> Dict:
    """Get analytics for a specific user"""
    from main import Verification, Transaction
    
    # User's verification history
    verifications = db.query(Verification).filter(
        Verification.user_id == user_id
    ).all()
    
    # Calculate user-specific metrics
    total_verifications = len(verifications)
    successful = len([v for v in verifications if v.status == "completed"])
    success_rate = (successful / total_verifications * 100) if total_verifications > 0 else 0
    
    # Spending analysis
    transactions = db.query(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.type == "debit"
    ).all()
    
    total_spent = sum(abs(t.amount) for t in transactions)
    
    return {
        "total_verifications": total_verifications,
        "success_rate": round(success_rate, 1),
        "total_spent": round(total_spent, 2),
        "avg_cost_per_verification": round(total_spent / total_verifications, 2) if total_verifications > 0 else 0,
        "most_used_services": get_user_top_services(user_id, db)
    }

def get_user_top_services(user_id: str, db: Session) -> List[Dict]:
    """Get user's most used services"""
    from main import Verification
    from sqlalchemy import func
    
    results = db.query(
        Verification.service_name,
        func.count(Verification.id).label('count')
    ).filter(
        Verification.user_id == user_id
    ).group_by(
        Verification.service_name
    ).order_by(
        func.count(Verification.id).desc()
    ).limit(5).all()
    
    return [{"service": r.service_name, "count": r.count} for r in results]