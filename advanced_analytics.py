"""
Advanced Analytics & Monitoring Module
Real-time analytics, predictive insights, and performance monitoring
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import json
import logging
from collections import defaultdict
import statistics

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for services and system"""

    success_rate: float
    avg_delivery_time: float
    total_volume: int
    revenue: float
    user_satisfaction: float
    peak_hours: List[int]
    failure_reasons: Dict[str, int]


@dataclass
class PredictiveInsight:
    """Predictive analytics insight"""

    metric: str
    prediction: float
    confidence: float
    timeframe: str
    recommendation: str
    impact: str  # high, medium, low


class AdvancedAnalytics:
    """Advanced analytics engine for business intelligence"""

    def __init__(self, db: Session):
        self.db = db
        self.cache = {}
        self.cache_ttl = {}

    def _get_cached_or_compute(
        self, cache_key: str, compute_func, ttl_minutes: int = 30
    ):
        """Get cached result or compute new one"""
        now = datetime.now(timezone.utc)

        if (
            cache_key in self.cache
            and cache_key in self.cache_ttl
            and now < self.cache_ttl[cache_key]
        ):
            return self.cache[cache_key]

        result = compute_func()
        self.cache[cache_key] = result
        self.cache_ttl[cache_key] = now + timedelta(minutes=ttl_minutes)

        return result

    def get_real_time_metrics(self) -> Dict:
        """Get real-time system metrics"""
        from main import Verification, Transaction, User

        now = datetime.now(timezone.utc)
        hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(days=1)

        # Real-time counters
        active_verifications = (
            self.db.query(Verification).filter(Verification.status == "pending").count()
        )

        hourly_verifications = (
            self.db.query(Verification)
            .filter(Verification.created_at >= hour_ago)
            .count()
        )

        hourly_completions = (
            self.db.query(Verification)
            .filter(
                and_(
                    Verification.completed_at >= hour_ago,
                    Verification.status == "completed",
                )
            )
            .count()
        )

        # Success rate (last hour)
        hourly_success_rate = (
            (hourly_completions / hourly_verifications * 100)
            if hourly_verifications > 0
            else 0
        )

        # Revenue (last 24 hours)
        daily_revenue = (
            self.db.query(func.sum(Transaction.amount))
            .filter(
                and_(Transaction.type == "debit", Transaction.created_at >= day_ago)
            )
            .scalar()
            or 0
        )
        daily_revenue = abs(daily_revenue)

        # Active users (last 24 hours)
        active_users = (
            self.db.query(Verification.user_id)
            .filter(Verification.created_at >= day_ago)
            .distinct()
            .count()
        )

        return {
            "timestamp": now.isoformat(),
            "active_verifications": active_verifications,
            "hourly_verifications": hourly_verifications,
            "hourly_success_rate": round(hourly_success_rate, 1),
            "daily_revenue": round(daily_revenue, 2),
            "active_users_24h": active_users,
            "system_health": self._calculate_system_health(),
        }

    def _calculate_system_health(self) -> str:
        """Calculate overall system health score"""
        from main import Verification

        # Check recent success rates and volumes
        hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)

        recent_verifications = (
            self.db.query(Verification)
            .filter(Verification.created_at >= hour_ago)
            .all()
        )

        if not recent_verifications:
            return "healthy"  # No recent activity

        success_count = len(
            [v for v in recent_verifications if v.status == "completed"]
        )
        success_rate = (success_count / len(recent_verifications)) * 100

        if success_rate >= 95:
            return "excellent"
        elif success_rate >= 90:
            return "healthy"
        elif success_rate >= 80:
            return "degraded"
        else:
            return "critical"

    def get_service_performance_analysis(self, days: int = 30) -> Dict:
        """Comprehensive service performance analysis"""
        from main import Verification

        cache_key = f"service_performance_{days}"

        def compute():
            start_date = datetime.now(timezone.utc) - timedelta(days=days)

            # Get all verifications in period
            verifications = (
                self.db.query(Verification)
                .filter(Verification.created_at >= start_date)
                .all()
            )

            # Group by service
            service_metrics = defaultdict(
                lambda: {
                    "total": 0,
                    "completed": 0,
                    "cancelled": 0,
                    "pending": 0,
                    "delivery_times": [],
                    "revenue": 0,
                    "hours": defaultdict(int),
                }
            )

            for v in verifications:
                service = v.service_name
                service_metrics[service]["total"] += 1
                service_metrics[service]["revenue"] += v.cost

                if v.status == "completed":
                    service_metrics[service]["completed"] += 1
                    if v.completed_at and v.created_at:
                        delivery_time = (v.completed_at - v.created_at).total_seconds()
                        service_metrics[service]["delivery_times"].append(delivery_time)
                elif v.status == "cancelled":
                    service_metrics[service]["cancelled"] += 1
                elif v.status == "pending":
                    service_metrics[service]["pending"] += 1

                # Track hourly distribution
                hour = v.created_at.hour
                service_metrics[service]["hours"][hour] += 1

            # Calculate final metrics
            results = {}
            for service, data in service_metrics.items():
                success_rate = (
                    (data["completed"] / data["total"] * 100)
                    if data["total"] > 0
                    else 0
                )
                avg_delivery = (
                    statistics.mean(data["delivery_times"])
                    if data["delivery_times"]
                    else 0
                )

                # Find peak hours
                peak_hours = sorted(
                    data["hours"].items(), key=lambda x: x[1], reverse=True
                )[:3]
                peak_hours = [hour for hour, count in peak_hours]

                results[service] = PerformanceMetrics(
                    success_rate=round(success_rate, 1),
                    avg_delivery_time=round(avg_delivery, 1),
                    total_volume=data["total"],
                    revenue=round(data["revenue"], 2),
                    user_satisfaction=self._calculate_satisfaction_score(
                        success_rate, avg_delivery
                    ),
                    peak_hours=peak_hours,
                    failure_reasons=self._analyze_failure_reasons(service, start_date),
                )

            return results

        return self._get_cached_or_compute(cache_key, compute, 60)  # Cache for 1 hour

    def _calculate_satisfaction_score(
        self, success_rate: float, avg_delivery: float
    ) -> float:
        """Calculate user satisfaction score based on performance"""
        # Success rate component (0-50 points)
        success_component = min(50, success_rate / 2)

        # Delivery time component (0-50 points)
        # Optimal delivery time is 30 seconds, max acceptable is 120 seconds
        if avg_delivery <= 30:
            delivery_component = 50
        elif avg_delivery <= 120:
            delivery_component = 50 - ((avg_delivery - 30) / 90 * 50)
        else:
            delivery_component = 0

        return round(success_component + delivery_component, 1)

    def _analyze_failure_reasons(
        self, service_name: str, start_date: datetime
    ) -> Dict[str, int]:
        """Analyze failure reasons for a service"""
        from main import Verification

        # This is a simplified version - in reality, you'd have more detailed failure tracking
        failed_verifications = (
            self.db.query(Verification)
            .filter(
                and_(
                    Verification.service_name == service_name,
                    Verification.status.in_(["cancelled", "failed"]),
                    Verification.created_at >= start_date,
                )
            )
            .all()
        )

        # Simulate failure reason analysis
        reasons = defaultdict(int)
        for v in failed_verifications:
            # In a real implementation, you'd have failure reason tracking
            if v.status == "cancelled":
                reasons["user_cancelled"] += 1
            else:
                reasons["service_unavailable"] += 1

        return dict(reasons)

    def get_predictive_insights(self) -> List[PredictiveInsight]:
        """Generate predictive insights using historical data"""
        insights = []

        # Predict demand patterns
        demand_insight = self._predict_demand_patterns()
        if demand_insight:
            insights.append(demand_insight)

        # Predict service performance
        performance_insights = self._predict_service_performance()
        insights.extend(performance_insights)

        # Predict revenue trends
        revenue_insight = self._predict_revenue_trends()
        if revenue_insight:
            insights.append(revenue_insight)

        return insights

    def _predict_demand_patterns(self) -> Optional[PredictiveInsight]:
        """Predict demand patterns for the next 24 hours"""
        from main import Verification

        # Get hourly verification counts for the last 7 days
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)

        verifications = (
            self.db.query(Verification)
            .filter(Verification.created_at >= seven_days_ago)
            .all()
        )

        if len(verifications) < 50:  # Not enough data
            return None

        # Group by hour of day
        hourly_counts = defaultdict(list)
        for v in verifications:
            hour = v.created_at.hour
            day = v.created_at.date()
            hourly_counts[hour].append(1)

        # Calculate average for each hour
        hourly_averages = {}
        for hour in range(24):
            if hour in hourly_counts:
                hourly_averages[hour] = statistics.mean(hourly_counts[hour])
            else:
                hourly_averages[hour] = 0

        # Find peak hour
        peak_hour = max(hourly_averages.items(), key=lambda x: x[1])
        current_hour = datetime.now(timezone.utc).hour

        # Predict if next few hours will be busy
        next_hours = [(current_hour + i) % 24 for i in range(1, 4)]
        avg_next_demand = statistics.mean([hourly_averages[h] for h in next_hours])

        if avg_next_demand > hourly_averages[current_hour] * 1.5:
            return PredictiveInsight(
                metric="demand_surge",
                prediction=avg_next_demand,
                confidence=0.75,
                timeframe="next_3_hours",
                recommendation="Consider increasing capacity or implementing surge pricing",
                impact="medium",
            )

        return None

    def _predict_service_performance(self) -> List[PredictiveInsight]:
        """Predict service performance issues"""
        insights = []

        service_metrics = self.get_service_performance_analysis(7)  # Last 7 days

        for service, metrics in service_metrics.items():
            # Predict services likely to have issues
            if metrics.success_rate < 90 and metrics.total_volume > 10:
                insights.append(
                    PredictiveInsight(
                        metric="service_reliability",
                        prediction=metrics.success_rate,
                        confidence=0.8,
                        timeframe="next_24_hours",
                        recommendation=f"Monitor {service} closely - success rate declining",
                        impact="high" if metrics.success_rate < 80 else "medium",
                    )
                )

            # Predict slow services
            if metrics.avg_delivery_time > 90 and metrics.total_volume > 5:
                insights.append(
                    PredictiveInsight(
                        metric="delivery_speed",
                        prediction=metrics.avg_delivery_time,
                        confidence=0.7,
                        timeframe="ongoing",
                        recommendation=f"Consider alternative providers for {service}",
                        impact="medium",
                    )
                )

        return insights[:5]  # Return top 5 insights

    def _predict_revenue_trends(self) -> Optional[PredictiveInsight]:
        """Predict revenue trends"""
        from main import Transaction

        # Get daily revenue for last 30 days
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)

        daily_revenue = (
            self.db.query(
                func.date(Transaction.created_at).label("date"),
                func.sum(Transaction.amount).label("revenue"),
            )
            .filter(
                and_(
                    Transaction.type == "debit",
                    Transaction.created_at >= thirty_days_ago,
                )
            )
            .group_by(func.date(Transaction.created_at))
            .all()
        )

        if len(daily_revenue) < 7:  # Not enough data
            return None

        # Calculate trend
        revenues = [abs(float(r.revenue)) for r in daily_revenue]

        if len(revenues) >= 7:
            # Simple trend analysis - compare last 7 days to previous 7 days
            recent_avg = statistics.mean(revenues[-7:])
            previous_avg = (
                statistics.mean(revenues[-14:-7]) if len(revenues) >= 14 else recent_avg
            )

            trend_pct = (
                ((recent_avg - previous_avg) / previous_avg * 100)
                if previous_avg > 0
                else 0
            )

            if abs(trend_pct) > 10:  # Significant trend
                direction = "increasing" if trend_pct > 0 else "decreasing"

                return PredictiveInsight(
                    metric="revenue_trend",
                    prediction=trend_pct,
                    confidence=0.6,
                    timeframe="next_7_days",
                    recommendation=f"Revenue is {direction} by {abs(trend_pct):.1f}% - adjust strategy accordingly",
                    impact="high" if abs(trend_pct) > 20 else "medium",
                )

        return None

    def get_user_behavior_analysis(self) -> Dict:
        """Analyze user behavior patterns"""
        from main import Verification, User, Transaction

        cache_key = "user_behavior_analysis"

        def compute():
            thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)

            # User segmentation
            users_with_activity = (
                self.db.query(User.id)
                .join(Verification)
                .filter(Verification.created_at >= thirty_days_ago)
                .distinct()
                .all()
            )

            user_segments = {
                "new_users": 0,
                "active_users": 0,
                "power_users": 0,
                "churned_users": 0,
            }

            service_preferences = defaultdict(int)
            usage_patterns = defaultdict(list)

            for user_id_tuple in users_with_activity:
                user_id = user_id_tuple[0]

                # Get user's verifications
                user_verifications = (
                    self.db.query(Verification)
                    .filter(
                        and_(
                            Verification.user_id == user_id,
                            Verification.created_at >= thirty_days_ago,
                        )
                    )
                    .all()
                )

                verification_count = len(user_verifications)

                # Segment users
                if verification_count >= 50:
                    user_segments["power_users"] += 1
                elif verification_count >= 5:
                    user_segments["active_users"] += 1
                else:
                    user_segments["new_users"] += 1

                # Track service preferences
                for v in user_verifications:
                    service_preferences[v.service_name] += 1
                    usage_patterns[user_id].append(v.created_at.hour)

            # Calculate peak usage hours across all users
            all_hours = []
            for hours in usage_patterns.values():
                all_hours.extend(hours)

            hour_distribution = defaultdict(int)
            for hour in all_hours:
                hour_distribution[hour] += 1

            peak_hours = sorted(
                hour_distribution.items(), key=lambda x: x[1], reverse=True
            )[:5]

            return {
                "user_segments": user_segments,
                "top_services": dict(
                    sorted(
                        service_preferences.items(), key=lambda x: x[1], reverse=True
                    )[:10]
                ),
                "peak_usage_hours": [hour for hour, count in peak_hours],
                "total_active_users": len(users_with_activity),
                "avg_verifications_per_user": (
                    statistics.mean([len(hours) for hours in usage_patterns.values()])
                    if usage_patterns
                    else 0
                ),
            }

        return self._get_cached_or_compute(cache_key, compute, 120)  # Cache for 2 hours

    def get_financial_analytics(self) -> Dict:
        """Comprehensive financial analytics"""
        from main import Transaction, User, Subscription

        cache_key = "financial_analytics"

        def compute():
            thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)

            # Revenue analysis
            revenue_data = (
                self.db.query(Transaction)
                .filter(
                    and_(
                        Transaction.type == "debit",
                        Transaction.created_at >= thirty_days_ago,
                    )
                )
                .all()
            )

            total_revenue = sum(abs(t.amount) for t in revenue_data)

            # Daily revenue trend
            daily_revenue = defaultdict(float)
            for t in revenue_data:
                date = t.created_at.date()
                daily_revenue[date] += abs(t.amount)

            # Subscription revenue
            active_subscriptions = (
                self.db.query(Subscription)
                .filter(Subscription.status == "active")
                .all()
            )

            subscription_revenue = sum(s.price for s in active_subscriptions)

            # Customer metrics
            paying_customers = (
                self.db.query(Transaction.user_id)
                .filter(
                    and_(
                        Transaction.type == "credit",
                        Transaction.created_at >= thirty_days_ago,
                    )
                )
                .distinct()
                .count()
            )

            # Average revenue per user
            arpu = total_revenue / paying_customers if paying_customers > 0 else 0

            return {
                "total_revenue_30d": round(total_revenue, 2),
                "subscription_revenue": round(subscription_revenue, 2),
                "transaction_revenue": round(total_revenue - subscription_revenue, 2),
                "paying_customers": paying_customers,
                "arpu": round(arpu, 2),
                "daily_revenue_trend": {
                    str(date): round(amount, 2)
                    for date, amount in sorted(daily_revenue.items())
                },
                "revenue_growth": self._calculate_revenue_growth(daily_revenue),
            }

        return self._get_cached_or_compute(cache_key, compute, 60)

    def _calculate_revenue_growth(self, daily_revenue: Dict) -> float:
        """Calculate revenue growth rate"""
        if len(daily_revenue) < 14:
            return 0.0

        sorted_dates = sorted(daily_revenue.keys())

        # Compare last 7 days to previous 7 days
        recent_revenue = sum(daily_revenue[date] for date in sorted_dates[-7:])
        previous_revenue = sum(daily_revenue[date] for date in sorted_dates[-14:-7])

        if previous_revenue == 0:
            return 0.0

        growth_rate = ((recent_revenue - previous_revenue) / previous_revenue) * 100
        return round(growth_rate, 1)

    def generate_executive_dashboard(self) -> Dict:
        """Generate executive-level dashboard with key metrics"""
        real_time = self.get_real_time_metrics()
        financial = self.get_financial_analytics()
        user_behavior = self.get_user_behavior_analysis()
        insights = self.get_predictive_insights()

        # Key performance indicators
        kpis = {
            "revenue_30d": financial["total_revenue_30d"],
            "active_users": user_behavior["total_active_users"],
            "success_rate": real_time["hourly_success_rate"],
            "system_health": real_time["system_health"],
            "revenue_growth": financial["revenue_growth"],
        }

        # Alerts and recommendations
        alerts = []
        for insight in insights:
            if insight.impact == "high":
                alerts.append(
                    {
                        "type": "warning",
                        "message": insight.recommendation,
                        "metric": insight.metric,
                    }
                )

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "kpis": kpis,
            "real_time_metrics": real_time,
            "financial_summary": financial,
            "user_insights": user_behavior,
            "predictive_insights": [asdict(insight) for insight in insights],
            "alerts": alerts,
            "recommendations": self._generate_recommendations(kpis, insights),
        }

    def _generate_recommendations(
        self, kpis: Dict, insights: List[PredictiveInsight]
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        # Revenue-based recommendations
        if kpis["revenue_growth"] < -10:
            recommendations.append(
                "Revenue declining - consider promotional campaigns or new service offerings"
            )
        elif kpis["revenue_growth"] > 20:
            recommendations.append(
                "Strong revenue growth - consider scaling infrastructure to meet demand"
            )

        # Success rate recommendations
        if kpis["success_rate"] < 90:
            recommendations.append(
                "Success rate below target - investigate service provider issues"
            )

        # System health recommendations
        if kpis["system_health"] in ["degraded", "critical"]:
            recommendations.append(
                "System health issues detected - immediate attention required"
            )

        # Insight-based recommendations
        high_impact_insights = [i for i in insights if i.impact == "high"]
        for insight in high_impact_insights[:3]:  # Top 3 high-impact insights
            recommendations.append(insight.recommendation)

        return recommendations


# Utility functions for integration
async def get_real_time_dashboard_data(db: Session) -> Dict:
    """Get real-time dashboard data for frontend"""
    analytics = AdvancedAnalytics(db)

    return {
        "metrics": analytics.get_real_time_metrics(),
        "insights": [
            asdict(insight) for insight in analytics.get_predictive_insights()[:3]
        ],
        "system_status": analytics._calculate_system_health(),
    }


def export_analytics_report(db: Session, format: str = "json") -> str:
    """Export comprehensive analytics report"""
    analytics = AdvancedAnalytics(db)
    dashboard = analytics.generate_executive_dashboard()

    if format == "json":
        return json.dumps(dashboard, indent=2, default=str)

    # Could add CSV, PDF export formats here
    return json.dumps(dashboard, default=str)
