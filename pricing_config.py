# Optimized Pricing Configuration
# Based on OPTIMIZATION_ROI_PLAN.md

# Service Tier Pricing (in Namaskah coins N, 1N = $2 USD)
SERVICE_TIERS = {
    'tier1': {
        'name': 'High-Demand',
        'services': ['whatsapp', 'telegram', 'discord', 'google', 'signal', 'line'],
        'base_price': 0.75,  # $1.50
        'success_rate': 98
    },
    'tier2': {
        'name': 'Standard',
        'services': ['instagram', 'facebook', 'twitter', 'tiktok', 'snapchat', 'reddit', 'linkedin'],
        'base_price': 1.00,  # $2.00
        'success_rate': 95
    },
    'tier3': {
        'name': 'Premium',
        'services': ['paypal', 'venmo', 'cashapp', 'coinbase', 'robinhood', 'stripe', 'chime'],
        'base_price': 1.50,  # $3.00
        'success_rate': 90
    },
    'tier4': {
        'name': 'General/Always-Active Rentals',
        'services': ['general', 'any', 'unlisted', 'rental_general'],  # General use numbers
        'base_price': 2.00,  # $4.00
        'success_rate': 85,
        'description': 'Always-active phone numbers for any service without manual activation'
    }
}

# Subscription Plans
SUBSCRIPTION_PLANS = {
    'starter': {
        'name': 'Starter',
        'price': 0,
        'discount': 0.0,
        'free_verifications': 1,
        'monthly_limit': 5,
        'features': ['Random numbers', 'Basic support', '1 free verification']
    },
    'pro': {
        'name': 'Pro',
        'price': 10.495,  # N10.495 = $20.99
        'discount': 0.15,
        'free_verifications': 5,
        'api_limit': 100,
        'features': ['15% discount', '5 free verifications/month', 'API access (100/day)', 'Email support']
    },
    'turbo': {
        'name': 'Turbo',
        'price': 17.995,  # N17.995 = $35.99
        'discount': 0.25,
        'free_verifications': 15,
        'api_limit': 500,
        'features': ['25% discount', '15 free verifications/month', 'API access (500/day)', 'Priority support']
    },
    'enterprise': {
        'name': 'Enterprise',
        'price': 27.995,  # N27.995 = $55.99
        'discount': 0.40,
        'free_verifications': 50,
        'api_limit': -1,  # unlimited
        'features': ['40% discount', '50 free verifications/month', 'Unlimited API', '24/7 support', 'Dedicated manager']
    }
}

# Rental Pricing (in Namaskah coins)
RENTAL_HOURLY = {
    1: 1.0,    # N1 = $2 (minimum charge)
    2: 1.25,   # N1.25 = $2.50
    3: 1.5,    # N1.5 = $3
    6: 2.0,    # N2 = $4
    12: 2.5,   # N2.5 = $5
    24: 3.0    # N3 = $6
}

# Hourly rental business rules
HOURLY_RENTAL_RULES = {
    'minimum_duration': 1,      # 1 hour minimum
    'maximum_duration': 24,     # 24 hours maximum for hourly
    'auto_extend_discount': 0.10,  # 10% discount for auto-extension
    'manual_mode_discount': 0.30,  # 30% discount for manual mode
    'bulk_discount_threshold': 5,   # 5+ simultaneous rentals
    'bulk_discount_rate': 0.15,     # 15% discount for bulk
    'peak_hours_surcharge': 0.20,   # 20% surcharge during peak (9-17 UTC)
    'weekend_discount': 0.05        # 5% discount on weekends
}

RENTAL_SERVICE_SPECIFIC = {
    168: 10.0,     # 7 days = N10 = $20
    336: 18.0,     # 14 days = N18 = $36
    720: 32.5,     # 30 days = N32.5 = $65
    1440: 60.0,    # 60 days = N60 = $120
    2160: 85.0,    # 90 days = N85 = $170
    8760: 100.0    # 365 days = N100 = $200
}

RENTAL_GENERAL_USE = {
    168: 15.0,     # 7 days = N15 = $30
    336: 25.0,     # 14 days = N25 = $50
    720: 40.0,     # 30 days = N40 = $80
    1440: 70.0,    # 60 days = N70 = $140
    2160: 95.0,    # 90 days = N95 = $190
    8760: 150.0    # 365 days = N150 = $300
}

# Premium Add-ons
PREMIUM_ADDONS = {
    'custom_area_code': 5.0,      # N5 = $10 (select area code only)
    'guaranteed_carrier': 12.5,   # N12.5 = $25 (select area code + ISP)
    'priority_queue': 2.5,        # N2.5 = $5
    'number_portability': 5.0,    # N5 = $10
    'extended_history': 10.0      # N10 = $20/month
}

# Voice Verification Premium
VOICE_PREMIUM = 0.30  # $0.60

# Volume Discounts (additional to plan discount)
VOLUME_DISCOUNTS = {
    'payg': {
        10: 0.0,
        50: 0.05,
        100: 0.10,
        999999: 0.15
    },
    'growth': {
        10: 0.15,
        50: 0.20,
        100: 0.25,
        999999: 0.30
    },
    'pro': {
        10: 0.25,
        50: 0.30,
        100: 0.35,
        999999: 0.40
    },
    'enterprise': {
        10: 0.40,
        50: 0.45,
        100: 0.50,
        999999: 0.55
    }
}

# Legacy Rental Discounts (kept for backward compatibility)
RENTAL_DISCOUNTS = {
    'manual_mode': 0.30,      # 30% discount (updated to match hourly rules)
    'auto_renewal': 0.10,     # 10% discount
    'bulk_5plus': 0.15        # 15% discount for 5+ rentals
}

def get_service_tier(service_name):
    """Get tier for a service"""
    service_lower = service_name.lower()
    for tier_id, tier_data in SERVICE_TIERS.items():
        if service_lower in tier_data['services']:
            return tier_id
    return 'tier4'  # Default to specialty

def get_service_price(service_name, user_plan='starter', volume_count=0):
    """Calculate service price with discounts"""
    tier = get_service_tier(service_name)
    base_price = SERVICE_TIERS[tier]['base_price']
    
    # Apply plan discount
    plan_discount = SUBSCRIPTION_PLANS.get(user_plan, SUBSCRIPTION_PLANS['starter'])['discount']
    
    # Apply volume discount (simplified for now)
    volume_discount = 0.0
    if volume_count >= 100:
        volume_discount = 0.15
    elif volume_count >= 51:
        volume_discount = 0.10
    elif volume_count >= 11:
        volume_discount = 0.05
    
    # Calculate final price
    final_price = base_price * (1 - max(plan_discount, volume_discount))
    return round(final_price, 2)

def calculate_rental_cost(hours, service_name='general', mode='always_active', auto_renew=False, bulk_count=1, is_peak_hour=False, is_weekend=False):
    """Calculate rental cost with discounts and dynamic pricing"""
    from datetime import datetime, timezone
    
    # Determine base cost
    if hours <= 24 and hours in RENTAL_HOURLY:
        # Hourly pricing for short-term rentals
        base_cost = RENTAL_HOURLY[hours]
    elif hours < 24:
        # Interpolate for custom hourly durations
        base_cost = (hours / 24) * RENTAL_HOURLY[24]
    elif service_name.lower() in ['general', 'any', 'unlisted']:
        base_cost = RENTAL_GENERAL_USE.get(hours, 0)
    else:
        base_cost = RENTAL_SERVICE_SPECIFIC.get(hours, 0)
    
    # Calculate proportional cost for non-standard durations
    if base_cost == 0:
        if hours < 168:
            # Use hourly rate for short durations
            base_cost = (hours / 24) * RENTAL_HOURLY[24]
        else:
            # Use weekly rate for long durations
            weekly_cost = RENTAL_GENERAL_USE[168] if service_name.lower() in ['general', 'any', 'unlisted'] else RENTAL_SERVICE_SPECIFIC[168]
            base_cost = (hours / 168) * weekly_cost
    
    # Apply time-based pricing adjustments
    if is_peak_hour and hours <= 24:
        base_cost *= (1 + HOURLY_RENTAL_RULES['peak_hours_surcharge'])
    
    if is_weekend and hours <= 24:
        base_cost *= (1 - HOURLY_RENTAL_RULES['weekend_discount'])
    
    # Apply mode and feature discounts
    if mode == 'manual':
        base_cost *= (1 - HOURLY_RENTAL_RULES['manual_mode_discount'])
    
    if auto_renew:
        base_cost *= (1 - HOURLY_RENTAL_RULES['auto_extend_discount'])
    
    if bulk_count >= HOURLY_RENTAL_RULES['bulk_discount_threshold']:
        base_cost *= (1 - HOURLY_RENTAL_RULES['bulk_discount_rate'])
    
    return round(base_cost, 2)

def get_hourly_rental_price(hours, service_name='general', mode='always_active', auto_renew=False, bulk_count=1):
    """Get hourly rental price with current time-based adjustments"""
    from datetime import datetime, timezone
    
    now = datetime.now(timezone.utc)
    is_peak_hour = 9 <= now.hour < 17  # Peak hours 9 AM - 5 PM UTC
    is_weekend = now.weekday() >= 5    # Saturday = 5, Sunday = 6
    
    return calculate_rental_cost(
        hours=hours,
        service_name=service_name,
        mode=mode,
        auto_renew=auto_renew,
        bulk_count=bulk_count,
        is_peak_hour=is_peak_hour,
        is_weekend=is_weekend
    )

def get_rental_price_breakdown(hours, service_name='general', mode='always_active', auto_renew=False, bulk_count=1):
    """Get detailed price breakdown for transparency"""
    from datetime import datetime, timezone
    
    now = datetime.now(timezone.utc)
    is_peak_hour = 9 <= now.hour < 17
    is_weekend = now.weekday() >= 5
    
    # Base price
    if hours <= 24 and hours in RENTAL_HOURLY:
        base_price = RENTAL_HOURLY[hours]
    elif hours < 24:
        base_price = (hours / 24) * RENTAL_HOURLY[24]
    elif service_name.lower() in ['general', 'any', 'unlisted']:
        base_price = RENTAL_GENERAL_USE.get(hours, (hours / 168) * RENTAL_GENERAL_USE[168])
    else:
        base_price = RENTAL_SERVICE_SPECIFIC.get(hours, (hours / 168) * RENTAL_SERVICE_SPECIFIC[168])
    
    adjustments = []
    current_price = base_price
    
    # Time-based adjustments
    if is_peak_hour and hours <= 24:
        surcharge = base_price * HOURLY_RENTAL_RULES['peak_hours_surcharge']
        current_price += surcharge
        adjustments.append({
            'type': 'Peak Hours Surcharge',
            'rate': f"+{HOURLY_RENTAL_RULES['peak_hours_surcharge']*100:.0f}%",
            'amount': surcharge
        })
    
    if is_weekend and hours <= 24:
        discount = base_price * HOURLY_RENTAL_RULES['weekend_discount']
        current_price -= discount
        adjustments.append({
            'type': 'Weekend Discount',
            'rate': f"-{HOURLY_RENTAL_RULES['weekend_discount']*100:.0f}%",
            'amount': -discount
        })
    
    # Feature discounts
    if mode == 'manual':
        discount = current_price * HOURLY_RENTAL_RULES['manual_mode_discount']
        current_price -= discount
        adjustments.append({
            'type': 'Manual Mode Discount',
            'rate': f"-{HOURLY_RENTAL_RULES['manual_mode_discount']*100:.0f}%",
            'amount': -discount
        })
    
    if auto_renew:
        discount = current_price * HOURLY_RENTAL_RULES['auto_extend_discount']
        current_price -= discount
        adjustments.append({
            'type': 'Auto-Renewal Discount',
            'rate': f"-{HOURLY_RENTAL_RULES['auto_extend_discount']*100:.0f}%",
            'amount': -discount
        })
    
    if bulk_count >= HOURLY_RENTAL_RULES['bulk_discount_threshold']:
        discount = current_price * HOURLY_RENTAL_RULES['bulk_discount_rate']
        current_price -= discount
        adjustments.append({
            'type': f'Bulk Discount ({bulk_count} rentals)',
            'rate': f"-{HOURLY_RENTAL_RULES['bulk_discount_rate']*100:.0f}%",
            'amount': -discount
        })
    
    return {
        'base_price': round(base_price, 2),
        'final_price': round(current_price, 2),
        'adjustments': adjustments,
        'savings': round(base_price - current_price, 2) if current_price < base_price else 0,
        'duration_hours': hours,
        'service_type': 'General Use' if service_name.lower() in ['general', 'any', 'unlisted'] else 'Service-Specific'
    }
