"""
Service Management & Optimization Module
Enhanced service categorization, success rate tracking, and intelligent routing
"""

import json
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging

logger = logging.getLogger(__name__)

@dataclass
class ServiceMetrics:
    """Service performance metrics"""
    service_name: str
    success_rate: float
    avg_delivery_time: float  # seconds
    total_attempts: int
    recent_failures: int
    last_success: Optional[datetime]
    carrier_performance: Dict[str, float]  # carrier -> success rate
    peak_hours: List[int]  # hours with best performance

class ServiceOptimizer:
    """Intelligent service optimization and routing"""
    
    def __init__(self, db: Session):
        self.db = db
        self.service_cache = {}
        self.cache_expiry = {}
        
    def load_service_categories(self) -> Dict:
        """Load and enhance service categories"""
        try:
            with open('services_categorized.json', 'r') as f:
                data = json.load(f)
            
            # Add success rate data from database
            enhanced_categories = {}
            for category, services in data.get("categories", {}).items():
                enhanced_services = []
                for service in services:
                    metrics = self.get_service_metrics(service)
                    enhanced_services.append({
                        "name": service,
                        "success_rate": metrics.success_rate,
                        "avg_delivery_time": metrics.avg_delivery_time,
                        "popularity_score": self._calculate_popularity(service)
                    })
                
                # Sort by success rate and popularity
                enhanced_services.sort(
                    key=lambda x: (x["success_rate"], x["popularity_score"]), 
                    reverse=True
                )
                enhanced_categories[category] = enhanced_services
            
            return enhanced_categories
            
        except Exception as e:
            logger.error(f"Failed to load service categories: {e}")
            return {}
    
    def get_service_metrics(self, service_name: str) -> ServiceMetrics:
        """Get comprehensive metrics for a service"""
        cache_key = f"metrics_{service_name}"
        
        # Check cache
        if (cache_key in self.service_cache and 
            cache_key in self.cache_expiry and 
            datetime.now(timezone.utc) < self.cache_expiry[cache_key]):
            return self.service_cache[cache_key]
        
        # Calculate from database
        from main import Verification  # Import here to avoid circular imports
        
        # Get verifications from last 30 days
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        
        verifications = self.db.query(Verification).filter(
            Verification.service_name == service_name,
            Verification.created_at >= thirty_days_ago
        ).all()
        
        if not verifications:
            # Default metrics for new services
            metrics = ServiceMetrics(
                service_name=service_name,
                success_rate=95.0,
                avg_delivery_time=30.0,
                total_attempts=0,
                recent_failures=0,
                last_success=None,
                carrier_performance={},
                peak_hours=list(range(9, 17))  # Default business hours
            )
        else:
            # Calculate actual metrics
            total_attempts = len(verifications)
            successful = [v for v in verifications if v.status == "completed"]
            success_rate = (len(successful) / total_attempts) * 100 if total_attempts > 0 else 0
            
            # Average delivery time (for completed verifications)
            delivery_times = []
            for v in successful:
                if v.completed_at and v.created_at:
                    delivery_time = (v.completed_at - v.created_at).total_seconds()
                    delivery_times.append(delivery_time)
            
            avg_delivery_time = sum(delivery_times) / len(delivery_times) if delivery_times else 30.0
            
            # Recent failures (last 7 days)
            seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
            recent_failures = len([
                v for v in verifications 
                if v.created_at >= seven_days_ago and v.status in ["cancelled", "failed"]
            ])
            
            # Last success
            last_success = None
            if successful:
                last_success = max(v.completed_at for v in successful if v.completed_at)
            
            # Carrier performance
            carrier_performance = {}
            for v in verifications:
                if v.requested_carrier:
                    carrier = v.requested_carrier
                    if carrier not in carrier_performance:
                        carrier_performance[carrier] = {"total": 0, "success": 0}
                    carrier_performance[carrier]["total"] += 1
                    if v.status == "completed":
                        carrier_performance[carrier]["success"] += 1
            
            # Convert to success rates
            for carrier in carrier_performance:
                total = carrier_performance[carrier]["total"]
                success = carrier_performance[carrier]["success"]
                carrier_performance[carrier] = (success / total) * 100 if total > 0 else 0
            
            # Peak hours analysis
            peak_hours = self._analyze_peak_hours(successful)
            
            metrics = ServiceMetrics(
                service_name=service_name,
                success_rate=success_rate,
                avg_delivery_time=avg_delivery_time,
                total_attempts=total_attempts,
                recent_failures=recent_failures,
                last_success=last_success,
                carrier_performance=carrier_performance,
                peak_hours=peak_hours
            )
        
        # Cache for 1 hour
        self.service_cache[cache_key] = metrics
        self.cache_expiry[cache_key] = datetime.now(timezone.utc) + timedelta(hours=1)
        
        return metrics
    
    def _analyze_peak_hours(self, successful_verifications: List) -> List[int]:
        """Analyze which hours have the best success rates"""
        hour_counts = {}
        
        for v in successful_verifications:
            if v.completed_at:
                hour = v.completed_at.hour
                hour_counts[hour] = hour_counts.get(hour, 0) + 1
        
        if not hour_counts:
            return list(range(9, 17))  # Default business hours
        
        # Return top 8 hours
        sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
        return [hour for hour, count in sorted_hours[:8]]
    
    def _calculate_popularity(self, service_name: str) -> float:
        """Calculate service popularity score"""
        from main import Verification
        
        # Count verifications in last 30 days
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        
        count = self.db.query(func.count(Verification.id)).filter(
            Verification.service_name == service_name,
            Verification.created_at >= thirty_days_ago
        ).scalar() or 0
        
        # Normalize to 0-100 scale (log scale for better distribution)
        import math
        return min(100, math.log10(count + 1) * 20)
    
    def recommend_service_alternatives(self, service_name: str, count: int = 3) -> List[Dict]:
        """Recommend alternative services based on category and performance"""
        # Find service category
        categories = self.load_service_categories()
        service_category = None
        
        for category, services in categories.items():
            if any(s["name"] == service_name for s in services):
                service_category = category
                break
        
        if not service_category:
            return []
        
        # Get alternatives from same category
        alternatives = []
        for service in categories[service_category]:
            if service["name"] != service_name:
                alternatives.append({
                    "service_name": service["name"],
                    "success_rate": service["success_rate"],
                    "popularity_score": service["popularity_score"],
                    "category": service_category
                })
        
        # Sort by success rate and return top alternatives
        alternatives.sort(key=lambda x: x["success_rate"], reverse=True)
        return alternatives[:count]
    
    def get_optimal_timing(self, service_name: str) -> Dict:
        """Get optimal timing recommendations for a service"""
        metrics = self.get_service_metrics(service_name)
        
        current_hour = datetime.now(timezone.utc).hour
        is_peak_hour = current_hour in metrics.peak_hours
        
        # Find next peak hour
        next_peak = None
        for hour in sorted(metrics.peak_hours):
            if hour > current_hour:
                next_peak = hour
                break
        
        if next_peak is None and metrics.peak_hours:
            next_peak = min(metrics.peak_hours) + 24  # Next day
        
        return {
            "current_hour_optimal": is_peak_hour,
            "peak_hours": metrics.peak_hours,
            "next_peak_hour": next_peak,
            "estimated_wait_reduction": 30 if is_peak_hour else 0,  # seconds
            "success_rate_boost": 5 if is_peak_hour else 0  # percentage points
        }
    
    def detect_service_issues(self, service_name: str) -> List[Dict]:
        """Detect potential issues with a service"""
        metrics = self.get_service_metrics(service_name)
        issues = []
        
        # Low success rate
        if metrics.success_rate < 85:
            issues.append({
                "type": "low_success_rate",
                "severity": "high" if metrics.success_rate < 70 else "medium",
                "message": f"Success rate is {metrics.success_rate:.1f}% (below 85%)",
                "recommendation": "Consider using alternative services or different carriers"
            })
        
        # High recent failures
        if metrics.recent_failures > 5:
            issues.append({
                "type": "recent_failures",
                "severity": "medium",
                "message": f"{metrics.recent_failures} failures in the last 7 days",
                "recommendation": "Service may be experiencing temporary issues"
            })
        
        # Slow delivery
        if metrics.avg_delivery_time > 120:  # 2 minutes
            issues.append({
                "type": "slow_delivery",
                "severity": "low",
                "message": f"Average delivery time is {metrics.avg_delivery_time:.1f} seconds",
                "recommendation": "Consider using services with faster delivery times"
            })
        
        # No recent successes
        if metrics.last_success and metrics.last_success < datetime.now(timezone.utc) - timedelta(days=7):
            issues.append({
                "type": "no_recent_success",
                "severity": "high",
                "message": "No successful verifications in the last 7 days",
                "recommendation": "Service may be temporarily unavailable"
            })
        
        return issues
    
    def get_service_health_report(self) -> Dict:
        """Generate comprehensive service health report"""
        categories = self.load_service_categories()
        
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_services": 0,
            "healthy_services": 0,
            "degraded_services": 0,
            "failed_services": 0,
            "category_health": {},
            "top_performing": [],
            "needs_attention": []
        }
        
        all_services = []
        
        for category, services in categories.items():
            category_health = {"total": len(services), "healthy": 0, "degraded": 0, "failed": 0}
            
            for service in services:
                service_name = service["name"]
                issues = self.detect_service_issues(service_name)
                
                # Classify service health
                if not issues:
                    health_status = "healthy"
                    category_health["healthy"] += 1
                    report["healthy_services"] += 1
                elif any(issue["severity"] == "high" for issue in issues):
                    health_status = "failed"
                    category_health["failed"] += 1
                    report["failed_services"] += 1
                else:
                    health_status = "degraded"
                    category_health["degraded"] += 1
                    report["degraded_services"] += 1
                
                service_data = {
                    "name": service_name,
                    "category": category,
                    "health_status": health_status,
                    "success_rate": service["success_rate"],
                    "issues": issues
                }
                
                all_services.append(service_data)
                report["total_services"] += 1
            
            report["category_health"][category] = category_health
        
        # Top performing services
        report["top_performing"] = sorted(
            [s for s in all_services if s["health_status"] == "healthy"],
            key=lambda x: x["success_rate"],
            reverse=True
        )[:10]
        
        # Services needing attention
        report["needs_attention"] = [
            s for s in all_services 
            if s["health_status"] in ["degraded", "failed"]
        ]
        
        return report

class SmartServiceRouter:
    """Intelligent service routing based on real-time conditions"""
    
    def __init__(self, optimizer: ServiceOptimizer):
        self.optimizer = optimizer
    
    async def route_verification_request(self, 
                                       preferred_service: str,
                                       user_preferences: Dict,
                                       fallback_count: int = 3) -> Tuple[str, Dict]:
        """Route verification to optimal service"""
        
        # Check primary service health
        issues = self.optimizer.detect_service_issues(preferred_service)
        high_severity_issues = [i for i in issues if i["severity"] == "high"]
        
        if not high_severity_issues:
            # Primary service is healthy
            timing = self.optimizer.get_optimal_timing(preferred_service)
            return preferred_service, {
                "routing_reason": "primary_service_healthy",
                "timing_optimal": timing["current_hour_optimal"],
                "estimated_delivery": 30 + timing.get("estimated_wait_reduction", 0)
            }
        
        # Primary service has issues, find alternatives
        alternatives = self.optimizer.recommend_service_alternatives(
            preferred_service, 
            fallback_count
        )
        
        # Filter alternatives by user preferences
        if user_preferences.get("min_success_rate"):
            min_rate = user_preferences["min_success_rate"]
            alternatives = [a for a in alternatives if a["success_rate"] >= min_rate]
        
        if alternatives:
            best_alternative = alternatives[0]
            return best_alternative["service_name"], {
                "routing_reason": "primary_service_issues",
                "primary_issues": [i["message"] for i in high_severity_issues],
                "alternative_success_rate": best_alternative["success_rate"],
                "estimated_delivery": 45  # Slightly longer for alternative
            }
        
        # No good alternatives, use primary service anyway but warn user
        return preferred_service, {
            "routing_reason": "no_alternatives",
            "warning": "Primary service has issues but no better alternatives available",
            "issues": [i["message"] for i in high_severity_issues],
            "estimated_delivery": 90  # Longer delivery time expected
        }

# Utility functions for integration
def get_service_recommendations(db: Session, user_history: List[str]) -> List[Dict]:
    """Get personalized service recommendations based on user history"""
    optimizer = ServiceOptimizer(db)
    
    # Analyze user's most used services
    service_usage = {}
    for service in user_history:
        service_usage[service] = service_usage.get(service, 0) + 1
    
    recommendations = []
    
    # For each frequently used service, recommend alternatives
    for service, usage_count in sorted(service_usage.items(), key=lambda x: x[1], reverse=True)[:5]:
        alternatives = optimizer.recommend_service_alternatives(service, 2)
        
        for alt in alternatives:
            if alt["success_rate"] > optimizer.get_service_metrics(service).success_rate:
                recommendations.append({
                    "service": alt["service_name"],
                    "reason": f"Better alternative to {service}",
                    "success_rate": alt["success_rate"],
                    "category": alt["category"]
                })
    
    return recommendations[:10]

async def optimize_bulk_verifications(db: Session, 
                                    service_requests: List[str]) -> List[Tuple[str, str]]:
    """Optimize bulk verification requests for better success rates"""
    optimizer = ServiceOptimizer(db)
    router = SmartServiceRouter(optimizer)
    
    optimized_requests = []
    
    for service in service_requests:
        optimal_service, routing_info = await router.route_verification_request(
            service, 
            {"min_success_rate": 90}
        )
        optimized_requests.append((service, optimal_service))
    
    return optimized_requests