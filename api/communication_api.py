#!/usr/bin/env python3
"""
Enhanced Communication API for CumApp Platform
Handles conversations, messaging, and real-time communication
"""
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import logging

from models.user_models import (
    User, Conversation, Message, PhoneNumber, VerificationRequest,
    ConversationCreate, ConversationResponse, MessageCreate, MessageResponse,
    VerificationCreate, VerificationResponse, MessageType, ConversationStatus
)
from services.database import get_db
from services.auth_service import get_current_user
from services.websocket_manager import ConnectionManager
from services.sms_service import SMSService
from services.verification_service import VerificationService
from textverified_client import TextVerifiedClient
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["communication"])
security = HTTPBearer()

# WebSocket connection manager
connection_manager = ConnectionManager()

# --- Conversation Management ---

@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    conversation: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new conversation"""
    try:
        # Create conversation
        db_conversation = Conversation(
            title=conversation.title,
            external_number=conversation.external_number,
            is_group=conversation.is_group
        )
        
        # Add current user as participant
        db_conversation.participants.append(current_user)
        
        # Add other participants if specified
        if conversation.participant_ids:
            participants = db.query(User).filter(User.id.in_(conversation.participant_ids)).all()
            db_conversation.participants.extend(participants)
        
        db.add(db_conversation)
        db.commit()
        db.refresh(db_conversation)
        
        logger.info(f"Created conversation {db_conversation.id} by user {current_user.id}")
        
        return ConversationResponse(
            id=db_conversation.id,
            title=db_conversation.title,
            is_group=db_conversation.is_group,
            external_number=db_conversation.external_number,
            status=db_conversation.status,
            created_at=db_conversation.created_at,
            last_message_at=db_conversation.last_message_at,
            participant_count=len(db_conversation.participants)
        )
        
    except Exception as e:
        logger.error(f"Failed to create conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to create conversation")

@router.get("/conversations", response_model=List[ConversationResponse])
async def get_user_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0
):
    """Get user's conversations"""
    try:
        conversations = db.query(Conversation)\
            .join(Conversation.participants)\
            .filter(User.id == current_user.id)\
            .filter(Conversation.status == ConversationStatus.ACTIVE)\
            .order_by(Conversation.last_message_at.desc())\
            .offset(offset)\
            .limit(limit)\
            .all()
        
        return [
            ConversationResponse(
                id=conv.id,
                title=conv.title or f"Chat with {conv.external_number}" if conv.external_number else "Group Chat",
                is_group=conv.is_group,
                external_number=conv.external_number,
                status=conv.status,
                created_at=conv.created_at,
                last_message_at=conv.last_message_at,
                participant_count=len(conv.participants)
            )
            for conv in conversations
        ]
        
    except Exception as e:
        logger.error(f"Failed to get conversations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get conversations")

@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_conversation_messages(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0
):
    """Get messages in a conversation"""
    try:
        # Verify user is participant
        conversation = db.query(Conversation)\
            .join(Conversation.participants)\
            .filter(Conversation.id == conversation_id)\
            .filter(User.id == current_user.id)\
            .first()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        messages = db.query(Message)\
            .filter(Message.conversation_id == conversation_id)\
            .order_by(Message.created_at.desc())\
            .offset(offset)\
            .limit(limit)\
            .all()
        
        return [
            MessageResponse(
                id=msg.id,
                conversation_id=msg.conversation_id,
                sender_id=msg.sender_id,
                content=msg.content,
                message_type=msg.message_type,
                is_delivered=msg.is_delivered,
                is_read=msg.is_read,
                created_at=msg.created_at,
                from_number=msg.from_number,
                to_number=msg.to_number
            )
            for msg in reversed(messages)  # Return in chronological order
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get messages: {e}")
        raise HTTPException(status_code=500, detail="Failed to get messages")

# --- Messaging ---

@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(
    conversation_id: str,
    message: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a message in a conversation"""
    try:
        # Verify user is participant
        conversation = db.query(Conversation)\
            .join(Conversation.participants)\
            .filter(Conversation.id == conversation_id)\
            .filter(User.id == current_user.id)\
            .first()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Create message
        db_message = Message(
            conversation_id=conversation_id,
            sender_id=current_user.id,
            content=message.content,
            message_type=message.message_type
        )
        
        # Handle SMS messages to external numbers
        if message.message_type == MessageType.SMS and conversation.external_number:
            # Get user's phone number for sending
            user_number = db.query(PhoneNumber)\
                .filter(PhoneNumber.owner_id == current_user.id)\
                .filter(PhoneNumber.is_active == True)\
                .first()
            
            if not user_number:
                raise HTTPException(status_code=400, detail="No active phone number found")
            
            # Send SMS via SMS service
            sms_service = SMSService()
            sms_result = await sms_service.send_sms(
                from_number=user_number.phone_number,
                to_number=conversation.external_number,
                message=message.content
            )
            
            db_message.external_message_id = sms_result.get("message_sid")
            db_message.from_number = user_number.phone_number
            db_message.to_number = conversation.external_number
            db_message.is_delivered = True
        
        db.add(db_message)
        
        # Update conversation last message time
        conversation.last_message_at = datetime.utcnow()
        
        db.commit()
        db.refresh(db_message)
        
        # Send real-time notification via WebSocket
        await connection_manager.send_to_conversation(
            conversation_id,
            {
                "type": "new_message",
                "message": {
                    "id": db_message.id,
                    "sender_id": db_message.sender_id,
                    "content": db_message.content,
                    "message_type": db_message.message_type,
                    "created_at": db_message.created_at.isoformat()
                }
            }
        )
        
        logger.info(f"Message sent in conversation {conversation_id} by user {current_user.id}")
        
        return MessageResponse(
            id=db_message.id,
            conversation_id=db_message.conversation_id,
            sender_id=db_message.sender_id,
            content=db_message.content,
            message_type=db_message.message_type,
            is_delivered=db_message.is_delivered,
            is_read=db_message.is_read,
            created_at=db_message.created_at,
            from_number=db_message.from_number,
            to_number=db_message.to_number
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        raise HTTPException(status_code=500, detail="Failed to send message")

# --- External Number Communication ---

@router.post("/external/sms/send")
async def send_external_sms(
    to_number: str,
    message: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send SMS to external number and create/update conversation"""
    try:
        # Get or create conversation with external number
        conversation = db.query(Conversation)\
            .join(Conversation.participants)\
            .filter(Conversation.external_number == to_number)\
            .filter(User.id == current_user.id)\
            .first()
        
        if not conversation:
            # Create new conversation
            conversation = Conversation(
                title=f"SMS with {to_number}",
                external_number=to_number,
                is_group=False
            )
            conversation.participants.append(current_user)
            db.add(conversation)
            db.flush()  # Get the ID
        
        # Send the message
        message_response = await send_message(
            conversation.id,
            MessageCreate(
                conversation_id=conversation.id,
                content=message,
                message_type=MessageType.SMS,
                to_number=to_number
            ),
            current_user,
            db
        )
        
        return {
            "conversation_id": conversation.id,
            "message": message_response,
            "status": "sent"
        }
        
    except Exception as e:
        logger.error(f"Failed to send external SMS: {e}")
        raise HTTPException(status_code=500, detail="Failed to send SMS")

# --- TextVerified Integration ---

@router.post("/verification/create", response_model=VerificationResponse)
async def create_verification(
    verification: VerificationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a TextVerified verification request"""
    try:
        # Initialize TextVerified client
        textverified_client = TextVerifiedClient(
            api_key=os.getenv("TEXTVERIFIED_API_KEY"),
            email=os.getenv("TEXTVERIFIED_EMAIL")
        )
        
        # Create verification service
        verification_service = VerificationService(db, textverified_client)
        
        # Create verification
        db_verification = await verification_service.create_verification(
            user_id=current_user.id,
            service_name=verification.service_name,
            capability=verification.capability
        )
        
        logger.info(f"Created verification {db_verification.id} for user {current_user.id}")
        
        return VerificationResponse(
            id=db_verification.id,
            textverified_id=db_verification.textverified_id,
            service_name=db_verification.service_name,
            phone_number=db_verification.phone_number,
            status=db_verification.status,
            verification_code=db_verification.verification_code,
            created_at=db_verification.created_at,
            expires_at=db_verification.expires_at
        )
        
    except Exception as e:
        logger.error(f"Failed to create verification: {e}")
        raise HTTPException(status_code=500, detail="Failed to create verification")

@router.get("/verification/{verification_id}/number")
async def get_verification_number(
    verification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get phone number for verification"""
    try:
        # Initialize TextVerified client and service
        textverified_client = TextVerifiedClient(
            api_key=os.getenv("TEXTVERIFIED_API_KEY"),
            email=os.getenv("TEXTVERIFIED_EMAIL")
        )
        verification_service = VerificationService(db, textverified_client)
        
        # Get phone number
        phone_number = await verification_service.get_verification_number(
            user_id=current_user.id,
            verification_id=verification_id
        )
        
        # Get verification for response
        verification = db.query(VerificationRequest)\
            .filter(VerificationRequest.id == verification_id)\
            .filter(VerificationRequest.user_id == current_user.id)\
            .first()
        
        return {
            "verification_id": verification_id,
            "phone_number": phone_number,
            "service_name": verification.service_name
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get verification number: {e}")
        raise HTTPException(status_code=500, detail="Failed to get verification number")

@router.get("/verification/{verification_id}/messages")
async def get_verification_messages(
    verification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get SMS messages for verification with automatic code extraction"""
    try:
        # Initialize TextVerified client and service
        textverified_client = TextVerifiedClient(
            api_key=os.getenv("TEXTVERIFIED_API_KEY"),
            email=os.getenv("TEXTVERIFIED_EMAIL")
        )
        verification_service = VerificationService(db, textverified_client)
        
        # Check messages and extract codes
        messages = await verification_service.check_verification_messages(
            user_id=current_user.id,
            verification_id=verification_id
        )
        
        # Get updated verification status
        verification = db.query(VerificationRequest)\
            .filter(VerificationRequest.id == verification_id)\
            .filter(VerificationRequest.user_id == current_user.id)\
            .first()
        
        return {
            "verification_id": verification_id,
            "messages": messages,
            "status": verification.status,
            "verification_code": verification.verification_code,
            "completed_at": verification.completed_at.isoformat() if verification.completed_at else None
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get verification messages: {e}")
        raise HTTPException(status_code=500, detail="Failed to get verification messages")

# --- WebSocket for Real-time Communication ---

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time communication"""
    await connection_manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            message_type = message.get("type")
            
            if message_type == "typing":
                conversation_id = message.get("conversation_id")
                is_typing = message.get("is_typing", False)
                
                if conversation_id:
                    await connection_manager.handle_typing_indicator(
                        user_id, conversation_id, is_typing
                    )
            
            elif message_type == "message_read":
                conversation_id = message.get("conversation_id")
                message_id = message.get("message_id")
                
                if conversation_id and message_id:
                    await connection_manager.handle_message_read(
                        user_id, conversation_id, message_id
                    )
            
            elif message_type == "join_conversation":
                conversation_id = message.get("conversation_id")
                # Handle joining conversation for real-time updates
                pass
                
    except WebSocketDisconnect:
        connection_manager.disconnect(user_id)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        connection_manager.disconnect(user_id)

# --- Phone Number Management ---

@router.get("/numbers/owned", response_model=List[Dict[str, Any]])
async def get_owned_numbers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's owned phone numbers"""
    try:
        numbers = db.query(PhoneNumber)\
            .filter(PhoneNumber.owner_id == current_user.id)\
            .filter(PhoneNumber.is_active == True)\
            .all()
        
        return [
            {
                "id": num.id,
                "phone_number": num.phone_number,
                "country_code": num.country_code,
                "provider": num.provider,
                "monthly_cost": num.monthly_cost,
                "purchased_at": num.purchased_at,
                "expires_at": num.expires_at,
                "total_sms_sent": num.total_sms_sent,
                "total_sms_received": num.total_sms_received
            }
            for num in numbers
        ]
        
    except Exception as e:
        logger.error(f"Failed to get owned numbers: {e}")
        raise HTTPException(status_code=500, detail="Failed to get owned numbers")

@router.post("/numbers/purchase")
async def purchase_number(
    phone_number: str,
    country_code: str,
    provider: str = "twilio",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Purchase a phone number"""
    try:
        # Check if user can purchase (subscription limits, etc.)
        existing_numbers = db.query(PhoneNumber)\
            .filter(PhoneNumber.owner_id == current_user.id)\
            .filter(PhoneNumber.is_active == True)\
            .count()
        
        # Implement subscription-based limits
        max_numbers = {"free": 1, "basic": 3, "premium": 10, "enterprise": 50}
        if existing_numbers >= max_numbers.get(current_user.subscription_plan, 1):
            raise HTTPException(status_code=400, detail="Number limit reached for your subscription")
        
        # Purchase number via provider (mock for now)
        # In real implementation, call Twilio/Vonage API
        
        db_number = PhoneNumber(
            phone_number=phone_number,
            country_code=country_code,
            provider=provider,
            owner_id=current_user.id,
            monthly_cost="$1.00",
            sms_cost_per_message="$0.0075",
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        
        db.add(db_number)
        db.commit()
        db.refresh(db_number)
        
        logger.info(f"User {current_user.id} purchased number {phone_number}")
        
        return {
            "id": db_number.id,
            "phone_number": db_number.phone_number,
            "status": "purchased",
            "monthly_cost": db_number.monthly_cost,
            "expires_at": db_number.expires_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to purchase number: {e}")
        raise HTTPException(status_code=500, detail="Failed to purchase number")

# --- Enhanced Verification Management ---

@router.get("/verification/history", response_model=List[VerificationResponse])
async def get_verification_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    service_name: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    limit: int = 50,
    offset: int = 0
):
    """Get verification history with optional filters"""
    try:
        # Initialize verification service
        textverified_client = TextVerifiedClient(
            api_key=os.getenv("TEXTVERIFIED_API_KEY"),
            email=os.getenv("TEXTVERIFIED_EMAIL")
        )
        verification_service = VerificationService(db, textverified_client)
        
        # Build filters
        filters = {}
        if service_name:
            filters['service_name'] = service_name
        if status:
            filters['status'] = status
        if date_from:
            filters['date_from'] = date_from
        if date_to:
            filters['date_to'] = date_to
        
        # Get history
        verifications = await verification_service.get_verification_history(
            user_id=current_user.id,
            filters=filters
        )
        
        # Apply pagination
        paginated_verifications = verifications[offset:offset + limit]
        
        return [
            VerificationResponse(
                id=v.id,
                textverified_id=v.textverified_id,
                service_name=v.service_name,
                phone_number=v.phone_number,
                status=v.status,
                verification_code=v.verification_code,
                created_at=v.created_at,
                expires_at=v.expires_at
            )
            for v in paginated_verifications
        ]
        
    except Exception as e:
        logger.error(f"Failed to get verification history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get verification history")

@router.get("/verification/search", response_model=List[VerificationResponse])
async def search_verifications(
    query: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    status: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    limit: int = 20
):
    """Search verification history"""
    try:
        # Initialize verification service
        textverified_client = TextVerifiedClient(
            api_key=os.getenv("TEXTVERIFIED_API_KEY"),
            email=os.getenv("TEXTVERIFIED_EMAIL")
        )
        verification_service = VerificationService(db, textverified_client)
        
        # Build filters
        filters = {}
        if status:
            filters['status'] = status
        if date_from:
            filters['date_from'] = date_from
        if date_to:
            filters['date_to'] = date_to
        
        # Search verifications
        verifications = await verification_service.search_verifications(
            user_id=current_user.id,
            search_query=query,
            filters=filters
        )
        
        # Apply limit
        limited_verifications = verifications[:limit]
        
        return [
            VerificationResponse(
                id=v.id,
                textverified_id=v.textverified_id,
                service_name=v.service_name,
                phone_number=v.phone_number,
                status=v.status,
                verification_code=v.verification_code,
                created_at=v.created_at,
                expires_at=v.expires_at
            )
            for v in limited_verifications
        ]
        
    except Exception as e:
        logger.error(f"Failed to search verifications: {e}")
        raise HTTPException(status_code=500, detail="Failed to search verifications")

@router.delete("/verification/{verification_id}")
async def cancel_verification(
    verification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel a verification request"""
    try:
        # Initialize verification service
        textverified_client = TextVerifiedClient(
            api_key=os.getenv("TEXTVERIFIED_API_KEY"),
            email=os.getenv("TEXTVERIFIED_EMAIL")
        )
        verification_service = VerificationService(db, textverified_client)
        
        # Cancel verification
        success = await verification_service.cancel_verification(
            user_id=current_user.id,
            verification_id=verification_id
        )
        
        return {
            "verification_id": verification_id,
            "status": "cancelled" if success else "failed",
            "message": "Verification cancelled successfully" if success else "Failed to cancel verification"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to cancel verification: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel verification")

@router.get("/verification/statistics")
async def get_verification_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    period_days: int = 30
):
    """Get verification statistics for the user"""
    try:
        # Initialize verification service
        textverified_client = TextVerifiedClient(
            api_key=os.getenv("TEXTVERIFIED_API_KEY"),
            email=os.getenv("TEXTVERIFIED_EMAIL")
        )
        verification_service = VerificationService(db, textverified_client)
        
        # Get statistics
        statistics = await verification_service.get_verification_statistics(
            user_id=current_user.id,
            period_days=period_days
        )
        
        return statistics
        
    except Exception as e:
        logger.error(f"Failed to get verification statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get verification statistics")

@router.get("/verification/export")
async def export_verification_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    format_type: str = "json",
    service_name: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None
):
    """Export verification data"""
    try:
        # Initialize verification service
        textverified_client = TextVerifiedClient(
            api_key=os.getenv("TEXTVERIFIED_API_KEY"),
            email=os.getenv("TEXTVERIFIED_EMAIL")
        )
        verification_service = VerificationService(db, textverified_client)
        
        # Build filters
        filters = {}
        if service_name:
            filters['service_name'] = service_name
        if status:
            filters['status'] = status
        if date_from:
            filters['date_from'] = date_from
        if date_to:
            filters['date_to'] = date_to
        
        # Export data
        export_result = await verification_service.export_verification_data(
            user_id=current_user.id,
            format_type=format_type,
            filters=filters
        )
        
        return export_result
        
    except Exception as e:
        logger.error(f"Failed to export verification data: {e}")
        raise HTTPException(status_code=500, detail="Failed to export verification data")