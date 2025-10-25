# Revenue Analytics Dashboard
from datetime import datetime, timedelta, timezone
from typing import Dict, List

class RevenueAnalytics:
    def __init__(self):
        self.currency_symbol = "N"
    
    def calculate_mrr(self, transactions: List[dict]) -> dict:
        """Calculate Monthly Recurring Revenue"""
        current_month = datetime.now(timezone.utc).replace(day=1)
        
        monthly_revenue = sum(
            t['amount'] for t in transactions 
            if t['created_at'] >= current_month and t['type'] == 'credit'
        )
        
        # Previous month for comparison
        prev_month = current_month - timedelta(days=32)
        prev_month = prev_month.replace(day=1)
        
        prev_monthly_revenue = sum(
            t['amount'] for t in transactions 
            if prev_month <= t['created_at'] < current_month and t['type'] == 'credit'
        )
        
        growth_rate = 0
        if prev_monthly_revenue > 0:
            growth_rate = ((monthly_revenue - prev_monthly_revenue) / prev_monthly_revenue) * 100
        
        return {
            'current_mrr': monthly_revenue,
            'previous_mrr': prev_monthly_revenue,
            'growth_rate': round(growth_rate, 2),
            'growth_amount': monthly_revenue - prev_monthly_revenue
        }
    
    def calculate_ltv(self, user_data: dict) -> float:
        """Calculate Customer Lifetime Value"""
        avg_monthly_spend = user_data.get('avg_monthly_spend', 0)
        churn_rate = user_data.get('churn_rate', 0.05)  # 5% default
        
        if churn_rate == 0:
            return avg_monthly_spend * 24  # 2 years max
        
        ltv = avg_monthly_spend / churn_rate
        return round(ltv, 2)
    
    def revenue_by_plan(self, users: List[dict]) -> dict:
        """Calculate revenue breakdown by subscription plan"""
        plan_revenue = {'starter': 0, 'pro': 0, 'enterprise': 0}
        plan_users = {'starter': 0, 'pro': 0, 'enterprise': 0}
        
        for user in users:
            plan = user.get('plan', 'starter')
            revenue = user.get('total_spent', 0)
            
            plan_revenue[plan] += revenue
            plan_users[plan] += 1
        
        return {
            'revenue_by_plan': plan_revenue,
            'users_by_plan': plan_users,
            'arpu_by_plan': {
                plan: round(plan_revenue[plan] / max(plan_users[plan], 1), 2)
                for plan in plan_revenue
            }
        }
    
    def cohort_analysis(self, users: List[dict]) -> dict:
        """Simple cohort retention analysis"""
        cohorts = {}
        
        for user in users:
            signup_month = user.get('created_at', datetime.now()).strftime('%Y-%m')
            if signup_month not in cohorts:
                cohorts[signup_month] = {'total': 0, 'active': 0, 'revenue': 0}
            
            cohorts[signup_month]['total'] += 1
            
            if user.get('last_login_days', 999) <= 30:
                cohorts[signup_month]['active'] += 1
            
            cohorts[signup_month]['revenue'] += user.get('total_spent', 0)
        
        # Calculate retention rates
        for month_data in cohorts.values():
            month_data['retention_rate'] = round(
                (month_data['active'] / max(month_data['total'], 1)) * 100, 1
            )
        
        return cohorts
    
    def generate_revenue_report(self, transactions: List[dict], users: List[dict]) -> dict:
        """Generate comprehensive revenue report"""
        mrr_data = self.calculate_mrr(transactions)
        plan_data = self.revenue_by_plan(users)
        cohort_data = self.cohort_analysis(users)
        
        total_revenue = sum(t['amount'] for t in transactions if t['type'] == 'credit')
        total_users = len(users)
        arpu = round(total_revenue / max(total_users, 1), 2)
        
        return {
            'summary': {
                'total_revenue': total_revenue,
                'total_users': total_users,
                'arpu': arpu,
                'mrr': mrr_data['current_mrr']
            },
            'mrr_analysis': mrr_data,
            'plan_breakdown': plan_data,
            'cohort_analysis': cohort_data,
            'generated_at': datetime.now(timezone.utc).isoformat()
        }

# Global revenue analytics instance
revenue_analytics = RevenueAnalytics()