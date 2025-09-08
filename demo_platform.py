#!/usr/bin/env python3
"""
CumApp Platform Demo Script
Demonstrates all platform capabilities using mock services
"""
import asyncio
import httpx
import json
import time
from typing import Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CumAppDemo:
    """Demo class for CumApp platform capabilities"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = httpx.AsyncClient()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.aclose()
    
    async def check_health(self) -> Dict[str, Any]:
        """Check platform health and available services"""
        logger.info("🔍 Checking platform health...")
        response = await self.session.get(f"{self.base_url}/health")
        health_data = response.json()
        
        print("🏥 Platform Health Status:")
        print(f"   Status: {health_data['status']}")
        print(f"   Version: {health_data['version']}")
        print("   Services:")
        for service, available in health_data['services'].items():
            status = "✅ Available" if available else "❌ Not Available"
            print(f"     {service}: {status}")
        
        return health_data
    
    async def demo_textverified_integration(self) -> Dict[str, Any]:
        """Demonstrate TextVerified service integration"""
        logger.info("📱 Testing TextVerified integration...")
        
        try:
            # Check balance
            balance_response = await self.session.get(f"{self.base_url}/api/account/textverified/balance")
            if balance_response.status_code == 200:
                balance_data = balance_response.json()
                print(f"💰 TextVerified Balance: ${balance_data['balance']}")
            else:
                print("⚠️  TextVerified balance check failed (service may not be configured)")
            
            # Get available services
            services_response = await self.session.get(f"{self.base_url}/api/services/textverified")
            if services_response.status_code == 200:
                services_data = services_response.json()
                print(f"🔧 Available Services: {services_data['count']} services")
                
                # Show first few services as examples
                if services_data['services']:
                    print("   Popular services:")
                    for service in services_data['services'][:5]:
                        print(f"     - {service}")
            else:
                print("⚠️  TextVerified services list failed (service may not be configured)")
                
        except Exception as e:
            print(f"❌ TextVerified demo failed: {e}")
            return {"status": "failed", "error": str(e)}
        
        return {"status": "completed"}
    
    async def demo_sms_functionality(self) -> Dict[str, Any]:
        """Demonstrate SMS sending and mock functionality"""
        logger.info("💬 Testing SMS functionality...")
        
        try:
            # Send a test SMS
            sms_data = {
                "to_number": "+1234567890",
                "message": "Hello from CumApp! This is a test message from our communication platform. 🚀",
                "from_number": "+1555000001"
            }
            
            print("📤 Sending test SMS...")
            sms_response = await self.session.post(f"{self.base_url}/api/sms/send", json=sms_data)
            
            if sms_response.status_code == 200:
                sms_result = sms_response.json()
                print(f"✅ SMS sent successfully!")
                print(f"   Message SID: {sms_result['message_sid']}")
                print(f"   To: {sms_result['to']}")
                print(f"   From: {sms_result['from']}")
            else:
                print(f"❌ SMS sending failed: {sms_response.text}")
            
            # Get SMS history (mock)
            print("\n📋 Retrieving SMS history...")
            history_response = await self.session.get(f"{self.base_url}/api/mock/sms/history?limit=10")
            
            if history_response.status_code == 200:
                history_data = history_response.json()
                print(f"📊 SMS History: {history_data['count']} messages")
                
                for msg in history_data['messages'][-3:]:  # Show last 3 messages
                    print(f"   📱 {msg['timestamp'][:19]} | To: {msg['to']} | {msg['body'][:50]}...")
            
            # Simulate incoming SMS
            print("\n📥 Simulating incoming SMS...")
            incoming_response = await self.session.post(
                f"{self.base_url}/api/mock/sms/simulate-incoming",
                params={
                    "from_number": "+1234567890",
                    "to_number": "+1555000001",
                    "body": "Thanks for your message! This is an automated reply."
                }
            )
            
            if incoming_response.status_code == 200:
                incoming_data = incoming_response.json()
                print("✅ Incoming SMS simulated successfully!")
                print(f"   Event ID: {incoming_data['event']['MessageSid']}")
            
        except Exception as e:
            print(f"❌ SMS demo failed: {e}")
            return {"status": "failed", "error": str(e)}
        
        return {"status": "completed"}
    
    async def demo_ai_features(self) -> Dict[str, Any]:
        """Demonstrate AI-powered features"""
        logger.info("🤖 Testing AI features...")
        
        try:
            # Test message intent analysis
            test_message = "I need help urgently with my verification code!"
            print(f"🔍 Analyzing message: '{test_message}'")
            
            intent_response = await self.session.post(
                f"{self.base_url}/api/ai/analyze-intent",
                params={"message": test_message}
            )
            
            if intent_response.status_code == 200:
                intent_data = intent_response.json()
                print("🧠 AI Analysis Results:")
                print(f"   Intent: {intent_data.get('intent', 'unknown')}")
                print(f"   Sentiment: {intent_data.get('sentiment', 'unknown')}")
                print(f"   Urgency: {intent_data.get('urgency', 'unknown')}")
                print(f"   Suggested Tone: {intent_data.get('suggested_tone', 'unknown')}")
            else:
                print("⚠️  AI intent analysis failed (Groq may not be configured)")
            
            # Test response suggestion
            conversation = [
                {"role": "user", "content": "Hi, I'm having trouble with WhatsApp verification"},
                {"role": "assistant", "content": "I can help you with that. What specific issue are you experiencing?"},
                {"role": "user", "content": "I'm not receiving the SMS code"}
            ]
            
            print("\n💡 Getting AI response suggestion...")
            suggestion_response = await self.session.post(
                f"{self.base_url}/api/ai/suggest-response",
                json={
                    "conversation_history": conversation,
                    "context": "Customer support for SMS verification issues"
                }
            )
            
            if suggestion_response.status_code == 200:
                suggestion_data = suggestion_response.json()
                print("🎯 AI Suggested Response:")
                print(f"   '{suggestion_data['suggestion']}'")
            else:
                print("⚠️  AI response suggestion failed (Groq may not be configured)")
            
        except Exception as e:
            print(f"❌ AI demo failed: {e}")
            return {"status": "failed", "error": str(e)}
        
        return {"status": "completed"}
    
    async def demo_number_management(self) -> Dict[str, Any]:
        """Demonstrate phone number management"""
        logger.info("📞 Testing number management...")
        
        try:
            # Get available numbers for different countries
            countries = ["US", "GB", "FR", "DE"]
            
            print("🌍 Available Numbers by Country:")
            for country in countries:
                numbers_response = await self.session.get(f"{self.base_url}/api/numbers/available/{country}")
                
                if numbers_response.status_code == 200:
                    numbers_data = numbers_response.json()
                    print(f"   {country}: {len(numbers_data['available_numbers'])} numbers available")
                    
                    # Show first number as example
                    if numbers_data['available_numbers']:
                        example = numbers_data['available_numbers'][0]
                        print(f"     Example: {example['phone_number']} - {example['monthly_cost']}/month")
            
        except Exception as e:
            print(f"❌ Number management demo failed: {e}")
            return {"status": "failed", "error": str(e)}
        
        return {"status": "completed"}
    
    async def demo_platform_statistics(self) -> Dict[str, Any]:
        """Show platform usage statistics"""
        logger.info("📊 Getting platform statistics...")
        
        try:
            stats_response = await self.session.get(f"{self.base_url}/api/mock/statistics")
            
            if stats_response.status_code == 200:
                stats_data = stats_response.json()
                stats = stats_data['statistics']
                
                print("📈 Platform Usage Statistics:")
                print(f"   Total Messages Sent: {stats['messages_sent']}")
                print(f"   Total Calls Made: {stats['calls_made']}")
                print(f"   Estimated Total Cost: ${stats['total_cost']:.4f}")
                print(f"   This Month - Messages: {stats['current_month']['messages']}")
                print(f"   This Month - Calls: {stats['current_month']['calls']}")
            
        except Exception as e:
            print(f"❌ Statistics demo failed: {e}")
            return {"status": "failed", "error": str(e)}
        
        return {"status": "completed"}
    
    async def run_full_demo(self):
        """Run complete platform demonstration"""
        print("🚀 CumApp Platform Demo Starting...")
        print("=" * 60)
        
        # Check health first
        await self.check_health()
        print("\n" + "=" * 60)
        
        # Demo each component
        demos = [
            ("TextVerified Integration", self.demo_textverified_integration),
            ("SMS Functionality", self.demo_sms_functionality),
            ("AI Features", self.demo_ai_features),
            ("Number Management", self.demo_number_management),
            ("Platform Statistics", self.demo_platform_statistics)
        ]
        
        results = {}
        for demo_name, demo_func in demos:
            print(f"\n🎯 {demo_name}")
            print("-" * 40)
            try:
                result = await demo_func()
                results[demo_name] = result
                print(f"✅ {demo_name} completed successfully")
            except Exception as e:
                print(f"❌ {demo_name} failed: {e}")
                results[demo_name] = {"status": "failed", "error": str(e)}
            
            # Small delay between demos
            await asyncio.sleep(1)
        
        print("\n" + "=" * 60)
        print("🎉 Demo Complete! Summary:")
        for demo_name, result in results.items():
            status = "✅" if result.get("status") == "completed" else "❌"
            print(f"   {status} {demo_name}")
        
        return results


async def main():
    """Main demo function"""
    print("🌟 Welcome to CumApp Platform Demo!")
    print("This demo showcases all platform capabilities using mock services.")
    print("Make sure the CumApp server is running on http://localhost:8000")
    print()
    
    # Wait a moment for user to read
    await asyncio.sleep(2)
    
    async with CumAppDemo() as demo:
        try:
            await demo.run_full_demo()
        except Exception as e:
            print(f"❌ Demo failed: {e}")
            print("Make sure the CumApp server is running: uvicorn main:app --reload")


if __name__ == "__main__":
    asyncio.run(main())