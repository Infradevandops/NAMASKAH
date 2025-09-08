#!/usr/bin/env python3
"""
Enhanced Chat Interface API endpoints
"""
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import logging

from database import get_db
from models import User
from services.auth_service import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["enhanced-chat"])
templates = Jinja2Templates(directory="templates")

@router.get("/demo", response_class=HTMLResponse)
async def enhanced_chat_demo(request: Request):
    """
    Serve the enhanced chat demo page (no authentication required)
    """
    return templates.TemplateResponse("enhanced_chat_demo.html", {"request": request})

@router.get("/marketplace", response_class=HTMLResponse)
async def phone_number_marketplace(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Serve the phone number marketplace interface
    """
    try:
        # Get user's current phone numbers for context
        from services.phone_number_service import PhoneNumberService
        phone_service = PhoneNumberService(db)
        
        owned_numbers, total_count = await phone_service.get_owned_numbers(
            current_user.id, include_inactive=False
        )
        
        context = {
            "request": request,
            "user": current_user,
            "owned_numbers_count": total_count,
            "has_numbers": total_count > 0
        }
        
        return templates.TemplateResponse("phone_number_marketplace.html", context)
        
    except Exception as e:
        logger.error(f"Error serving phone marketplace: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load phone marketplace"
        )

@router.get("/enhanced", response_class=HTMLResponse)
async def enhanced_chat_interface(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Serve the enhanced chat interface
    """
    try:
        # Get user's conversation count for context
        from services.conversation_service import ConversationService
        conversation_service = ConversationService(db)
        
        conversations, total_count = await conversation_service.get_user_conversations(
            current_user.id, limit=1, offset=0
        )
        
        context = {
            "request": request,
            "user": current_user,
            "conversation_count": total_count,
            "has_conversations": total_count > 0
        }
        
        return templates.TemplateResponse("enhanced_chat.html", context)
        
    except Exception as e:
        logger.error(f"Error serving enhanced chat interface: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load chat interface"
        )

@router.get("/search", response_class=HTMLResponse)
async def enhanced_chat_with_search(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Serve the enhanced chat interface with advanced search and infinite scroll
    """
    try:
        # Get user's conversation count for context
        from services.conversation_service import ConversationService
        conversation_service = ConversationService(db)
        
        conversations, total_count = await conversation_service.get_user_conversations(
            current_user.id, limit=10, offset=0
        )
        
        context = {
            "request": request,
            "user": current_user,
            "conversations": conversations,
            "conversation_count": total_count,
            "has_conversations": total_count > 0
        }
        
        return templates.TemplateResponse("enhanced_chat_with_search.html", context)
        
    except Exception as e:
        logger.error(f"Error serving enhanced chat with search: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load chat interface"
        )

@router.get("/features", response_model=dict)
async def get_chat_features(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get available chat features for the current user
    """
    try:
        features = {
            "message_threading": True,
            "typing_indicators": True,
            "read_receipts": True,
            "desktop_notifications": True,
            "infinite_scroll": True,
            "message_search": True,
            "file_attachments": False,  # Not implemented yet
            "emoji_reactions": False,   # Not implemented yet
            "message_editing": True,
            "message_deletion": True,
            "conversation_muting": True,
            "user_presence": True,
            "group_conversations": True,
            "sms_integration": True
        }
        
        # Check user subscription level for premium features
        if hasattr(current_user, 'subscription_plan'):
            if current_user.subscription_plan in ['PREMIUM', 'ENTERPRISE']:
                features.update({
                    "file_attachments": True,
                    "emoji_reactions": True,
                    "advanced_search": True,
                    "message_scheduling": True,
                    "conversation_analytics": True
                })
        
        return {
            "user_id": current_user.id,
            "features": features,
            "limits": {
                "max_conversation_participants": 50,
                "max_message_length": 4000,
                "max_file_size_mb": 10,
                "daily_message_limit": 1000
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting chat features: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get chat features"
        )

@router.get("/settings", response_model=dict)
async def get_chat_settings(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get user's chat settings and preferences
    """
    try:
        # In a real implementation, you'd fetch these from a user_settings table
        default_settings = {
            "notifications": {
                "desktop_enabled": True,
                "sound_enabled": True,
                "email_enabled": False,
                "push_enabled": True
            },
            "chat_preferences": {
                "show_timestamps": True,
                "show_read_receipts": True,
                "auto_scroll": True,
                "compact_mode": False,
                "dark_theme": False
            },
            "privacy": {
                "show_online_status": True,
                "show_typing_indicators": True,
                "allow_message_forwarding": True,
                "read_receipt_privacy": "all"  # all, contacts, none
            },
            "advanced": {
                "message_preview_length": 100,
                "conversation_auto_archive_days": 30,
                "typing_indicator_timeout_ms": 1000
            }
        }
        
        return {
            "user_id": current_user.id,
            "settings": default_settings
        }
        
    except Exception as e:
        logger.error(f"Error getting chat settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get chat settings"
        )

@router.put("/settings", response_model=dict)
async def update_chat_settings(
    settings: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update user's chat settings and preferences
    """
    try:
        # In a real implementation, you'd save these to a user_settings table
        # For now, we'll just validate and return the settings
        
        valid_sections = ['notifications', 'chat_preferences', 'privacy', 'advanced']
        
        for section in settings:
            if section not in valid_sections:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid settings section: {section}"
                )
        
        # Here you would save to database
        # user_settings_service.update_settings(current_user.id, settings)
        
        return {
            "success": True,
            "message": "Chat settings updated successfully",
            "updated_settings": settings
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating chat settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update chat settings"
        )

@router.get("/health")
async def enhanced_chat_health():
    """
    Health check for enhanced chat interface
    """
    return {
        "status": "healthy",
        "service": "enhanced_chat",
        "version": "1.1.0",
        "features": [
            "message_threading",
            "typing_indicators", 
            "read_receipts",
            "desktop_notifications",
            "infinite_scroll",
            "message_search",
            "user_presence",
            "conversation_management"
        ]
    }