"""
PHASE 2: API Enhancement Implementation
Pro Tips: API versioning, comprehensive validation, graceful degradation
"""
import uuid
import secrets
import asyncio
import httpx
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, validator
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text
from fastapi import HTTPException, Depends, BackgroundTasks

# Pro Tip: API Key model with proper indexing
class APIKey(BaseModel):
    id: str
    user_id: str
    key: str
    name: str
    is_active: bool = True
    created_at: datetime
    last_used: Optional[datetime] = None
    rate_limit: int = 1000  # requests per hour
    permissions: List[str] = ["verify:create", "verify:read"]

# Pro Tip: Comprehensive API request validation
class BulkVerificationRequest(BaseModel):
    services: List[str]
    webhook_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @validator('services')
    def validate_services(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one service required')
        if len(v) > 10:
            raise ValueError('Maximum 10 services per bulk request')
        
        allowed_services = {
            'telegram', 'whatsapp', 'discord', 'twitter', 'instagram',
            'facebook', 'tiktok', 'snapchat', 'linkedin', 'gmail'
        }
        
        for service in v:
            if service.lower() not in allowed_services:
                raise ValueError(f'Invalid service: {service}')
        
        return [s.lower() for s in v]
    
    @validator('webhook_url')
    def validate_webhook_url(cls, v):
        if v:
            if not v.startswith(('http://', 'https://')):
                raise ValueError('Webhook URL must use HTTP or HTTPS')
            if len(v) > 500:
                raise ValueError('Webhook URL too long')
        return v

class WebhookRequest(BaseModel):
    url: str
    events: List[str] = ["verification.completed", "verification.failed"]
    secret: Optional[str] = None
    
    @validator('url')
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must use HTTP or HTTPS')
        return v

# Pro Tip: API Key management with security best practices
class APIKeyManager:
    def __init__(self, db: Session):
        self.db = db
        self.usage_tracking: Dict[str, list] = {}
    
    def create_key(self, user_id: str, name: str, permissions: List[str] = None) -> Dict[str, str]:
        """Create new API key with secure generation"""
        if permissions is None:
            permissions = ["verify:create", "verify:read"]
        
        # Pro Tip: Prefix for easy identification and revocation
        key = f"nsk_{secrets.token_urlsafe(32)}"
        key_hash = self._hash_key(key)
        
        api_key = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "key_hash": key_hash,
            "name": name,
            "permissions": ",".join(permissions),
            "is_active": True,
            "created_at": datetime.utcnow(),
            "rate_limit": 1000
        }
        
        # Store in database (implementation depends on your DB setup)
        # self.db.execute("INSERT INTO api_keys ...", api_key)
        
        return {
            "key": key,
            "name": name,
            "permissions": permissions,
            "rate_limit": 1000
        }
    
    def validate_key(self, key: str) -> Optional[Dict[str, Any]]:
        """Validate API key and check rate limits"""
        if not key.startswith("nsk_"):
            return None
        
        key_hash = self._hash_key(key)
        
        # Check rate limiting
        if not self._check_rate_limit(key):
            raise HTTPException(429, "API rate limit exceeded")
        
        # Simulate database lookup
        # In real implementation, query database with key_hash
        return {
            "user_id": "user_123",
            "permissions": ["verify:create", "verify:read"],
            "is_active": True
        }
    
    def _hash_key(self, key: str) -> str:
        """Hash API key for secure storage"""
        import hashlib
        return hashlib.sha256(key.encode()).hexdigest()
    
    def _check_rate_limit(self, key: str) -> bool:
        """Check API key rate limiting"""
        now = datetime.utcnow()
        hour_ago = now - timedelta(hours=1)
        
        if key not in self.usage_tracking:
            self.usage_tracking[key] = []
        
        # Clean old requests
        self.usage_tracking[key] = [
            req_time for req_time in self.usage_tracking[key]
            if req_time > hour_ago
        ]
        
        # Check limit (1000 per hour)
        if len(self.usage_tracking[key]) >= 1000:
            return False
        
        self.usage_tracking[key].append(now)
        return True

# Pro Tip: Webhook reliability with exponential backoff
class WebhookManager:
    def __init__(self):
        self.retry_delays = [1, 2, 4, 8, 16]  # Exponential backoff
        self.max_retries = 5
    
    async def send_webhook(self, url: str, data: Dict[str, Any], secret: str = None) -> bool:
        """Send webhook with retry logic"""
        headers = {"Content-Type": "application/json"}
        
        # Pro Tip: HMAC signature for webhook verification
        if secret:
            import hmac
            import hashlib
            import json
            
            payload = json.dumps(data, sort_keys=True)
            signature = hmac.new(
                secret.encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()
            headers["X-Webhook-Signature"] = f"sha256={signature}"
        
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(url, json=data, headers=headers)
                    
                    if response.status_code in [200, 201, 202]:
                        logging.info(f"Webhook delivered successfully: {url}")
                        return True
                    
                    logging.warning(f"Webhook failed with status {response.status_code}: {url}")
                    
            except Exception as e:
                logging.error(f"Webhook attempt {attempt + 1} failed: {str(e)}")
            
            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_delays[attempt])
        
        # Log final failure
        logging.error(f"Webhook failed after {self.max_retries} attempts: {url}")
        return False
    
    async def send_verification_webhook(self, webhook_url: str, verification_data: Dict[str, Any]):
        """Send verification status webhook"""
        webhook_data = {
            "event": "verification.completed",
            "timestamp": datetime.utcnow().isoformat(),
            "data": verification_data
        }
        
        return await self.send_webhook(webhook_url, webhook_data)

# Pro Tip: Bulk operations with proper error handling
class BulkOperationManager:
    def __init__(self, tv_client, db: Session):
        self.tv_client = tv_client
        self.db = db
        self.webhook_manager = WebhookManager()
    
    async def create_bulk_verifications(
        self, 
        request: BulkVerificationRequest, 
        user_id: str,
        background_tasks: BackgroundTasks
    ) -> Dict[str, Any]:
        """Create multiple verifications with proper error handling"""
        results = []
        successful_count = 0
        
        for service in request.services:
            try:
                # Create individual verification
                verification = await self._create_single_verification(service, user_id)
                
                result = {
                    "service": service,
                    "status": "success",
                    "verification_id": verification["id"],
                    "phone_number": verification.get("phone_number"),
                    "expires_at": verification.get("expires_at")
                }
                
                successful_count += 1
                
                # Schedule webhook if provided
                if request.webhook_url:
                    background_tasks.add_task(
                        self.webhook_manager.send_verification_webhook,
                        request.webhook_url,
                        verification
                    )
                
            except Exception as e:
                result = {
                    "service": service,
                    "status": "error",
                    "error": str(e),
                    "error_code": getattr(e, 'status_code', 500)
                }
            
            results.append(result)
        
        return {
            "total_requested": len(request.services),
            "successful": successful_count,
            "failed": len(request.services) - successful_count,
            "results": results,
            "metadata": request.metadata
        }
    
    async def _create_single_verification(self, service: str, user_id: str) -> Dict[str, Any]:
        """Create single verification with error handling"""
        try:
            # Call TextVerified API
            response = await self.tv_client.create_verification(service)
            
            if not response.get("success"):
                raise HTTPException(400, f"Failed to create verification for {service}")
            
            verification_data = {
                "id": response["id"],
                "service": service,
                "phone_number": response.get("number"),
                "expires_at": (datetime.utcnow() + timedelta(minutes=10)).isoformat(),
                "status": "pending",
                "user_id": user_id
            }
            
            # Store in database
            # self.db.execute("INSERT INTO verifications ...", verification_data)
            
            return verification_data
            
        except Exception as e:
            logging.error(f"Failed to create verification for {service}: {str(e)}")
            raise HTTPException(400, f"Service {service} temporarily unavailable")

# Pro Tip: API response standardization
class APIResponse:
    @staticmethod
    def success(data: Any, message: str = "Success") -> Dict[str, Any]:
        """Standardized success response"""
        return {
            "success": True,
            "message": message,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def error(message: str, code: str = "GENERAL_ERROR", details: Any = None) -> Dict[str, Any]:
        """Standardized error response"""
        response = {
            "success": False,
            "error": {
                "message": message,
                "code": code,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        if details:
            response["error"]["details"] = details
        
        return response
    
    @staticmethod
    def validation_error(errors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Standardized validation error response"""
        return APIResponse.error(
            "Validation failed",
            "VALIDATION_ERROR",
            {"validation_errors": errors}
        )

# Pro Tip: API versioning support
class APIVersioning:
    SUPPORTED_VERSIONS = ["v1", "v2"]
    DEFAULT_VERSION = "v1"
    
    @staticmethod
    def get_version_from_header(request) -> str:
        """Extract API version from header"""
        version = request.headers.get("API-Version", APIVersioning.DEFAULT_VERSION)
        
        if version not in APIVersioning.SUPPORTED_VERSIONS:
            raise HTTPException(400, f"Unsupported API version: {version}")
        
        return version
    
    @staticmethod
    def version_specific_response(data: Any, version: str) -> Dict[str, Any]:
        """Format response based on API version"""
        if version == "v2":
            # Enhanced response format for v2
            return {
                "api_version": version,
                "success": True,
                "result": data,
                "meta": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "request_id": str(uuid.uuid4())
                }
            }
        else:
            # Legacy format for v1
            return APIResponse.success(data)

# Initialize managers
webhook_manager = WebhookManager()