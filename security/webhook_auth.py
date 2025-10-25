# Webhook Signature Verification
import hmac
import hashlib
import time
from fastapi import HTTPException, Request

class WebhookAuth:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key.encode('utf-8')
    
    def generate_signature(self, payload: bytes, timestamp: int) -> str:
        """Generate HMAC signature for webhook payload"""
        message = f"{timestamp}.{payload.decode('utf-8')}"
        signature = hmac.new(
            self.secret_key,
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return f"t={timestamp},v1={signature}"
    
    def verify_signature(self, payload: bytes, signature: str, tolerance: int = 300) -> bool:
        """Verify webhook signature with timestamp tolerance"""
        try:
            # Parse signature header
            elements = signature.split(',')
            timestamp = None
            signatures = []
            
            for element in elements:
                if element.startswith('t='):
                    timestamp = int(element[2:])
                elif element.startswith('v1='):
                    signatures.append(element[3:])
            
            if not timestamp or not signatures:
                return False
            
            # Check timestamp tolerance
            current_time = int(time.time())
            if abs(current_time - timestamp) > tolerance:
                return False
            
            # Verify signature
            expected_sig = self.generate_signature(payload, timestamp)
            expected_hash = expected_sig.split('v1=')[1]
            
            return any(
                hmac.compare_digest(expected_hash, sig)
                for sig in signatures
            )
        except Exception:
            return False

async def verify_webhook_signature(request: Request, webhook_auth: WebhookAuth):
    """Middleware to verify webhook signatures"""
    signature = request.headers.get('X-Webhook-Signature')
    if not signature:
        raise HTTPException(400, "Missing webhook signature")
    
    body = await request.body()
    if not webhook_auth.verify_signature(body, signature):
        raise HTTPException(401, "Invalid webhook signature")
    
    return True