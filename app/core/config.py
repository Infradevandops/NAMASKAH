"""Core configuration management using Pydantic Settings."""
import os
from typing import Optional
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings
from pydantic import validator


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application
    app_name: str = "Namaskah SMS"
    app_version: str = "2.4.0"
    debug: bool = False
    environment: str = "development"
    
    # Security
    secret_key: str = ""
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 43200  # 30 days
    
    # Server Configuration
    host: str = "127.0.0.1"  # Default to localhost for security
    port: int = 8000
    workers: int = 1
    
    # Database
    database_url: str = "sqlite:///./sms.db"
    database_pool_size: int = 10
    database_max_overflow: int = 20
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_max_connections: int = 50
    
    # TextVerified API
    textverified_api_key: Optional[str] = None
    textverified_email: Optional[str] = None
    textverified_base_url: str = "https://www.textverified.com"
    
    # Paystack
    paystack_secret_key: Optional[str] = None
    paystack_public_key: Optional[str] = None
    
    # Email
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    from_email: str = "noreply@namaskah.app"
    
    # Application URLs
    base_url: str = "http://localhost:8000"
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 3600
    
    # Google OAuth
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    
    # Monitoring
    sentry_dsn: Optional[str] = None
    google_analytics_id: Optional[str] = None
    
    # SSL/TLS
    ssl_cert_path: Optional[str] = None
    ssl_key_path: Optional[str] = None
    
    @validator('secret_key', 'jwt_secret_key')
    def validate_key_length(cls, v):
        """Validate secret keys are at least 32 characters."""
        if v and len(v) < 32:
            raise ValueError('Secret keys must be at least 32 characters long')
        return v
    
    @validator('database_url')
    def validate_database_url(cls, v, values):
        """Validate database URL format."""
        if not v:
            raise ValueError('Database URL is required')
        
        # Check for production database requirements
        environment = values.get('environment', 'development')
        if v.startswith('sqlite://') and environment == 'production':
            raise ValueError('SQLite is not recommended for production. Use PostgreSQL.')
        
        return v
    
    @validator('base_url')
    def validate_base_url(cls, v):
        """Validate base URL format."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('Base URL must start with http:// or https://')
        return v
    
    def __init__(self, **kwargs):
        # Generate secure keys if not provided
        if not kwargs.get('secret_key'):
            import secrets
            kwargs['secret_key'] = secrets.token_urlsafe(32)
        
        if not kwargs.get('jwt_secret_key'):
            import secrets
            kwargs['jwt_secret_key'] = secrets.token_urlsafe(32)
            
        super().__init__(**kwargs)
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"
    
    def validate_production_config(self) -> None:
        """Validate production-specific configuration."""
        if not self.is_production():
            return
        
        required_production_settings = [
            ('database_url', 'DATABASE_URL'),
            ('textverified_api_key', 'TEXTVERIFIED_API_KEY'),
            ('paystack_secret_key', 'PAYSTACK_SECRET_KEY'),
        ]
        
        missing_settings = []
        for attr, env_var in required_production_settings:
            value = getattr(self, attr)
            if not value or value in ['your-', 'change-me', 'placeholder']:
                missing_settings.append(env_var)
        
        if missing_settings:
            raise ValueError(f"Production environment requires these settings: {', '.join(missing_settings)}")
        
        # Validate HTTPS in production
        if not self.base_url.startswith('https://'):
            raise ValueError("Production environment requires HTTPS base URL")
        
        # Validate database is PostgreSQL
        if not self.database_url.startswith('postgresql://'):
            raise ValueError("Production environment requires PostgreSQL database")
        
        # Note: Host binding validation removed for cloud deployment compatibility
        # Cloud platforms and containers handle networking securely at the infrastructure level
    
    model_config = {
        "env_file": [
            ".env.local",      # Highest priority (local overrides)
            ".env",            # Main environment file
            ".env.development" # Fallback for development
        ],
        "case_sensitive": False,
        "extra": "ignore"
    }


from functools import lru_cache
from .secrets import SecretsManager

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance with validation."""
    settings_instance = Settings()
    
    # Validate secrets on startup
    SecretsManager.validate_required_secrets()
    
    # Validate production configuration
    settings_instance.validate_production_config()
    
    return settings_instance

# Legacy settings instance for backward compatibility  
settings = get_settings()