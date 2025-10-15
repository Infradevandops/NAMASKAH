"""Fetch all services from TextVerified and cache them"""
import json
from main import tv_client
import requests

try:
    token = tv_client.get_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get all services
    r = requests.get(f"{tv_client.base_url}/api/pub/v2/services", headers=headers, params={
        "numberType": "mobile",
        "reservationType": "verification"
    })
    
    if r.ok:
        services = r.json()
        
        # Extract unique service names
        service_names = set()
        for s in services:
            name = s.get('serviceName', '').strip()
            if name and name != 'servicenotlisted':
                service_names.add(name)
        
        # Sort and save
        sorted_services = sorted(list(service_names))
        
        with open('services_cache.json', 'w') as f:
            json.dump(sorted_services, f, indent=2)
        
        print(f"✅ Cached {len(sorted_services)} services")
        print(f"Sample: {sorted_services[:20]}")
    else:
        print(f"❌ Error: {r.status_code}")
        
except Exception as e:
    print(f"❌ Error: {e}")
