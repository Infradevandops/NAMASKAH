"""Secrets management for production security."""
import os
from typing import Optional, List


class SecretsManager:
    """Secure secrets management with validation."""
    
    REQUIRED_SECRETS = [
        "SECRET_KEY",
        "DATABASE_URL", 
        "TEXTVERIFIED_API_KEY",
        "PAYSTACK_SECRET_KEY"
    ]
    
    @staticmethod
    def get_secret(key: str, default: Optional[str] = None) -> str:
        """Get secret from environment with validation."""
        value = os.getenv(key, default)
        if not value:
            raise ValueError(f"Required secret {key} not found")
        return value
    
    @staticmethod
    def validate_required_secrets() -> None:
        """Validate all required secrets are present."""
        missing = []
        for key in SecretsManager.REQUIRED_SECRETS:
            if not os.getenv(key):
                # Auto-generate SECRET_KEY if missing (common for deployment)
                if key == "SECRET_KEY":
                    import secrets
                    generated_key = secrets.token_urlsafe(32)
                    os.environ[key] = generated_key
                    print(f"⚠️ Generated {key} for deployment")
                else:
                    missing.append(key)
        
        if missing:
            raise ValueError(f"Missing required secrets: {missing}")
    
    @staticmethod
    def generate_secret_key() -> str:
        """Generate secure 256-bit secret key."""
        import secrets
        return secrets.token_urlsafe(32)