# Customer Success Metrics
from datetime import datetime, timedelta, timezone
from typing import Dict, List


class CustomerSuccessMetrics:
    def __init__(self):
        self.success_thresholds = {
            "activation": 1,  # First verification
            "engagement": 5,  # 5+ verifications
            "retention": 30,  # 30+ day usage
        }

    def calculate_health_score(self, user_data: dict) -> dict:
        """Calculate customer health score (0-100)"""
        score = 0
        factors = []

        # Usage frequency (40 points)
        monthly_usage = user_data.get("monthly_verifications", 0)
        if monthly_usage >= 50:
            score += 40
            factors.append("High usage")
        elif monthly_usage >= 10:
            score += 25
            factors.append("Regular usage")
        elif monthly_usage >= 1:
            score += 10
            factors.append("Low usage")

        # Success rate (30 points)
        success_rate = user_data.get("success_rate", 0)
        if success_rate >= 95:
            score += 30
            factors.append("High success rate")
        elif success_rate >= 80:
            score += 20
            factors.append("Good success rate")

        # Payment history (20 points)
        if user_data.get("total_spent", 0) > 50:
            score += 20
            factors.append("High value customer")
        elif user_data.get("total_spent", 0) > 10:
            score += 10
            factors.append("Paying customer")

        # Engagement (10 points)
        if user_data.get("last_login_days", 999) <= 7:
            score += 10
            factors.append("Recently active")

        return {
            "health_score": min(score, 100),
            "risk_level": "low" if score >= 70 else "medium" if score >= 40 else "high",
            "factors": factors,
        }

    def identify_churn_risk(self, users: List[dict]) -> List[dict]:
        """Identify users at risk of churning"""
        at_risk = []

        for user in users:
            health = self.calculate_health_score(user)

            if health["risk_level"] == "high":
                at_risk.append(
                    {
                        "user_id": user.get("id"),
                        "email": user.get("email"),
                        "health_score": health["health_score"],
                        "risk_factors": self.get_risk_factors(user),
                        "recommended_action": self.get_retention_action(user),
                    }
                )

        return at_risk

    def get_risk_factors(self, user_data: dict) -> List[str]:
        """Identify specific risk factors"""
        factors = []

        if user_data.get("last_login_days", 0) > 14:
            factors.append("Inactive for 14+ days")

        if user_data.get("success_rate", 100) < 70:
            factors.append("Low success rate")

        if user_data.get("monthly_verifications", 0) == 0:
            factors.append("No recent usage")

        return factors

    def get_retention_action(self, user_data: dict) -> str:
        """Suggest retention action"""
        if user_data.get("last_login_days", 0) > 30:
            return "Send re-engagement email"
        elif user_data.get("success_rate", 100) < 70:
            return "Provide technical support"
        elif user_data.get("monthly_verifications", 0) == 0:
            return "Offer free credits"
        else:
            return "Monitor closely"


# Global customer success instance
customer_success = CustomerSuccessMetrics()
