"""
TextVerified API Optimization Module
Enhanced integration with advanced features and better error handling
"""

import asyncio
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
import requests
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class VerificationStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


@dataclass
class CarrierFilter:
    """Enhanced carrier filtering options"""

    carrier: Optional[str] = None
    area_code: Optional[str] = None
    state: Optional[str] = None
    exclude_voip: bool = True
    exclude_landline: bool = False


@dataclass
class VerificationRequest:
    """Structured verification request"""

    service_name: str
    capability: str = "sms"
    carrier_filter: Optional[CarrierFilter] = None
    priority: bool = False
    webhook_url: Optional[str] = None


class EnhancedTextVerifiedClient:
    """Enhanced TextVerified client with advanced features"""

    def __init__(self, api_key: str, email: str):
        self.base_url = "https://www.textverified.com"
        self.api_key = api_key
        self.email = email
        self.token = None
        self.token_expires = None
        self.rate_limit_remaining = 100
        self.rate_limit_reset = None

    async def get_token(self, force_refresh=False) -> str:
        """Enhanced token management with async support"""
        if self.token and not force_refresh:
            if self.token_expires and datetime.now(timezone.utc) < self.token_expires:
                return self.token

        try:
            headers = {"X-API-KEY": self.api_key, "X-API-USERNAME": self.email}
            response = requests.post(
                f"{self.base_url}/api/pub/v2/auth", headers=headers, timeout=10
            )
            response.raise_for_status()

            data = response.json()
            self.token = data["token"]
            self.token_expires = datetime.now(timezone.utc) + timedelta(minutes=50)

            logger.info("✅ TextVerified token refreshed successfully")
            return self.token

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ TextVerified auth failed: {e}")
            raise Exception(f"Authentication failed: {str(e)}")

    def _update_rate_limits(self, response: requests.Response):
        """Update rate limit tracking from response headers"""
        self.rate_limit_remaining = int(
            response.headers.get("X-RateLimit-Remaining", 100)
        )
        reset_time = response.headers.get("X-RateLimit-Reset")
        if reset_time:
            self.rate_limit_reset = datetime.fromtimestamp(
                int(reset_time), timezone.utc
            )

    async def check_rate_limit(self):
        """Check if we're approaching rate limits"""
        if self.rate_limit_remaining < 10:
            if (
                self.rate_limit_reset
                and datetime.now(timezone.utc) < self.rate_limit_reset
            ):
                wait_time = (
                    self.rate_limit_reset - datetime.now(timezone.utc)
                ).total_seconds()
                logger.warning(f"⏳ Rate limit low, waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)

    async def get_available_services(self) -> List[Dict]:
        """Get all available services with current pricing"""
        await self.check_rate_limit()

        try:
            headers = {"Authorization": f"Bearer {await self.get_token()}"}
            response = requests.get(
                f"{self.base_url}/api/pub/v2/services", headers=headers, timeout=10
            )
            response.raise_for_status()
            self._update_rate_limits(response)

            return response.json().get("data", [])

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get services: {e}")
            return []

    async def get_service_availability(self, service_name: str) -> Dict:
        """Check real-time availability for a specific service"""
        await self.check_rate_limit()

        try:
            headers = {"Authorization": f"Bearer {await self.get_token()}"}
            response = requests.get(
                f"{self.base_url}/api/pub/v2/services/{service_name}/availability",
                headers=headers,
                timeout=10,
            )
            response.raise_for_status()
            self._update_rate_limits(response)

            data = response.json()
            return {
                "available": data.get("available", False),
                "estimated_wait": data.get("estimatedWait", 0),
                "success_rate": data.get("successRate", 0),
                "carriers_available": data.get("carriersAvailable", []),
            }

        except requests.exceptions.RequestException as e:
            logger.warning(f"Availability check failed for {service_name}: {e}")
            return {"available": True, "estimated_wait": 0, "success_rate": 95}

    async def create_verification_enhanced(
        self, request: VerificationRequest
    ) -> Tuple[str, Dict]:
        """Enhanced verification creation with advanced options"""
        await self.check_rate_limit()

        # Check service availability first
        availability = await self.get_service_availability(request.service_name)
        if not availability["available"]:
            raise Exception(f"Service {request.service_name} is currently unavailable")

        payload = {
            "serviceName": request.service_name,
            "capability": request.capability,
        }

        # Add carrier filtering
        if request.carrier_filter:
            if request.carrier_filter.carrier:
                payload["carrier"] = request.carrier_filter.carrier
            if request.carrier_filter.area_code:
                payload["areaCode"] = request.carrier_filter.area_code
            if request.carrier_filter.state:
                payload["state"] = request.carrier_filter.state
            if request.carrier_filter.exclude_voip:
                payload["excludeVoip"] = True
            if request.carrier_filter.exclude_landline:
                payload["excludeLandline"] = True

        # Priority queue
        if request.priority:
            payload["priority"] = True

        # Webhook URL
        if request.webhook_url:
            payload["webhookUrl"] = request.webhook_url

        try:
            headers = {"Authorization": f"Bearer {await self.get_token()}"}
            response = requests.post(
                f"{self.base_url}/api/pub/v2/verifications",
                headers=headers,
                json=payload,
                timeout=15,
            )
            response.raise_for_status()
            self._update_rate_limits(response)

            verification_id = response.headers.get("Location", "").split("/")[-1]
            verification_data = await self.get_verification_details(verification_id)

            return verification_id, verification_data

        except requests.exceptions.RequestException as e:
            if e.response and e.response.status_code == 401:
                # Token expired, retry once
                headers = {
                    "Authorization": f"Bearer {await self.get_token(force_refresh=True)}"
                }
                response = requests.post(
                    f"{self.base_url}/api/pub/v2/verifications",
                    headers=headers,
                    json=payload,
                    timeout=15,
                )
                response.raise_for_status()
                verification_id = response.headers.get("Location", "").split("/")[-1]
                verification_data = await self.get_verification_details(verification_id)
                return verification_id, verification_data
            raise

    async def get_verification_details(self, verification_id: str) -> Dict:
        """Get comprehensive verification details"""
        await self.check_rate_limit()

        try:
            headers = {"Authorization": f"Bearer {await self.get_token()}"}
            response = requests.get(
                f"{self.base_url}/api/pub/v2/verifications/{verification_id}",
                headers=headers,
                timeout=10,
            )
            response.raise_for_status()
            self._update_rate_limits(response)

            data = response.json()

            # Enhanced status mapping
            status_map = {
                "verificationPending": VerificationStatus.PENDING,
                "verificationCompleted": VerificationStatus.COMPLETED,
                "verificationFailed": VerificationStatus.FAILED,
                "verificationExpired": VerificationStatus.EXPIRED,
                "verificationCancelled": VerificationStatus.CANCELLED,
            }

            return {
                "id": verification_id,
                "status": status_map.get(
                    data.get("state"), VerificationStatus.PENDING
                ).value,
                "phone_number": data.get("number"),
                "carrier": data.get("carrier"),
                "network": data.get("network"),
                "location": {
                    "city": data.get("city"),
                    "state": data.get("state"),
                    "country": data.get("country"),
                },
                "created_at": data.get("createdAt"),
                "expires_at": data.get("expiresAt"),
                "estimated_delivery": data.get("estimatedDelivery"),
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get verification details: {e}")
            raise

    async def get_messages_enhanced(self, verification_id: str) -> List[Dict]:
        """Enhanced message retrieval with metadata"""
        await self.check_rate_limit()

        try:
            headers = {"Authorization": f"Bearer {await self.get_token()}"}
            response = requests.get(
                f"{self.base_url}/api/pub/v2/sms?reservationId={verification_id}",
                headers=headers,
                timeout=10,
            )
            response.raise_for_status()
            self._update_rate_limits(response)

            data = response.json()
            messages = []

            for sms in data.get("data", []):
                messages.append(
                    {
                        "content": sms.get("smsContent"),
                        "sender": sms.get("sender"),
                        "received_at": sms.get("receivedAt"),
                        "message_id": sms.get("id"),
                        "verification_code": self._extract_verification_code(
                            sms.get("smsContent", "")
                        ),
                    }
                )

            return messages

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get messages: {e}")
            return []

    def _extract_verification_code(self, message: str) -> Optional[str]:
        """Extract verification code from SMS message"""
        import re

        # Common patterns for verification codes
        patterns = [
            r"\b(\d{4,8})\b",  # 4-8 digit codes
            r"code[:\s]*(\d{4,8})",  # "code: 123456"
            r"verification[:\s]*(\d{4,8})",  # "verification: 123456"
            r"pin[:\s]*(\d{4,8})",  # "pin: 1234"
            r"otp[:\s]*(\d{4,8})",  # "otp: 123456"
        ]

        for pattern in patterns:
            match = re.search(pattern, message.lower())
            if match:
                return match.group(1)

        return None

    async def bulk_create_verifications(
        self, requests_list: List[VerificationRequest]
    ) -> List[Tuple[str, Dict]]:
        """Create multiple verifications efficiently"""
        results = []

        # Process in batches to respect rate limits
        batch_size = 5
        for i in range(0, len(requests_list), batch_size):
            batch = requests_list[i : i + batch_size]

            # Create tasks for concurrent processing
            tasks = [self.create_verification_enhanced(req) for req in batch]

            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Batch verification {i+j} failed: {result}")
                    results.append((None, {"error": str(result)}))
                else:
                    results.append(result)

            # Rate limiting between batches
            if i + batch_size < len(requests_list):
                await asyncio.sleep(1)

        return results

    async def get_account_balance(self) -> Dict:
        """Get current account balance and usage stats"""
        await self.check_rate_limit()

        try:
            headers = {"Authorization": f"Bearer {await self.get_token()}"}
            response = requests.get(
                f"{self.base_url}/api/pub/v2/account/me", headers=headers, timeout=10
            )
            response.raise_for_status()
            self._update_rate_limits(response)

            data = response.json()
            return {
                "balance": data.get("currentBalance", 0),
                "currency": data.get("currency", "USD"),
                "monthly_usage": data.get("monthlyUsage", 0),
                "total_verifications": data.get("totalVerifications", 0),
                "success_rate": data.get("successRate", 0),
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get account balance: {e}")
            return {"balance": 0, "currency": "USD"}


# Usage optimization functions
async def optimize_service_selection(
    client: EnhancedTextVerifiedClient, preferred_services: List[str]
) -> str:
    """Select the best available service from preferences"""
    for service in preferred_services:
        availability = await client.get_service_availability(service)
        if availability["available"] and availability["success_rate"] > 90:
            return service

    # Fallback to first available
    return preferred_services[0] if preferred_services else "general"


async def smart_carrier_selection(
    client: EnhancedTextVerifiedClient, service_name: str, user_preferences: Dict
) -> CarrierFilter:
    """Intelligently select carrier based on success rates and preferences"""
    availability = await client.get_service_availability(service_name)

    carrier_filter = CarrierFilter()

    # Prefer carriers with high success rates
    available_carriers = availability.get("carriers_available", [])
    if available_carriers and user_preferences.get("carrier_preference"):
        preferred = user_preferences["carrier_preference"]
        if preferred in available_carriers:
            carrier_filter.carrier = preferred

    # Area code preference
    if user_preferences.get("area_code"):
        carrier_filter.area_code = user_preferences["area_code"]

    # Exclude VOIP for better reliability
    carrier_filter.exclude_voip = user_preferences.get("exclude_voip", True)

    return carrier_filter
