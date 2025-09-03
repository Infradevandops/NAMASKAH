#!/usr/bin/env python3
"""
Mock Twilio Client for Development and Testing
Simulates Twilio SMS functionality without requiring actual Twilio account
"""
import uuid
import time
import random
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class MockMessage:
    """Mock Twilio Message object"""
    def __init__(self, to: str, from_: str, body: str):
        self.sid = f"SM{uuid.uuid4().hex[:32]}"
        self.to = to
        self.from_ = from_
        self.body = body
        self.status = "sent"
        self.date_created = datetime.now()
        self.date_sent = datetime.now()
        self.error_code = None
        self.error_message = None

class MockCall:
    """Mock Twilio Call object"""
    def __init__(self, to: str, from_: str):
        self.sid = f"CA{uuid.uuid4().hex[:32]}"
        self.to = to
        self.from_ = from_
        self.status = "completed"
        self.duration = random.randint(30, 300)  # Random duration 30-300 seconds
        self.date_created = datetime.now()

class MockMessagesResource:
    """Mock Twilio Messages resource"""
    def __init__(self, mock_client):
        self.mock_client = mock_client
    
    def create(self, body: str, from_: str, to: str, **kwargs) -> MockMessage:
        """Create a mock SMS message"""
        # Simulate network delay
        time.sleep(random.uniform(0.1, 0.5))
        
        # Simulate occasional failures (5% chance)
        if random.random() < 0.05:
            raise Exception("Mock SMS delivery failed - simulated network error")
        
        message = MockMessage(to=to, from_=from_, body=body)
        
        # Store in mock client's message history
        self.mock_client.message_history.append({
            "sid": message.sid,
            "to": to,
            "from": from_,
            "body": body,
            "status": "sent",
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info(f"Mock SMS sent: {message.sid} to {to}")
        return message

class MockCallsResource:
    """Mock Twilio Calls resource"""
    def __init__(self, mock_client):
        self.mock_client = mock_client
    
    def create(self, to: str, from_: str, url: str = None, **kwargs) -> MockCall:
        """Create a mock voice call"""
        # Simulate call setup delay
        time.sleep(random.uniform(0.2, 1.0))
        
        # Simulate occasional call failures (3% chance)
        if random.random() < 0.03:
            raise Exception("Mock call failed - simulated busy signal")
        
        call = MockCall(to=to, from_=from_)
        
        # Store in mock client's call history
        self.mock_client.call_history.append({
            "sid": call.sid,
            "to": to,
            "from": from_,
            "status": "completed",
            "duration": call.duration,
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info(f"Mock call made: {call.sid} to {to}, duration: {call.duration}s")
        return call

class MockTwilioClient:
    """
    Mock Twilio Client that simulates Twilio REST API functionality
    Perfect for development, testing, and demos without needing real Twilio account
    """
    
    def __init__(self, account_sid: str = None, auth_token: str = None):
        self.account_sid = account_sid or f"AC{uuid.uuid4().hex[:32]}"
        self.auth_token = auth_token or f"mock_token_{uuid.uuid4().hex[:16]}"
        
        # Initialize resources
        self.messages = MockMessagesResource(self)
        self.calls = MockCallsResource(self)
        
        # Storage for history and analytics
        self.message_history: List[Dict[str, Any]] = []
        self.call_history: List[Dict[str, Any]] = []
        self.webhook_events: List[Dict[str, Any]] = []
        
        # Mock phone numbers pool
        self.available_numbers = [
            "+1555000001", "+1555000002", "+1555000003",
            "+44700000001", "+44700000002", 
            "+33600000001", "+49300000001"
        ]
        
        logger.info("Mock Twilio client initialized successfully")
    
    def get_message_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent message history"""
        return self.message_history[-limit:]
    
    def get_call_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent call history"""
        return self.call_history[-limit:]
    
    def simulate_incoming_sms(self, from_number: str, to_number: str, body: str) -> Dict[str, Any]:
        """Simulate receiving an incoming SMS (for webhook testing)"""
        webhook_event = {
            "MessageSid": f"SM{uuid.uuid4().hex[:32]}",
            "From": from_number,
            "To": to_number,
            "Body": body,
            "MessageStatus": "received",
            "Timestamp": datetime.now().isoformat()
        }
        
        self.webhook_events.append(webhook_event)
        logger.info(f"Simulated incoming SMS from {from_number}: {body}")
        return webhook_event
    
    def simulate_incoming_call(self, from_number: str, to_number: str) -> Dict[str, Any]:
        """Simulate receiving an incoming call (for webhook testing)"""
        webhook_event = {
            "CallSid": f"CA{uuid.uuid4().hex[:32]}",
            "From": from_number,
            "To": to_number,
            "CallStatus": "ringing",
            "Timestamp": datetime.now().isoformat()
        }
        
        self.webhook_events.append(webhook_event)
        logger.info(f"Simulated incoming call from {from_number}")
        return webhook_event
    
    def get_available_phone_numbers(self, country_code: str = "US") -> List[Dict[str, str]]:
        """Get available phone numbers for purchase (mock)"""
        country_numbers = {
            "US": ["+1555000001", "+1555000002", "+1555000003"],
            "GB": ["+44700000001", "+44700000002"],
            "FR": ["+33600000001"],
            "DE": ["+49300000001"]
        }
        
        numbers = country_numbers.get(country_code, country_numbers["US"])
        return [
            {
                "phone_number": num,
                "friendly_name": num,
                "country_code": country_code,
                "monthly_cost": "$1.00",
                "sms_cost": "$0.0075"
            }
            for num in numbers
        ]
    
    def purchase_phone_number(self, phone_number: str) -> Dict[str, Any]:
        """Mock phone number purchase"""
        return {
            "phone_number": phone_number,
            "status": "purchased",
            "monthly_cost": "$1.00",
            "purchase_date": datetime.now().isoformat(),
            "sid": f"PN{uuid.uuid4().hex[:32]}"
        }
    
    def get_usage_statistics(self) -> Dict[str, Any]:
        """Get usage statistics for the mock account"""
        return {
            "messages_sent": len(self.message_history),
            "calls_made": len(self.call_history),
            "total_cost": len(self.message_history) * 0.0075 + len(self.call_history) * 0.02,
            "current_month": {
                "messages": len([m for m in self.message_history 
                               if datetime.fromisoformat(m["timestamp"]).month == datetime.now().month]),
                "calls": len([c for c in self.call_history 
                            if datetime.fromisoformat(c["timestamp"]).month == datetime.now().month])
            }
        }


# Factory function to create appropriate client
def create_twilio_client(account_sid: str = None, auth_token: str = None, use_mock: bool = True):
    """
    Factory function to create either real or mock Twilio client
    Args:
        account_sid: Twilio account SID (ignored if use_mock=True)
        auth_token: Twilio auth token (ignored if use_mock=True)
        use_mock: If True, returns MockTwilioClient, else real Twilio client
    """
    if use_mock or not account_sid or not auth_token:
        logger.info("Creating Mock Twilio client for development")
        return MockTwilioClient(account_sid, auth_token)
    else:
        # Import real Twilio client only when needed
        from twilio.rest import Client
        logger.info("Creating real Twilio client")
        return Client(account_sid, auth_token)


# Example usage and testing
if __name__ == "__main__":
    # Test the mock client
    mock_client = MockTwilioClient()
    
    # Test sending SMS
    try:
        message = mock_client.messages.create(
            body="Hello from Mock Twilio!",
            from_="+1555000001",
            to="+1234567890"
        )
        print(f"Mock SMS sent: {message.sid}")
        
        # Test making call
        call = mock_client.calls.create(
            to="+1234567890",
            from_="+1555000001",
            url="http://demo.twilio.com/docs/voice.xml"
        )
        print(f"Mock call made: {call.sid}")
        
        # Test incoming SMS simulation
        incoming = mock_client.simulate_incoming_sms(
            from_number="+1234567890",
            to_number="+1555000001",
            body="Reply to your message"
        )
        print(f"Simulated incoming SMS: {incoming['MessageSid']}")
        
        # Get statistics
        stats = mock_client.get_usage_statistics()
        print(f"Usage stats: {stats}")
        
    except Exception as e:
        print(f"Error: {e}")