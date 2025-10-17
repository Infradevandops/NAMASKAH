"""Activity Tracking System for User Actions"""

from sqlalchemy import Column, String, DateTime, Text, Integer
from datetime import datetime, timezone
from main import Base, engine, SessionLocal

class ActivityLog(Base):
    __tablename__ = "activity_logs"
    
    id = Column(String, primary_key=True)
    user_id = Column(String)  # nullable for anonymous users
    email = Column(String)
    action = Column(String, nullable=False)  # register, login, fund_wallet, create_verification
    status = Column(String, nullable=False)  # success, failed, pending
    details = Column(Text)  # JSON string with additional info
    ip_address = Column(String)
    user_agent = Column(String)
    error_message = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class PaymentLog(Base):
    __tablename__ = "payment_logs"
    
    id = Column(String, primary_key=True)
    user_id = Column(String)
    email = Column(String)
    reference = Column(String, unique=True)
    amount_ngn = Column(Integer)  # in kobo
    amount_usd = Column(Integer)  # in cents
    namaskah_amount = Column(Integer)  # in N
    status = Column(String)  # initialized, pending, success, failed
    payment_method = Column(String)  # paystack, bitcoin, etc
    webhook_received = Column(String)  # yes, no, pending
    credited = Column(String)  # yes, no
    error_message = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime)

# Create tables
Base.metadata.create_all(bind=engine)

def log_activity(user_id=None, email=None, action=None, status=None, details=None, error=None):
    """Log user activity"""
    db = SessionLocal()
    try:
        log = ActivityLog(
            id=f"log_{datetime.now(timezone.utc).timestamp()}",
            user_id=user_id,
            email=email,
            action=action,
            status=status,
            details=details,
            error_message=error,
        )
        db.add(log)
        db.commit()
    except Exception as e:
        print(f"Activity log error: {e}")
    finally:
        db.close()

def log_payment(user_id=None, email=None, reference=None, amount_ngn=0, status="initialized", **kwargs):
    """Log payment attempt"""
    db = SessionLocal()
    try:
        log = PaymentLog(
            id=f"pay_{datetime.now(timezone.utc).timestamp()}",
            user_id=user_id,
            email=email,
            reference=reference,
            amount_ngn=amount_ngn,
            status=status,
            webhook_received="pending",
            credited="no",
            **kwargs
        )
        db.add(log)
        db.commit()
    except Exception as e:
        print(f"Payment log error: {e}")
    finally:
        db.close()

def check_payment_logs(email=None, reference=None):
    """Check payment logs for user"""
    db = SessionLocal()
    try:
        query = db.query(PaymentLog)
        if email:
            query = query.filter(PaymentLog.email == email)
        if reference:
            query = query.filter(PaymentLog.reference == reference)
        
        logs = query.order_by(PaymentLog.created_at.desc()).all()
        
        print(f"\n{'='*80}")
        print(f"💳 PAYMENT LOGS")
        print(f"{'='*80}")
        
        if not logs:
            print("No payment logs found")
            return
        
        for log in logs:
            print(f"\nReference: {log.reference}")
            print(f"Email: {log.email}")
            print(f"Amount: ₦{log.amount_ngn/100:.2f} → N{log.namaskah_amount}")
            print(f"Status: {log.status}")
            print(f"Webhook: {log.webhook_received}")
            print(f"Credited: {log.credited}")
            print(f"Created: {log.created_at}")
            if log.error_message:
                print(f"Error: {log.error_message}")
    finally:
        db.close()

def check_activity_logs(email=None, action=None):
    """Check activity logs"""
    db = SessionLocal()
    try:
        query = db.query(ActivityLog)
        if email:
            query = query.filter(ActivityLog.email == email)
        if action:
            query = query.filter(ActivityLog.action == action)
        
        logs = query.order_by(ActivityLog.created_at.desc()).limit(50).all()
        
        print(f"\n{'='*80}")
        print(f"📊 ACTIVITY LOGS")
        print(f"{'='*80}")
        
        if not logs:
            print("No activity logs found")
            return
        
        for log in logs:
            status_icon = "✅" if log.status == "success" else "❌" if log.status == "failed" else "⏳"
            print(f"{status_icon} {log.created_at} | {log.action} | {log.status} | {log.email or 'anonymous'}")
            if log.error_message:
                print(f"   Error: {log.error_message}")
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("\n📊 Activity Tracker\n")
        print("Usage:")
        print("  python activity_tracker.py activity <email>     - Check user activity")
        print("  python activity_tracker.py payments <email>     - Check payment logs")
        print("  python activity_tracker.py reference <ref>      - Check by payment reference")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "activity":
        email = sys.argv[2] if len(sys.argv) > 2 else None
        check_activity_logs(email=email)
    elif command == "payments":
        email = sys.argv[2] if len(sys.argv) > 2 else None
        check_payment_logs(email=email)
    elif command == "reference":
        reference = sys.argv[2] if len(sys.argv) > 2 else None
        check_payment_logs(reference=reference)
