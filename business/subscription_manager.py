# Advanced Subscription Management
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
from pydantic import BaseModel


class SubscriptionManager:
    def __init__(self):
        self.plans = {
            "starter": {"price": 0, "discount": 0, "features": ["basic_api"]},
            "pro": {"price": 25, "discount": 0.20, "features": ["api_v2", "webhooks"]},
            "enterprise": {
                "price": 100,
                "discount": 0.35,
                "features": ["priority_support", "custom_limits"],
            },
        }

    def calculate_pricing(self, plan: str, monthly_usage: int) -> dict:
        """Calculate dynamic pricing based on usage"""
        base_plan = self.plans.get(plan, self.plans["starter"])

        # Volume discounts
        volume_discount = 0
        if monthly_usage > 1000:
            volume_discount = 0.10
        elif monthly_usage > 500:
            volume_discount = 0.05

        total_discount = base_plan["discount"] + volume_discount

        return {
            "plan": plan,
            "base_discount": base_plan["discount"],
            "volume_discount": volume_discount,
            "total_discount": min(total_discount, 0.50),  # Max 50% discount
            "monthly_price": base_plan["price"],
            "features": base_plan["features"],
        }

    def check_plan_limits(self, plan: str, current_usage: dict) -> dict:
        """Check if user is within plan limits"""
        limits = {
            "starter": {"api_calls": 100, "webhooks": 0},
            "pro": {"api_calls": 500, "webhooks": 5},
            "enterprise": {"api_calls": 2000, "webhooks": 20},
        }

        plan_limits = limits.get(plan, limits["starter"])

        return {
            "within_limits": all(
                current_usage.get(key, 0) <= limit for key, limit in plan_limits.items()
            ),
            "limits": plan_limits,
            "usage": current_usage,
        }

    def suggest_upgrade(self, current_plan: str, usage: dict) -> Optional[str]:
        """Suggest plan upgrade based on usage"""
        if current_plan == "starter" and usage.get("api_calls", 0) > 80:
            return "pro"
        elif current_plan == "pro" and usage.get("api_calls", 0) > 400:
            return "enterprise"
        return None


class SubscriptionRequest(BaseModel):
    plan: str
    billing_cycle: str = "monthly"


# Global subscription manager
subscription_manager = SubscriptionManager()
