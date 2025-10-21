# Carrier and Location Utilities Module

SUPPORTED_CARRIERS = {
    'verizon': {'name': 'Verizon', 'type': 'mobile'},
    'att': {'name': 'AT&T', 'type': 'mobile'},
    'tmobile': {'name': 'T-Mobile', 'type': 'mobile'},
    'sprint': {'name': 'Sprint', 'type': 'mobile'},
    'cricket': {'name': 'Cricket', 'type': 'mobile'},
    'boost': {'name': 'Boost Mobile', 'type': 'mobile'},
    'metropcs': {'name': 'Metro PCS', 'type': 'mobile'},
    'tracfone': {'name': 'TracFone', 'type': 'mobile'},
    'straighttalk': {'name': 'Straight Talk', 'type': 'mobile'},
    'uscellular': {'name': 'U.S. Cellular', 'type': 'mobile'}
}

AREA_CODE_MAP = {
    '212': {'city': 'New York', 'state': 'NY', 'region': 'Northeast'},
    '310': {'city': 'Los Angeles', 'state': 'CA', 'region': 'West'},
    '415': {'city': 'San Francisco', 'state': 'CA', 'region': 'West'},
    '312': {'city': 'Chicago', 'state': 'IL', 'region': 'Midwest'},
    '214': {'city': 'Dallas', 'state': 'TX', 'region': 'South'},
    '305': {'city': 'Miami', 'state': 'FL', 'region': 'South'},
    '404': {'city': 'Atlanta', 'state': 'GA', 'region': 'South'},
    '617': {'city': 'Boston', 'state': 'MA', 'region': 'Northeast'},
    '206': {'city': 'Seattle', 'state': 'WA', 'region': 'West'},
    '303': {'city': 'Denver', 'state': 'CO', 'region': 'West'},
    '702': {'city': 'Las Vegas', 'state': 'NV', 'region': 'West'},
    '713': {'city': 'Houston', 'state': 'TX', 'region': 'South'},
    '602': {'city': 'Phoenix', 'state': 'AZ', 'region': 'West'},
    '215': {'city': 'Philadelphia', 'state': 'PA', 'region': 'Northeast'},
    '313': {'city': 'Detroit', 'state': 'MI', 'region': 'Midwest'}
}

def extract_area_code(phone_number):
    """Extract area code from phone number"""
    if not phone_number:
        return None
    
    # Remove non-digits
    digits = ''.join(filter(str.isdigit, phone_number))
    
    # US numbers should have 10 or 11 digits
    if len(digits) == 11 and digits[0] == '1':
        return digits[1:4]
    elif len(digits) == 10:
        return digits[:3]
    
    return None

def get_location_info(phone_number):
    """Get location information from phone number"""
    area_code = extract_area_code(phone_number)
    if area_code and area_code in AREA_CODE_MAP:
        return AREA_CODE_MAP[area_code]
    
    return {'city': 'Unknown', 'state': 'Unknown', 'region': 'Unknown'}

def format_carrier_info(carrier_id, phone_number=None):
    """Format carrier information for display"""
    if carrier_id and carrier_id in SUPPORTED_CARRIERS:
        carrier = SUPPORTED_CARRIERS[carrier_id]
        return {
            'name': carrier['name'],
            'type': carrier['type'],
            'requested': True
        }
    
    return {
        'name': 'Auto-Selected',
        'type': 'mobile',
        'requested': False
    }