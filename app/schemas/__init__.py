"""Schemas package for request/response validation."""

# Authentication schemas
from .auth import (
    UserCreate,
    UserUpdate,
    UserResponse,
    LoginRequest,
    TokenResponse,
    APIKeyCreate,
    APIKeyResponse,
    APIKeyListResponse,
    PasswordResetRequest,
    PasswordResetConfirm,
    EmailVerificationRequest,
    GoogleAuthRequest,
)

# Verification schemas
from .verification import (
    VerificationCreate,
    VerificationResponse,
    MessageResponse,
    NumberRentalRequest,
    NumberRentalResponse,
    ExtendRentalRequest,
    RetryVerificationRequest,
    ServicePriceResponse,
    VerificationHistoryResponse,
)

# Payment schemas
from .payment import (
    PaymentInitialize,
    PaymentInitializeResponse,
    PaymentVerify,
    PaymentVerifyResponse,
    WebhookPayload,
    TransactionResponse,
    TransactionHistoryResponse,
    RefundRequest,
    RefundResponse,
    WalletBalanceResponse,
    SubscriptionPlan,
    SubscriptionRequest,
    SubscriptionResponse,
)

# Common schemas
from .common import (
    ErrorResponse,
    SuccessResponse,
    PaginationResponse,
    HealthCheck,
    ServiceStatus,
    ServiceStatusSummary,
    NotificationResponse,
    NotificationPreferences,
    AnalyticsResponse,
    SupportTicketCreate,
    SupportTicketResponse,
    ExportRequest,
)

# Validation utilities
from .validators import (
    validate_phone_number,
    validate_service_name,
    validate_currency_amount,
    validate_referral_code,
    validate_api_key_name,
    validate_webhook_url,
    validate_duration_hours,
    validate_area_code,
    validate_carrier_name,
    ValidationMixin,
    sanitize_input,
    validate_pagination_params,
    create_pagination_response,
)

__all__ = [
    # Authentication
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "LoginRequest",
    "TokenResponse",
    "APIKeyCreate",
    "APIKeyResponse",
    "APIKeyListResponse",
    "PasswordResetRequest",
    "PasswordResetConfirm",
    "EmailVerificationRequest",
    "GoogleAuthRequest",
    # Verification
    "VerificationCreate",
    "VerificationResponse",
    "MessageResponse",
    "NumberRentalRequest",
    "NumberRentalResponse",
    "ExtendRentalRequest",
    "RetryVerificationRequest",
    "ServicePriceResponse",
    "VerificationHistoryResponse",
    # Payment
    "PaymentInitialize",
    "PaymentInitializeResponse",
    "PaymentVerify",
    "PaymentVerifyResponse",
    "WebhookPayload",
    "TransactionResponse",
    "TransactionHistoryResponse",
    "RefundRequest",
    "RefundResponse",
    "WalletBalanceResponse",
    "SubscriptionPlan",
    "SubscriptionRequest",
    "SubscriptionResponse",
    # Common
    "ErrorResponse",
    "SuccessResponse",
    "PaginationResponse",
    "HealthCheck",
    "ServiceStatus",
    "ServiceStatusSummary",
    "NotificationResponse",
    "NotificationPreferences",
    "AnalyticsResponse",
    "SupportTicketCreate",
    "SupportTicketResponse",
    "ExportRequest",
    # Validators
    "validate_phone_number",
    "validate_service_name",
    "validate_currency_amount",
    "validate_referral_code",
    "validate_api_key_name",
    "validate_webhook_url",
    "validate_duration_hours",
    "validate_area_code",
    "validate_carrier_name",
    "ValidationMixin",
    "sanitize_input",
    "validate_pagination_params",
    "create_pagination_response",
]
