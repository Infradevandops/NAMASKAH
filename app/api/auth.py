"""Authentication API router."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.core.dependencies import get_current_user_id
from app.services import get_auth_service, get_notification_service
from app.schemas import (
    UserCreate, UserResponse, LoginRequest, TokenResponse,
    APIKeyCreate, APIKeyResponse, APIKeyListResponse,
    PasswordResetRequest, PasswordResetConfirm, GoogleAuthRequest,
    SuccessResponse, 
)
from app.core.exceptions import AuthenticationError, ValidationError

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Register new user account."""
    auth_service = get_auth_service(db)
    notification_service = get_notification_service(db)
    
    try:
        # Register user
        user = auth_service.register_user(
            email=user_data.email,
            password=user_data.password,
            referral_code=user_data.referral_code
        )
        
        # Generate access token
        access_token = auth_service.create_access_token(user.id)
        
        # Send welcome email (async)
        await notification_service.send_email(
            to_email=user.email,
            subject="Welcome to Namaskah SMS!",
            body=f"""
            <h2>Welcome to Namaskah SMS!</h2>
            <p>Your account has been created successfully.</p>
            <p>You have {user.free_verifications} free verification(s) to get started.</p>
            <p><a href="/app">Start Using Namaskah SMS</a></p>
            """
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse.from_orm(user)
        )
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Registration failed")


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """Authenticate user with email and password."""
    auth_service = get_auth_service(db)
    
    try:
        # Authenticate user
        user = auth_service.authenticate_user(
            email=login_data.email,
            password=login_data.password
        )
        
        # Generate access token
        access_token = auth_service.create_access_token(user.id)
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse.from_orm(user)
        )
        
    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/google", response_model=TokenResponse)
async def google_auth(
    google_data: GoogleAuthRequest,
    db: Session = Depends(get_db)
):
    """Authenticate with Google OAuth."""
    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests as google_requests
        
        # Verify Google token
        idinfo = id_token.verify_oauth2_token(
            google_data.token, 
            google_requests.Request(), 
            "your-google-client-id"  # Should come from settings
        )
        
        email = idinfo['email']
        email_verified = idinfo.get('email_verified', False)
        
        auth_service = get_auth_service(db)
        
        # Check if user exists
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            # Create new user
            user = auth_service.register_user(email=email, password=idinfo['sub'])
            user.email_verified = email_verified
            db.commit()
        
        # Generate access token
        access_token = auth_service.create_access_token(user.id)
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse.from_orm(user)
        )
        
    except ImportError:
        raise HTTPException(status_code=503, detail="Google OAuth not configured")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Google authentication failed")


@router.get("/me", response_model=UserResponse)
def get_current_user(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get current authenticated user information."""
    auth_service = get_auth_service(db)
    user = auth_service.get(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse.from_orm(user)


@router.post("/forgot-password", response_model=SuccessResponse)
async def forgot_password(
    request_data: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """Request password reset link."""
    auth_service = get_auth_service(db)
    notification_service = get_notification_service(db)
    
    # Generate reset token
    reset_token = auth_service.reset_password_request(request_data.email)
    
    if reset_token:
        # Send reset email
        await notification_service.send_email(
            to_email=request_data.email,
            subject="Password Reset - Namaskah SMS",
            body=f"""
            <h2>Password Reset Request</h2>
            <p>Click the link below to reset your password:</p>
            <p><a href="/auth/reset-password?token={reset_token}">Reset Password</a></p>
            <p>This link expires in 1 hour.</p>
            """
        )
    
    # Always return success for security
    return SuccessResponse(message="If email exists, reset link sent")


@router.post("/reset-password", response_model=SuccessResponse)
def reset_password(
    reset_data: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """Reset password using token."""
    auth_service = get_auth_service(db)
    
    success = auth_service.reset_password(reset_data.token, reset_data.new_password)
    
    if not success:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    return SuccessResponse(message="Password reset successfully")


@router.post("/verify-email", response_model=SuccessResponse)
def verify_email(
    token: str,
    db: Session = Depends(get_db)
):
    """Verify email address using token."""
    auth_service = get_auth_service(db)
    
    success = auth_service.verify_email(token)
    
    if not success:
        raise HTTPException(status_code=400, detail="Invalid verification token")
    
    return SuccessResponse(message="Email verified successfully")


@router.post("/api-keys", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
def create_api_key(
    api_key_data: APIKeyCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Create new API key for programmatic access."""
    auth_service = get_auth_service(db)
    
    api_key = auth_service.create_api_key(user_id, api_key_data.name)
    
    return APIKeyResponse.from_orm(api_key)


@router.get("/api-keys", response_model=list[APIKeyListResponse])
def list_api_keys(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """List user's API keys (without showing actual keys)."""
    from app.models.user import APIKey
    
    api_keys = db.query(APIKey).filter(APIKey.user_id == user_id).all()
    
    return [
        APIKeyListResponse(
            id=key.id,
            name=key.name,
            key_preview=f"{key.key[:12]}...{key.key[-6:]}",
            is_active=key.is_active,
            created_at=key.created_at,
            last_used=key.last_used
        )
        for key in api_keys
    ]


@router.delete("/api-keys/{key_id}", response_model=SuccessResponse)
def delete_api_key(
    key_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Delete API key."""
    from app.models.user import APIKey
    
    api_key = db.query(APIKey).filter(
        APIKey.id == key_id,
        APIKey.user_id == user_id
    ).first()
    
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    db.delete(api_key)
    db.commit()
    
    return SuccessResponse(message="API key deleted successfully")