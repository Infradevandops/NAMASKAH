# ISP/Carrier utilities for Namaskah SMS
AREA_CODE_MAP = {
    "212": {"city": "New York", "state": "NY", "region": "Manhattan"},
    "310": {"city": "Los Angeles", "state": "CA", "region": "West LA"},
    "415": {"city": "San Francisco", "state": "CA", "region": "SF"},
    "312": {"city": "Chicago", "state": "IL", "region": "Downtown"},
    "214": {"city": "Dallas", "state": "TX", "region": "Dallas"},
    "305": {"city": "Miami", "state": "FL", "region": "Miami-Dade"},
}

SUPPORTED_CARRIERS = {
    "verizon": {"name": "Verizon Wireless", "type": "Mobile"},
    "att": {"name": "AT&T Wireless", "type": "Mobile"},
    "tmobile": {"name": "T-Mobile US", "type": "Mobile"},
    "sprint": {"name": "Sprint (T-Mobile)", "type": "Mobile"},
}

def extract_area_code(phone_number):
    if not phone_number:
        return None
    clean_number = ''.join(filter(str.isdigit, phone_number))
    if len(clean_number) == 10:
        return clean_number[:3]
    elif len(clean_number) == 11 and clean_number.startswith('1'):
        return clean_number[1:4]
    return None

def get_location_info(phone_number):
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