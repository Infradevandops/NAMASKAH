"""Verification-related database models."""

from sqlalchemy import Column, String, Float, DateTime, Boolean
from app.models.base import BaseModel


class Verification(BaseModel):
    """SMS/Voice verification model."""

    __tablename__ = "verifications"

    user_id = Column(String, nullable=False, index=True)
    service_name = Column(String, nullable=False, index=True)
    phone_number = Column(String)
    capability = Column(String, default="sms", nullable=False)
    status = Column(String, default="pending", nullable=False, index=True)
    verification_code = Column(String)
    cost = Column(Float, nullable=False)
    call_duration = Column(Float)
    transcription = Column(String)
    audio_url = Column(String)
    requested_carrier = Column(String)
    requested_area_code = Column(String)
    completed_at = Column(DateTime)


class NumberRental(BaseModel):
    """Number rental for extended use."""

    __tablename__ = "number_rentals"

    user_id = Column(String, nullable=False, index=True)
    phone_number = Column(String, nullable=False)
    service_name = Column(String)
    duration_hours = Column(Float, nullable=False)
    cost = Column(Float, nullable=False)
    mode = Column(String, default="always_ready", nullable=False)
    status = Column(String, default="active", nullable=False, index=True)
    started_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    released_at = Column(DateTime)
    auto_extend = Column(Boolean, default=False, nullable=False)
    warning_sent = Column(Boolean, default=False, nullable=False)


class VerificationReceipt(BaseModel):
    """Receipt for completed verifications."""

    __tablename__ = "verification_receipts"

    user_id = Column(String, nullable=False, index=True)
    verification_id = Column(String, nullable=False, index=True)
    service_name = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    amount_spent = Column(Float, nullable=False)
    isp_carrier = Column(String)
    area_code = Column(String)
    success_timestamp = Column(DateTime, nullable=False)
    receipt_data = Column(String)
