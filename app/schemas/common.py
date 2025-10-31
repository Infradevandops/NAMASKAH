"""Common schemas for shared responses and utilities."""
from datetime import datetime
from typing import Optional, List, Dict, Any, Generic, TypeVar
from pydantic import BaseModel, Field, validator
from pydantic.generics import GenericModel

T = TypeVar('T')


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Invalid input data",
                "details": {
                    "field": "email",
                    "issue": "Invalid email format"
                },
                "timestamp": "2024-01-20T10:00:00Z"
            }
        }


class SuccessResponse(BaseModel):
    """Schema for success responses."""
    success: bool = Field(default=True, description="Success status")
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Operation completed successfully",
                "data": {
                    "id": "123",
                    "status": "completed"
                }
            }
        }


class PaginationResponse(GenericModel, Generic[T]):
    """Generic schema for paginated responses."""
    items: List[T] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Items per page")
    pages: int = Field(..., description="Total number of pages")
    
    class Config:
        json_schema_extra = {
            "example": {
                "items": [],
                "total": 100,
                "page": 1,
                "size": 20,
                "pages": 5
            }
        }


class HealthCheck(BaseModel):
    """Schema for health check response."""
    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    database: str = Field(..., description="Database status")
    external_services: Dict[str, str] = Field(..., description="External service statuses")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "service": "namaskah-sms",
                "version": "2.3.0",
                "database": "connected",
                "external_services": {
                    "textverified": "operational",
                    "paystack": "operational"
                },
                "timestamp": "2024-01-20T10:00:00Z"
            }
        }


class ServiceStatus(BaseModel):
    """Schema for service status."""
    service_name: str = Field(..., description="Service name")
    status: str = Field(..., description="Service status")
    success_rate: float = Field(..., description="Success rate percentage")
    last_checked: datetime = Field(..., description="Last check timestamp")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "service_name": "textverified_api",
                "status": "operational",
                "success_rate": 95.5,
                "last_checked": "2024-01-20T10:00:00Z"
            }
        }


class ServiceStatusSummary(BaseModel):
    """Schema for service status summary."""
    overall_status: str = Field(..., description="Overall platform status")
    services: List[ServiceStatus] = Field(..., description="Individual service statuses")
    stats: Dict[str, int] = Field(..., description="Status statistics")
    last_updated: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "overall_status": "operational",
                "services": [
                    {
                        "service_name": "textverified_api",
                        "status": "operational",
                        "success_rate": 95.5,
                        "last_checked": "2024-01-20T10:00:00Z"
                    }
                ],
                "stats": {
                    "operational": 5,
                    "degraded": 1,
                    "down": 0
                },
                "last_updated": "2024-01-20T10:00:00Z"
            }
        }


class NotificationResponse(BaseModel):
    """Schema for notification response."""
    id: str
    title: str
    message: str
    type: str = Field(..., description="Notification type: info, success, warning, error")
    is_read: bool
    verification_id: Optional[str]
    created_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "notification_1642680000000",
                "title": "Verification Completed",
                "message": "Your Telegram verification completed successfully!",
                "type": "success",
                "is_read": False,
                "verification_id": "verification_1642680000000",
                "created_at": "2024-01-20T10:00:00Z"
            }
        }


class NotificationPreferences(BaseModel):
    """Schema for notification preferences."""
    in_app_notifications: bool = Field(default=True, description="Enable in-app notifications")
    email_notifications: bool = Field(default=True, description="Enable email notifications")
    receipt_notifications: bool = Field(default=True, description="Enable receipt notifications")
    
    class Config:
        json_schema_extra = {
            "example": {
                "in_app_notifications": True,
                "email_notifications": True,
                "receipt_notifications": False
            }
        }


class AnalyticsResponse(BaseModel):
    """Schema for analytics data."""
    total_users: int = Field(..., description="Total users count")
    new_users: int = Field(..., description="New users in period")
    total_verifications: int = Field(..., description="Total verifications count")
    success_rate: float = Field(..., description="Success rate percentage")
    total_spent: float = Field(..., description="Total amount spent")
    popular_services: List[Dict[str, Any]] = Field(..., description="Popular services")
    daily_usage: List[Dict[str, Any]] = Field(..., description="Daily usage statistics")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_verifications": 150,
                "success_rate": 94.5,
                "total_spent": 125.50,
                "popular_services": [
                    {"service": "telegram", "count": 45},
                    {"service": "whatsapp", "count": 32}
                ],
                "daily_usage": [
                    {"date": "2024-01-20", "count": 12},
                    {"date": "2024-01-19", "count": 8}
                ]
            }
        }


class SupportTicketCreate(BaseModel):
    """Schema for creating support ticket."""
    name: str = Field(..., min_length=1, max_length=100, description="Your name")
    email: str = Field(..., description="Contact email")
    category: str = Field(..., description="Issue category")
    message: str = Field(..., min_length=10, description="Detailed message")
    
    @validator('category')
    def validate_category(cls, v):
        valid_categories = ['billing', 'technical', 'account', 'verification', 'other']
        if v not in valid_categories:
            raise ValueError(f'Category must be one of: {", ".join(valid_categories)}')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "email": "john@example.com",
                "category": "billing",
                "message": "I need help with my recent payment that didn't reflect in my account."
            }
        }


class SupportTicketResponse(BaseModel):
    """Schema for support ticket response."""
    id: str
    name: str
    email: str
    category: str
    message: str
    status: str
    admin_response: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "ticket_1642680000000",
                "name": "John Doe",
                "email": "john@example.com",
                "category": "billing",
                "message": "I need help with my recent payment...",
                "status": "open",
                "admin_response": None,
                "created_at": "2024-01-20T10:00:00Z",
                "updated_at": None
            }
        }


class ExportRequest(BaseModel):
    """Schema for data export request."""
    format: str = Field(default="csv", description="Export format: csv or json")
    date_from: Optional[datetime] = Field(None, description="Start date for export")
    date_to: Optional[datetime] = Field(None, description="End date for export")
    
    @validator('format')
    def validate_format(cls, v):
        if v not in ['csv', 'json']:
            raise ValueError('Format must be csv or json')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "format": "csv",
                "date_from": "2024-01-01T00:00:00Z",
                "date_to": "2024-01-31T23:59:59Z"
            }
        }