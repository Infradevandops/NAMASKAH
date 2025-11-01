#!/usr/bin/env python3
"""Fix TextVerified API integration for working SMS verification"""

import asyncio
import httpx
from typing import Dict, Any

class TextVerifiedIntegrationFixer:
    """Fix and test TextVerified API integration."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.textverified.com/api"
    
    async def test_api_connection(self) -> Dict[str, Any]:
        """Test basic API connectivity."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/Users/balance",
                    params={"bearer": self.api_key},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "status": "success",
                        "balance": data.get("balance", 0),
                        "message": "API connection successful"
                    }
                else:
                    return {
                        "status": "error", 
                        "message": f"API returned {response.status_code}: {response.text}"
                    }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Connection failed: {str(e)}"
            }
    
    async def get_available_services(self) -> Dict[str, Any]:
        """Get real services from TextVerified API."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/Services",
                    params={"bearer": self.api_key},
                    timeout=15
                )
                
                if response.status_code == 200:
                    services = response.json()
                    return {
                        "status": "success",
                        "services": services,
                        "count": len(services) if isinstance(services, list) else 0
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Services API returned {response.status_code}"
                    }
        except Exception as e:
            return {
                "status": "error", 
                "message": f"Services request failed: {str(e)}"
            }
    
    async def test_number_request(self, service_id: int = 1) -> Dict[str, Any]:
        """Test requesting a phone number."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/GetNumber",
                    params={
                        "bearer": self.api_key,
                        "service_id": service_id,
                        "country": "US"
                    },
                    timeout=15
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "status": "success",
                        "number_data": data,
                        "message": "Number request successful"
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Number request returned {response.status_code}: {response.text}"
                    }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Number request failed: {str(e)}"
            }
    
    def generate_service_mapping(self, services: list) -> Dict[str, Dict]:
        """Generate service mapping from TextVerified services."""
        mapping = {}
        
        for service in services:
            if isinstance(service, dict):
                name = service.get("name", "").lower()
                service_id = service.get("id")
                price = service.get("price", 0.50)
                
                # Map common service names
                if "telegram" in name:
                    mapping["telegram"] = {"id": service_id, "cost": price}
                elif "whatsapp" in name:
                    mapping["whatsapp"] = {"id": service_id, "cost": price}
                elif "discord" in name:
                    mapping["discord"] = {"id": service_id, "cost": price}
                elif "instagram" in name:
                    mapping["instagram"] = {"id": service_id, "cost": price}
                elif "twitter" in name:
                    mapping["twitter"] = {"id": service_id, "cost": price}
        
        return mapping
    
    async def run_integration_test(self) -> Dict[str, Any]:
        """Run comprehensive integration test."""
        results = {
            "api_connection": None,
            "services": None,
            "number_request": None,
            "service_mapping": None,
            "recommendations": []
        }
        
        print("🔧 Testing TextVerified Integration")
        print("=" * 40)
        
        # Test 1: API Connection
        print("1. Testing API connection...")
        results["api_connection"] = await self.test_api_connection()
        if results["api_connection"]["status"] == "success":
            print(f"   ✅ Connected - Balance: ${results['api_connection']['balance']}")
        else:
            print(f"   ❌ Failed: {results['api_connection']['message']}")
            return results
        
        # Test 2: Services
        print("2. Fetching available services...")
        results["services"] = await self.get_available_services()
        if results["services"]["status"] == "success":
            count = results["services"]["count"]
            print(f"   ✅ Found {count} services")
            
            # Generate service mapping
            services_list = results["services"]["services"]
            results["service_mapping"] = self.generate_service_mapping(services_list)
            print(f"   📋 Mapped {len(results['service_mapping'])} common services")
        else:
            print(f"   ❌ Failed: {results['services']['message']}")
        
        # Test 3: Number Request (if balance > 0)
        if results["api_connection"]["balance"] > 0:
            print("3. Testing number request...")
            results["number_request"] = await self.test_number_request()
            if results["number_request"]["status"] == "success":
                print("   ✅ Number request successful")
            else:
                print(f"   ❌ Failed: {results['number_request']['message']}")
        else:
            print("3. Skipping number request (insufficient balance)")
            results["recommendations"].append("Add funds to TextVerified account for full testing")
        
        # Generate recommendations
        if results["api_connection"]["status"] == "success":
            results["recommendations"].append("✅ API integration is working")
            
        if results["services"]["status"] == "success":
            results["recommendations"].append("✅ Services can be loaded dynamically")
        else:
            results["recommendations"].append("❌ Fix services endpoint integration")
            
        if results["service_mapping"]:
            results["recommendations"].append("✅ Service mapping can be automated")
        else:
            results["recommendations"].append("❌ Create manual service mapping fallback")
        
        return results

async def main():
    """Main integration test function."""
    
    # You would get this from environment variables in production
    api_key = input("Enter your TextVerified API key: ").strip()
    
    if not api_key:
        print("❌ API key required")
        return
    
    fixer = TextVerifiedIntegrationFixer(api_key)
    results = await fixer.run_integration_test()
    
    print("\n📊 Integration Test Results:")
    print("=" * 40)
    
    for recommendation in results["recommendations"]:
        print(f"  {recommendation}")
    
    print(f"\n🔧 Next Steps:")
    print("1. Update verification creation to use real TextVerified API")
    print("2. Replace static service mapping with dynamic loading")
    print("3. Implement proper SMS polling system")
    print("4. Add error handling for API failures")

if __name__ == "__main__":
    asyncio.run(main())