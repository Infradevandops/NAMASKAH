"""Transaction and payment-related database models."""
from sqlalchemy import Column, String, Float, Boolean, DateTime
from app.models.base import BaseModel


class Transaction(BaseModel):
    """Financial transaction model."""
    __tablename__ = "transactions"
    
    user_id = Column(String, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    type = Column(String, nullable=False, index=True)  # credit, debit
    description = Column(String)


class PaymentLog(BaseModel):
    """Payment processing log."""
    __tablename__ = "payment_logs"
    
    user_id = Column(String, index=True)
    email = Column(String)
    reference = Column(String, unique=True, index=True)
    amount_ngn = Column(Float)
    amount_usd = Column(Float)
    namaskah_amount = Column(Float)
    status = Column(String, index=True)
    payment_method = Column(String)
    webhook_received = Column(Boolean, default=False, nullable=False)
    credited = Column(Boolean, default=False, nullable=False)
    error_message = Column(String)