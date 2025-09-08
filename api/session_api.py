#!/usr/bin/env python3
"""
Session Management API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import logging

from database import get_db
from models.user_models import User, Session as UserSession
from middleware.auth_middleware import SessionManager, get_current_user_from_middleware

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sessions", tags=["session_management"])

# Pydantic models
class SessionResponse(BaseModel):
    id: str
    user_agent: Optional[str]
    ip_address: Optional[str]
    created_at: datetime
    last_used: datetime
    is_active: bool
    is_current: bool

class SessionListResponse(BaseModel):
    sessions: List[SessionResponse]
    total_count: int
    active_count: int

@router.get("/", response_model=SessionListResponse)
async def list_user_sessions(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    List all sessions for the current user
    """
    try:
        current_user = get_current_user_from_middleware(request)
        
        # Get current session token from request
        auth_header = request.headers.get("Authorization", "")
        current_token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else None
        
        # Query user sessions
        sessions = db.query(UserSession).filter(
            UserSession.user_id == current_user.id
        ).order_by(UserSession.last_used.desc()).all()
        
        session_responses = []
        for session in sessions:
            is_current = (current_token and 
                         session.refresh_token == current_token and 
                         session.is_active)
            
            session_responses.append(SessionResponse(
                id=session.id,
                user_agent=session.user_agent,
                ip_address=session.ip_address,
                created_at=session.created_at,
                last_used=session.last_used,
                is_active=session.is_active,
                is_current=is_current
            ))
        
        active_count = sum(1 for s in sessions if s.is_active)
        
        return SessionListResponse(
            sessions=session_responses,
            total_count=len(sessions),
            active_count=active_count
        )
        
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list sessions"
        )

@router.delete("/{session_id}")
async def revoke_session(
    session_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Revoke a specific session
    """
    try:
        current_user = get_current_user_from_middleware(request)
        
        # Find the session
        session = db.query(UserSession).filter(
            UserSession.id == session_id,
            UserSession.user_id == current_user.id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Revoke the session
        session_manager = SessionManager(db)
        success = await session_manager.invalidate_session(session.refresh_token)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to revoke session"
            )
        
        logger.info(f"Session {session_id} revoked for user {current_user.id}")
        
        return {"message": "Session revoked successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke session"
        )

@router.delete("/")
async def revoke_all_sessions(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Revoke all sessions for the current user (except current session)
    """
    try:
        current_user = get_current_user_from_middleware(request)
        
        # Get current session token
        auth_header = request.headers.get("Authorization", "")
        current_token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else None
        
        # Get all sessions except current
        sessions_to_revoke = db.query(UserSession).filter(
            UserSession.user_id == current_user.id,
            UserSession.is_active == True
        )
        
        if current_token:
            sessions_to_revoke = sessions_to_revoke.filter(
                UserSession.refresh_token != current_token
            )
        
        sessions = sessions_to_revoke.all()
        
        # Revoke all sessions
        session_manager = SessionManager(db)
        revoked_count = 0
        
        for session in sessions:
            success = await session_manager.invalidate_session(session.refresh_token)
            if success:
                revoked_count += 1
        
        logger.info(f"Revoked {revoked_count} sessions for user {current_user.id}")
        
        return {
            "message": f"Revoked {revoked_count} sessions successfully",
            "revoked_count": revoked_count
        }
        
    except Exception as e:
        logger.error(f"Error revoking all sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke sessions"
        )

@router.post("/cleanup")
async def cleanup_expired_sessions(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Clean up expired sessions (admin function)
    """
    try:
        current_user = get_current_user_from_middleware(request)
        
        # Only allow admin users to cleanup sessions
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        session_manager = SessionManager(db)
        cleaned_count = await session_manager.cleanup_expired_sessions()
        
        logger.info(f"Cleaned up {cleaned_count} expired sessions")
        
        return {
            "message": f"Cleaned up {cleaned_count} expired sessions",
            "cleaned_count": cleaned_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cleaning up sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup sessions"
        )

@router.get("/stats")
async def get_session_stats(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Get session statistics for the current user
    """
    try:
        current_user = get_current_user_from_middleware(request)
        
        # Count sessions
        total_sessions = db.query(UserSession).filter(
            UserSession.user_id == current_user.id
        ).count()
        
        active_sessions = db.query(UserSession).filter(
            UserSession.user_id == current_user.id,
            UserSession.is_active == True
        ).count()
        
        # Get most recent session
        latest_session = db.query(UserSession).filter(
            UserSession.user_id == current_user.id
        ).order_by(UserSession.last_used.desc()).first()
        
        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "latest_activity": latest_session.last_used.isoformat() if latest_session else None,
            "user_id": current_user.id
        }
        
    except Exception as e:
        logger.error(f"Error getting session stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get session statistics"
        )