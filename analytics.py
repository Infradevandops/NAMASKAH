#!/usr/bin/env python3
"""
Analytics and monitoring for SMSPROJ Platform
"""
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json
import logging

logger = logging.getLogger(__name__)

class Analytics:
    """Simple analytics tracking"""
    
    def __init__(self):
        self.events = []
        self.stats = {
            'sms_sent': 0,
            'verifications_created': 0,
            'ai_analyses': 0,
            'api_calls': 0,
            'active_users': 0
        }
    
    def track_event(self, event_type: str, data: Dict[str, Any] = None):
        """Track an event"""
        event = {
            'type': event_type,
            'timestamp': datetime.utcnow().isoformat(),
            'data': data or {}
        }
        self.events.append(event)
        
        # Update stats
        if event_type == 'sms_sent':
            self.stats['sms_sent'] += 1
        elif event_type == 'verification_created':
            self.stats['verifications_created'] += 1
        elif event_type == 'ai_analysis':
            self.stats['ai_analyses'] += 1
        elif event_type == 'api_call':
            self.stats['api_calls'] += 1
        
        logger.info(f"Analytics: {event_type} tracked")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics"""
        return {
            **self.stats,
            'total_events': len(self.events),
            'last_activity': self.events[-1]['timestamp'] if self.events else None
        }
    
    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent events"""
        return self.events[-limit:]

# Global analytics instance
analytics = Analytics()