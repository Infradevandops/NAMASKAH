#!/usr/bin/env python3
"""
Database service for CumApp Platform
Provides database session management
"""
from sqlalchemy.orm import Session
from models.database import SessionLocal

def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()