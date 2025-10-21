# Pricing Configuration Module

# Service Tiers with Dynamic Pricing
SERVICE_TIERS = {
    'tier1': {
        'name': 'High-Demand',
        'base_price': 0.75,
        'success_rate': 98,
        'services': ['whatsapp', 'telegram', 'discord', 'google']
    },
    'tier2': {
        'name': 'Standard',
        'base_price': 1.00,
        'success_rate': 95,
        'services': ['instagram', 'facebook', 'twitter', 'tiktok']
    },
    'tier3': {
        'name': 'Premium',
        'base_price': 1.50,
        'success_rate': 90,
        'services': ['paypal', 'banking', 'finance']
    },
    'tier4': {
        'name': 'Specialty',
        'base_price': 2.00,
        'success_rate': 85,
        'services': []  # Unlisted services
    }
}

# Subscription Plans
SUBSCRIPTION_PLANS = {
    'starter': {
        'name': 'Starter',
        'price': 0,
        'discount': 0.0,
        'free_verifications': 1,
        'duration': 0,
        'features': ['1 free verification', '5/month limit']
    },
    'pro': {
        'name': 'Pro',
        'price': 10.50,
        'discount': 0.15,
        'free_verifications': 5,
        'duration': 30,
        'features': ['15% discount', '5 free/month', 'API access']
    },
    'turbo': {
        'name': 'Turbo',
        'price': 18.00,
        'discount': 0.25,
        'free_verifications': 15,
        'duration': 30,
        'features': ['25% discount', '15 free/month', 'Priority support']
    }
}

# Rental Pricing
RENTAL_HOURLY = {
    1: 1.20, 3: 1.80, 6: 2.40, 12: 3.00, 24: 3.60
}

HOURLY_RENTAL_RULES = {
    'manual_discount': 0.30,
    'auto_renew_discount': 0.10,
    'bulk_discount_threshold': 5,
    'bulk_discount': 0.15
}

RENTAL_SERVICE_SPECIFIC = {
    7: 10.00, 14: 18.00, 30: 32.50
}

RENTAL_GENERAL_USE = {
    7: 15.00, 14: 27.00, 30: 48.75
}

# Premium Add-ons
PREMIUM_ADDONS = {
    'custom_area_code': 5.00,
    'guaranteed_carrier': 12.50,
    'priority_queue': 2.50
}

VOICE_PREMIUM = 0.30

def get_service_tier(service_name):
    """Get tier for a service"""
    for tier_id, tier_data in SERVICE_TIERS.items():
        if service_name.lower() in tier_data['services']:
            return tier_id
    return 'tier4'  # Default to specialty

def get_service_price(service_name, user_plan='starter', monthly_count=0):
    """Calculate dynamic price for service"""
    tier = get_service_tier(service_name)
    base_price = SERVICE_TIERS[tier]['base_price']
    
    # Apply plan discount
    plan_discount = SUBSCRIPTION_PLANS.get(user_plan, {}).get('discount', 0)
    price = base_price * (1 - plan_discount)
    
    # Volume discount
    if monthly_count >= 100:
        price *= 0.85
    elif monthly_count >= 51:
        price *= 0.90
    elif monthly_count >= 11:
        price *= 0.95
    
    return round(price, 2)

def calculate_rental_cost(hours, service_name='general', mode='always_ready', auto_renew=False, bulk_count=1):
    """Calculate rental cost with all discounts"""
    if hours <= 24:
        base_cost = RENTAL_HOURLY.get(hours, hours * 0.15)
    else:
        days = hours / 24
        if days <= 7:
            base_cost = RENTAL_SERVICE_SPECIFIC.get(7, 10.00)
        elif days <= 14:
            base_cost = RENTAL_SERVICE_SPECIFIC.get(14, 18.00)
        else:
            base_cost = RENTAL_SERVICE_SPECIFIC.get(30, 32.50)
    
    # Apply discounts
    if mode == 'manual':
        base_cost *= (1 - HOURLY_RENTAL_RULES['manual_discount'])
    
    if auto_renew:
        base_cost *= (1 - HOURLY_RENTAL_RULES['auto_renew_discount'])
    
    if bulk_count >= HOURLY_RENTAL_RULES['bulk_discount_threshold']:
        base_cost *= (1 - HOURLY_RENTAL_RULES['bulk_discount'])
    
    return round(base_cost, 2)

def get_hourly_rental_price(hours, service_name='general', mode='always_ready', auto_renew=False, bulk_count=1):
    """Get hourly rental price"""
    return calculate_rental_cost(hours, service_name, mode, auto_renew, bulk_count)

def get_rental_price_breakdown(hours, service_name='general', mode='always_ready', auto_renew=False, bulk_count=1):
    """Get detailed price breakdown"""
    base_price = RENTAL_HOURLY.get(hours, hours * 0.15) if hours <= 24 else 10.00
    
    discounts = []
    final_price = base_price
    
    if mode == 'manual':
        discount = base_price * HOURLY_RENTAL_RULES['manual_discount']
        discounts.append(f"Manual mode: -N{discount:.2f}")
        final_price -= discount
    
    if auto_renew:
        discount = final_price * HOURLY_RENTAL_RULES['auto_renew_discount']
        discounts.append(f"Auto-renewal: -N{discount:.2f}")
        final_price -= discount
    
    if bulk_count >= HOURLY_RENTAL_RULES['bulk_discount_threshold']:
        discount = final_price * HOURLY_RENTAL_RULES['bulk_discount']
        discounts.append(f"Bulk discount: -N{discount:.2f}")
        final_price -= discount
    
    return {
        'base_price': base_price,
        'discounts': discounts,
        'final_price': round(final_price, 2),
        'savings': round(base_price - final_price, 2)
    }