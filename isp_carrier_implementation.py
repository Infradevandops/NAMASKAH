#!/usr/bin/env python3
"""
ISP/Carrier Information Implementation for Namaskah SMS
Minimal implementation using TextVerified filtering + area code mapping
"""

# Area code to location mapping (US focus)
AREA_CODE_MAP = {
    # New York
    "212": {"city": "New York", "state": "NY", "region": "Manhattan"},
    "646": {"city": "New York", "state": "NY", "region": "Manhattan"},
    "917": {"city": "New York", "state": "NY", "region": "Mobile"},
    "718": {"city": "New York", "state": "NY", "region": "Brooklyn/Queens"},
    
    # California
    "310": {"city": "Los Angeles", "state": "CA", "region": "West LA"},
    "323": {"city": "Los Angeles", "state": "CA", "region": "Central LA"},
    "415": {"city": "San Francisco", "state": "CA", "region": "SF"},
    "510": {"city": "Oakland", "state": "CA", "region": "East Bay"},
    "650": {"city": "San Mateo", "state": "CA", "region": "Peninsula"},
    
    # Texas
    "214": {"city": "Dallas", "state": "TX", "region": "Dallas"},
    "713": {"city": "Houston", "state": "TX", "region": "Houston"},
    "512": {"city": "Austin", "state": "TX", "region": "Austin"},
    
    # Florida
    "305": {"city": "Miami", "state": "FL", "region": "Miami-Dade"},
    "407": {"city": "Orlando", "state": "FL", "region": "Central FL"},
    
    # Illinois
    "312": {"city": "Chicago", "state": "IL", "region": "Downtown"},
    "773": {"city": "Chicago", "state": "IL", "region": "Chicago"},
    
    # Add more as needed...
}

# Supported carriers for filtering
SUPPORTED_CARRIERS = {
    "verizon": {"name": "Verizon Wireless", "type": "Mobile"},
    "att": {"name": "AT&T Wireless", "type": "Mobile"},
    "tmobile": {"name": "T-Mobile US", "type": "Mobile"},
    "sprint": {"name": "Sprint (T-Mobile)", "type": "Mobile"},
}

def extract_area_code(phone_number):
    """Extract area code from phone number"""
    if not phone_number:
        return None
    
    # Remove any formatting
    clean_number = ''.join(filter(str.isdigit, phone_number))
    
    # Handle different formats
    if len(clean_number) == 10:
        return clean_number[:3]
    elif len(clean_number) == 11 and clean_number.startswith('1'):
        return clean_number[1:4]
    
    return None

def get_location_info(phone_number):
    """Get location information from phone number"""
    area_code = extract_area_code(phone_number)
    
    if area_code and area_code in AREA_CODE_MAP:
        location = AREA_CODE_MAP[area_code]
        return {
            "area_code": area_code,
            "city": location["city"],
            "state": location["state"],
            "region": location["region"],
            "display": f"{location['city']}, {location['state']} ({area_code})"
        }
    
    return {
        "area_code": area_code or "Unknown",
        "city": "Unknown",
        "state": "Unknown", 
        "region": "Unknown",
        "display": f"Unknown ({area_code})" if area_code else "Unknown"
    }

def format_carrier_info(requested_carrier, phone_number):
    """Format carrier and location info for display"""
    location = get_location_info(phone_number)
    
    carrier_info = {
        "requested_carrier": None,
        "carrier_display": "Unknown Carrier",
        "location": location,
        "full_display": f"{location['display']} • Unknown Carrier"
    }
    
    if requested_carrier and requested_carrier in SUPPORTED_CARRIERS:
        carrier_data = SUPPORTED_CARRIERS[requested_carrier]
        carrier_info.update({
            "requested_carrier": requested_carrier,
            "carrier_display": carrier_data["name"],
            "full_display": f"{location['display']} • {carrier_data['name']}"
        })
    
    return carrier_info

# Example usage for frontend
def get_verification_display_info(verification_data):
    """Get formatted info for frontend display"""
    phone_number = verification_data.get('phone_number')
    requested_carrier = verification_data.get('requested_carrier')
    requested_area_code = verification_data.get('requested_area_code')
    
    carrier_info = format_carrier_info(requested_carrier, phone_number)
    
    return {
        "phone_number": phone_number,
        "formatted_number": format_phone_number(phone_number),
        "carrier_info": carrier_info,
        "user_selections": {
            "requested_carrier": requested_carrier,
            "requested_area_code": requested_area_code
        }
    }

def format_phone_number(phone_number):
    """Format phone number for display"""
    if not phone_number:
        return "Unknown"
    
    clean = ''.join(filter(str.isdigit, phone_number))
    
    if len(clean) == 10:
        return f"+1 ({clean[:3]}) {clean[3:6]}-{clean[6:]}"
    elif len(clean) == 11 and clean.startswith('1'):
        return f"+1 ({clean[1:4]}) {clean[4:7]}-{clean[7:]}"
    
    return phone_number

# Pro user carrier selection options
PRO_CARRIER_OPTIONS = [
    {"value": "verizon", "label": "Verizon Wireless", "popular": True},
    {"value": "att", "label": "AT&T Wireless", "popular": True},
    {"value": "tmobile", "label": "T-Mobile US", "popular": True},
    {"value": "sprint", "label": "Sprint (T-Mobile)", "popular": False},
]

PRO_AREA_CODE_OPTIONS = [
    {"value": "212", "label": "New York, NY (212)", "popular": True},
    {"value": "310", "label": "Los Angeles, CA (310)", "popular": True},
    {"value": "415", "label": "San Francisco, CA (415)", "popular": True},
    {"value": "312", "label": "Chicago, IL (312)", "popular": True},
    {"value": "214", "label": "Dallas, TX (214)", "popular": True},
    {"value": "305", "label": "Miami, FL (305)", "popular": True},
    # Add more popular area codes
]

if __name__ == "__main__":
    # Test the implementation
    test_cases = [
        {"phone_number": "2125551234", "requested_carrier": "verizon"},
        {"phone_number": "3105551234", "requested_carrier": "att"},
        {"phone_number": "4155551234", "requested_carrier": None},
    ]
    
    for case in test_cases:
        print(f"\nTest: {case}")
        result = get_verification_display_info(case)
        print(f"Display: {result['carrier_info']['full_display']}")
        print(f"Formatted Number: {result['formatted_number']}")