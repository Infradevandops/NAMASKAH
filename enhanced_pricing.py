"""
Enhanced Pricing Engine
Dynamic pricing based on demand, success rates, and market conditions
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import math
import logging

logger = logging.getLogger(__name__)

class PricingTier(Enum):
    PREMIUM = "premium"
    STANDARD = "standard"
    ECONOMY = "economy"
    BULK = "bulk"

@dataclass
class PricingFactors:
    """Factors that influence pricing"""
    base_price: float
    demand_multiplier: float = 1.0
    success_rate_modifier: float = 1.0
    time_of_day_modifier: float = 1.0
    volume_discount: float = 0.0
    carrier_premium: float = 0.0
    priority_surcharge: float = 0.0

@dataclass
class PricingResult:
    """Result of pricing calculation"""
    final_price: float
    base_price: float
    discounts_applied: List[str]
    surcharges_applied: List[str]
    savings: float
    tier: PricingTier

class EnhancedPricingEngine:
    """Advanced pricing engine with dynamic adjustments"""
    
    def __init__(self):
        # Base pricing tiers
        self.base_tiers = {
            'tier1': {'name': 'High-Demand', 'base_price': 0.75, 'services': ['whatsapp', 'telegram', 'discord', 'google']},
            'tier2': {'name': 'Standard', 'base_price': 1.00, 'services': ['instagram', 'facebook', 'twitter', 'tiktok']},
            'tier3': {'name': 'Premium', 'base_price': 1.50, 'services': ['paypal', 'banking', 'finance']},
            'tier4': {'name': 'Specialty', 'base_price': 2.00, 'services': []}
        }
        
        # Dynamic pricing parameters
        self.demand_thresholds = {
            'low': 0.5,      # < 50% of average demand
            'normal': 1.0,   # Normal demand
            'high': 1.5,     # > 150% of average demand
            'peak': 2.0      # > 200% of average demand
        }
        
        # Time-based pricing
        self.time_modifiers = {
            'peak_hours': (9, 17, 1.1),      # Business hours +10%
            'off_hours': (18, 8, 0.95),      # Evening/night -5%
            'weekend': (1.05,),              # Weekend +5%
        }
        
        # Volume discount tiers
        self.volume_tiers = [
            (1, 10, 0.0),      # 1-10: No discount
            (11, 50, 0.05),    # 11-50: 5% discount
            (51, 100, 0.10),   # 51-100: 10% discount
            (101, 500, 0.15),  # 101-500: 15% discount
            (501, float('inf'), 0.20)  # 501+: 20% discount
        ]
    
    def calculate_demand_multiplier(self, service_name: str, current_hour: int) -> float:
        """Calculate demand-based pricing multiplier"""
        # This would typically use real-time data
        # For now, simulate based on service popularity and time
        
        popular_services = ['whatsapp', 'telegram', 'google', 'discord']
        
        if service_name in popular_services:
            base_demand = 1.2
        else:
            base_demand = 1.0
        
        # Peak hours increase demand
        if 9 <= current_hour <= 17:
            time_demand = 1.1
        elif 18 <= current_hour <= 22:
            time_demand = 1.05
        else:
            time_demand = 0.95
        
        return base_demand * time_demand
    
    def calculate_success_rate_modifier(self, service_name: str, success_rate: float) -> float:
        """Adjust pricing based on service success rate"""
        if success_rate >= 98:
            return 1.1  # Premium for high reliability
        elif success_rate >= 95:
            return 1.0  # Standard pricing
        elif success_rate >= 90:
            return 0.95  # Small discount for lower reliability
        else:
            return 0.85  # Significant discount for poor reliability
    
    def calculate_volume_discount(self, monthly_count: int) -> float:
        """Calculate volume-based discount"""
        for min_vol, max_vol, discount in self.volume_tiers:
            if min_vol <= monthly_count <= max_vol:
                return discount
        return 0.0
    
    def get_time_modifier(self, current_time: datetime) -> Tuple[float, str]:
        """Get time-based pricing modifier"""
        hour = current_time.hour
        weekday = current_time.weekday()
        
        # Weekend pricing
        if weekday >= 5:  # Saturday = 5, Sunday = 6
            return self.time_modifiers['weekend'][0], "weekend_surcharge"
        
        # Peak hours (business hours)
        if 9 <= hour <= 17:
            return self.time_modifiers['peak_hours'][2], "peak_hours"
        
        # Off hours
        return self.time_modifiers['off_hours'][2], "off_hours"
    
    def calculate_carrier_premium(self, carrier_preference: Optional[str]) -> Tuple[float, str]:
        """Calculate premium for specific carrier requests"""
        if not carrier_preference:
            return 0.0, ""
        
        premium_carriers = ['verizon', 'att', 'tmobile']
        
        if carrier_preference.lower() in premium_carriers:
            return 0.25, f"premium_carrier_{carrier_preference}"
        
        return 0.15, f"specific_carrier_{carrier_preference}"
    
    def calculate_dynamic_price(self, 
                              service_name: str,
                              user_plan: str = 'starter',
                              monthly_count: int = 0,
                              success_rate: float = 95.0,
                              carrier_preference: Optional[str] = None,
                              priority: bool = False,
                              current_time: Optional[datetime] = None) -> PricingResult:
        """Calculate dynamic price with all factors"""
        
        if current_time is None:
            current_time = datetime.now(timezone.utc)
        
        # Get base price
        tier = self.get_service_tier(service_name)
        base_price = self.base_tiers[tier]['base_price']
        
        # Initialize pricing factors
        factors = PricingFactors(base_price=base_price)
        
        # Calculate all modifiers
        factors.demand_multiplier = self.calculate_demand_multiplier(service_name, current_time.hour)
        factors.success_rate_modifier = self.calculate_success_rate_modifier(service_name, success_rate)
        
        time_modifier, time_reason = self.get_time_modifier(current_time)
        factors.time_of_day_modifier = time_modifier
        
        factors.volume_discount = self.calculate_volume_discount(monthly_count)
        
        carrier_premium, carrier_reason = self.calculate_carrier_premium(carrier_preference)
        factors.carrier_premium = carrier_premium
        
        if priority:
            factors.priority_surcharge = 0.50  # $0.50 priority fee
        
        # Apply plan discount
        plan_discounts = {
            'starter': 0.0,
            'pro': 0.15,
            'turbo': 0.25
        }
        plan_discount = plan_discounts.get(user_plan, 0.0)
        
        # Calculate final price
        price = base_price
        
        # Apply multipliers
        price *= factors.demand_multiplier
        price *= factors.success_rate_modifier
        price *= factors.time_of_day_modifier
        
        # Apply discounts
        price *= (1 - factors.volume_discount)
        price *= (1 - plan_discount)
        
        # Add surcharges
        price += factors.carrier_premium
        price += factors.priority_surcharge
        
        # Track applied discounts and surcharges
        discounts_applied = []
        surcharges_applied = []
        
        if factors.volume_discount > 0:
            discounts_applied.append(f"Volume discount: {factors.volume_discount*100:.0f}%")
        
        if plan_discount > 0:
            discounts_applied.append(f"Plan discount: {plan_discount*100:.0f}%")
        
        if factors.success_rate_modifier < 1.0:
            discount_pct = (1 - factors.success_rate_modifier) * 100
            discounts_applied.append(f"Reliability discount: {discount_pct:.0f}%")
        
        if time_reason == "off_hours":
            discounts_applied.append("Off-hours discount: 5%")
        
        if factors.demand_multiplier > 1.0:
            surcharge_pct = (factors.demand_multiplier - 1) * 100
            surcharges_applied.append(f"High demand: +{surcharge_pct:.0f}%")
        
        if time_reason in ["peak_hours", "weekend_surcharge"]:
            surcharge_pct = (time_modifier - 1) * 100
            surcharges_applied.append(f"{time_reason.replace('_', ' ').title()}: +{surcharge_pct:.0f}%")
        
        if factors.carrier_premium > 0:
            surcharges_applied.append(f"Carrier premium: +${factors.carrier_premium:.2f}")
        
        if factors.priority_surcharge > 0:
            surcharges_applied.append(f"Priority processing: +${factors.priority_surcharge:.2f}")
        
        # Determine pricing tier
        if price <= 1.0:
            pricing_tier = PricingTier.ECONOMY
        elif price <= 1.5:
            pricing_tier = PricingTier.STANDARD
        elif monthly_count > 100:
            pricing_tier = PricingTier.BULK
        else:
            pricing_tier = PricingTier.PREMIUM
        
        savings = base_price - price if price < base_price else 0
        
        return PricingResult(
            final_price=round(price, 2),
            base_price=base_price,
            discounts_applied=discounts_applied,
            surcharges_applied=surcharges_applied,
            savings=round(savings, 2),
            tier=pricing_tier
        )
    
    def get_service_tier(self, service_name: str) -> str:
        """Get tier for a service"""
        for tier_id, tier_data in self.base_tiers.items():
            if service_name.lower() in tier_data['services']:
                return tier_id
        return 'tier4'  # Default to specialty
    
    def get_pricing_forecast(self, service_name: str, hours_ahead: int = 24) -> List[Dict]:
        """Get pricing forecast for the next N hours"""
        forecast = []
        current_time = datetime.now(timezone.utc)
        
        for hour in range(hours_ahead):
            future_time = current_time + timedelta(hours=hour)
            
            # Calculate price for this hour (using default parameters)
            result = self.calculate_dynamic_price(
                service_name=service_name,
                current_time=future_time
            )
            
            forecast.append({
                "hour": future_time.hour,
                "datetime": future_time.isoformat(),
                "price": result.final_price,
                "tier": result.tier.value,
                "factors": {
                    "demand": "high" if result.final_price > self.base_tiers[self.get_service_tier(service_name)]['base_price'] else "normal"
                }
            })
        
        return forecast
    
    def optimize_timing_for_cost(self, service_name: str, hours_ahead: int = 24) -> Dict:
        """Find the optimal time to minimize cost"""
        forecast = self.get_pricing_forecast(service_name, hours_ahead)
        
        if not forecast:
            return {}
        
        # Find cheapest time
        cheapest = min(forecast, key=lambda x: x["price"])
        
        # Find current price
        current = forecast[0] if forecast else cheapest
        
        savings = current["price"] - cheapest["price"]
        
        return {
            "current_price": current["price"],
            "optimal_price": cheapest["price"],
            "optimal_time": cheapest["datetime"],
            "potential_savings": round(savings, 2),
            "savings_percentage": round((savings / current["price"]) * 100, 1) if current["price"] > 0 else 0,
            "recommendation": "immediate" if savings < 0.10 else "wait"
        }

class SubscriptionPricingManager:
    """Manage subscription-based pricing and benefits"""
    
    def __init__(self):
        self.plans = {
            'starter': {
                'name': 'Starter',
                'monthly_price': 0,
                'discount': 0.0,
                'free_verifications': 1,
                'features': ['1 free verification', 'Basic support'],
                'limits': {'monthly_verifications': 50}
            },
            'pro': {
                'name': 'Pro',
                'monthly_price': 10.50,
                'discount': 0.15,
                'free_verifications': 5,
                'features': ['15% discount', '5 free/month', 'API access', 'Priority support'],
                'limits': {'monthly_verifications': 500}
            },
            'turbo': {
                'name': 'Turbo',
                'monthly_price': 18.00,
                'discount': 0.25,
                'free_verifications': 15,
                'features': ['25% discount', '15 free/month', 'API access', 'Priority support', 'Custom integrations'],
                'limits': {'monthly_verifications': float('inf')}
            },
            'enterprise': {
                'name': 'Enterprise',
                'monthly_price': 50.00,
                'discount': 0.35,
                'free_verifications': 50,
                'features': ['35% discount', '50 free/month', 'Dedicated support', 'Custom pricing', 'SLA guarantee'],
                'limits': {'monthly_verifications': float('inf')}
            }
        }
    
    def calculate_plan_value(self, monthly_usage: int, avg_price_per_verification: float = 1.0) -> Dict:
        """Calculate value proposition for each plan"""
        results = {}
        
        for plan_id, plan in self.plans.items():
            # Calculate monthly cost
            monthly_cost = plan['monthly_price']
            
            # Calculate verification costs
            free_verifications = min(plan['free_verifications'], monthly_usage)
            paid_verifications = max(0, monthly_usage - free_verifications)
            
            # Apply discount to paid verifications
            discounted_price = avg_price_per_verification * (1 - plan['discount'])
            verification_cost = paid_verifications * discounted_price
            
            total_monthly_cost = monthly_cost + verification_cost
            
            # Calculate savings vs starter plan
            starter_cost = monthly_usage * avg_price_per_verification
            savings = starter_cost - total_monthly_cost
            
            results[plan_id] = {
                'plan_name': plan['name'],
                'monthly_subscription': monthly_cost,
                'verification_cost': round(verification_cost, 2),
                'total_monthly_cost': round(total_monthly_cost, 2),
                'savings_vs_starter': round(savings, 2),
                'cost_per_verification': round(total_monthly_cost / monthly_usage, 2) if monthly_usage > 0 else 0,
                'break_even_usage': self._calculate_break_even(plan, avg_price_per_verification),
                'recommended': savings > 0 and monthly_usage >= plan.get('limits', {}).get('monthly_verifications', 0)
            }
        
        return results
    
    def _calculate_break_even(self, plan: Dict, avg_price: float) -> int:
        """Calculate break-even point for a subscription plan"""
        if plan['monthly_price'] == 0:
            return 0
        
        # Solve: monthly_price = savings_per_verification * usage
        # savings_per_verification = avg_price * discount - (avg_price * (1-discount) - avg_price)
        # Simplified: savings_per_verification = avg_price * discount
        
        savings_per_verification = avg_price * plan['discount']
        
        if savings_per_verification <= 0:
            return float('inf')
        
        break_even = plan['monthly_price'] / savings_per_verification
        return math.ceil(break_even)
    
    def recommend_plan(self, monthly_usage: int, avg_price: float = 1.0) -> Dict:
        """Recommend the best plan for a user"""
        plan_values = self.calculate_plan_value(monthly_usage, avg_price)
        
        # Find plan with best value (lowest total cost)
        best_plan = min(
            plan_values.items(),
            key=lambda x: x[1]['total_monthly_cost']
        )
        
        return {
            'recommended_plan': best_plan[0],
            'plan_details': best_plan[1],
            'all_options': plan_values,
            'reasoning': self._get_recommendation_reasoning(best_plan[0], monthly_usage, plan_values)
        }
    
    def _get_recommendation_reasoning(self, plan_id: str, usage: int, all_plans: Dict) -> str:
        """Generate reasoning for plan recommendation"""
        plan = all_plans[plan_id]
        
        if plan_id == 'starter':
            return f"Starter plan is most cost-effective for {usage} verifications/month"
        
        savings = plan['savings_vs_starter']
        return f"Save ${savings:.2f}/month with {plan['plan_name']} plan at your usage level"

# Integration functions
def get_optimized_pricing(service_name: str, user_context: Dict) -> Dict:
    """Get optimized pricing for a service with user context"""
    engine = EnhancedPricingEngine()
    
    result = engine.calculate_dynamic_price(
        service_name=service_name,
        user_plan=user_context.get('plan', 'starter'),
        monthly_count=user_context.get('monthly_count', 0),
        success_rate=user_context.get('success_rate', 95.0),
        carrier_preference=user_context.get('carrier_preference'),
        priority=user_context.get('priority', False)
    )
    
    # Get timing optimization
    timing_opt = engine.optimize_timing_for_cost(service_name)
    
    return {
        'current_price': result.final_price,
        'base_price': result.base_price,
        'tier': result.tier.value,
        'discounts': result.discounts_applied,
        'surcharges': result.surcharges_applied,
        'savings': result.savings,
        'timing_optimization': timing_opt
    }