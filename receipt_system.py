# Receipt and Notification System Module
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any

class VerificationReceipt:
    """Verification receipt data structure"""
    def __init__(self, verification_id, service_name, phone_number, amount_spent, isp_carrier=None, area_code=None):
        self.verification_id = verification_id
        self.service_name = service_name
        self.phone_number = phone_number
        self.amount_spent = amount_spent
        self.isp_carrier = isp_carrier
        self.area_code = area_code
        self.success_timestamp = datetime.now(timezone.utc)

class NotificationPreferences:
    """User notification preferences"""
    def __init__(self, user_id):
        self.user_id = user_id
        self.in_app_notifications = True
        self.email_notifications = True
        self.receipt_notifications = True

class InAppNotification:
    """In-app notification data structure"""
    def __init__(self, user_id, title, message, notification_type="receipt", verification_id=None):
        self.user_id = user_id
        self.title = title
        self.message = message
        self.type = notification_type
        self.verification_id = verification_id
        self.is_read = False
        self.created_at = datetime.now(timezone.utc)

class ReceiptService:
    """Service for managing verification receipts"""
    def __init__(self, db):
        self.db = db

    def create_receipt(self, user_id, verification_id, service_name, phone_number, amount_spent, isp_carrier=None):
        """Create a new verification receipt"""
        from main import VerificationReceipt as ReceiptModel
        
        receipt_data = {
            "verification_id": verification_id,
            "service_name": service_name,
            "phone_number": phone_number,
            "amount_spent": amount_spent,
            "isp_carrier": isp_carrier,
            "success_timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        receipt = ReceiptModel(
            id=f"receipt_{datetime.now(timezone.utc).timestamp()}",
            user_id=user_id,
            verification_id=verification_id,
            service_name=service_name,
            phone_number=phone_number,
            amount_spent=amount_spent,
            isp_carrier=isp_carrier or "Unknown",
            area_code=phone_number[:3] if phone_number else None,
            success_timestamp=datetime.now(timezone.utc),
            receipt_data=json.dumps(receipt_data)
        )
        
        self.db.add(receipt)
        self.db.commit()
        return receipt

    def get_user_receipts(self, user_id, limit=50):
        """Get receipts for a user"""
        from main import VerificationReceipt as ReceiptModel
        
        receipts = self.db.query(ReceiptModel).filter(
            ReceiptModel.user_id == user_id
        ).order_by(ReceiptModel.created_at.desc()).limit(limit).all()
        
        return [
            {
                "id": r.id,
                "verification_id": r.verification_id,
                "service_name": r.service_name,
                "phone_number": r.phone_number,
                "amount_spent": r.amount_spent,
                "isp_carrier": r.isp_carrier,
                "success_timestamp": r.success_timestamp.isoformat(),
                "receipt_number": f"NSK-{r.verification_id[-8:].upper()}"
            }
            for r in receipts
        ]

class NotificationService:
    """Service for managing notifications"""
    def __init__(self, db):
        self.db = db

    def create_notification(self, user_id, title, message, notification_type="info", verification_id=None):
        """Create a new in-app notification"""
        from main import InAppNotification as NotificationModel
        
        notification = NotificationModel(
            id=f"notif_{datetime.now(timezone.utc).timestamp()}",
            user_id=user_id,
            title=title,
            message=message,
            type=notification_type,
            verification_id=verification_id,
            is_read=False
        )
        
        self.db.add(notification)
        self.db.commit()
        return notification

    def get_user_notifications(self, user_id, unread_only=False, limit=50):
        """Get notifications for a user"""
        from main import InAppNotification as NotificationModel
        
        query = self.db.query(NotificationModel).filter(
            NotificationModel.user_id == user_id
        )
        
        if unread_only:
            query = query.filter(NotificationModel.is_read == False)
        
        notifications = query.order_by(NotificationModel.created_at.desc()).limit(limit).all()
        
        return [
            {
                "id": n.id,
                "title": n.title,
                "message": n.message,
                "type": n.type,
                "is_read": n.is_read,
                "verification_id": n.verification_id,
                "created_at": n.created_at.isoformat()
            }
            for n in notifications
        ]

    def mark_notification_read(self, notification_id, user_id):
        """Mark notification as read"""
        from main import InAppNotification as NotificationModel
        
        notification = self.db.query(NotificationModel).filter(
            NotificationModel.id == notification_id,
            NotificationModel.user_id == user_id
        ).first()
        
        if notification:
            notification.is_read = True
            self.db.commit()
            return True
        return False

    def mark_all_read(self, user_id):
        """Mark all notifications as read for user"""
        from main import InAppNotification as NotificationModel
        
        self.db.query(NotificationModel).filter(
            NotificationModel.user_id == user_id,
            NotificationModel.is_read == False
        ).update({"is_read": True})
        self.db.commit()

    def get_notification_preferences(self, user_id):
        """Get user notification preferences"""
        from main import NotificationPreferences as PrefsModel
        
        prefs = self.db.query(PrefsModel).filter(
            PrefsModel.user_id == user_id
        ).first()
        
        if not prefs:
            # Create default preferences
            prefs = PrefsModel(
                id=f"prefs_{datetime.now(timezone.utc).timestamp()}",
                user_id=user_id,
                in_app_notifications=True,
                email_notifications=True,
                receipt_notifications=True
            )
            self.db.add(prefs)
            self.db.commit()
        
        return {
            "in_app_notifications": prefs.in_app_notifications,
            "email_notifications": prefs.email_notifications,
            "receipt_notifications": prefs.receipt_notifications
        }

    def update_notification_preferences(self, user_id, **kwargs):
        """Update notification preferences"""
        from main import NotificationPreferences as PrefsModel
        
        prefs = self.db.query(PrefsModel).filter(
            PrefsModel.user_id == user_id
        ).first()
        
        if not prefs:
            prefs = PrefsModel(
                id=f"prefs_{datetime.now(timezone.utc).timestamp()}",
                user_id=user_id
            )
            self.db.add(prefs)
        
        for key, value in kwargs.items():
            if value is not None and hasattr(prefs, key):
                setattr(prefs, key, value)
        
        self.db.commit()
        return self.get_notification_preferences(user_id)

def process_successful_verification(db, user_id, user_email, verification_id, service_name, phone_number, amount_spent, isp_carrier=None):
    """Process successful verification and create receipt/notification"""
    try:
        # Create receipt
        receipt_service = ReceiptService(db)
        receipt = receipt_service.create_receipt(
            user_id=user_id,
            verification_id=verification_id,
            service_name=service_name,
            phone_number=phone_number,
            amount_spent=amount_spent,
            isp_carrier=isp_carrier
        )
        
        # Create notification
        notification_service = NotificationService(db)
        notification_service.create_notification(
            user_id=user_id,
            title="✅ Verification Successful",
            message=f"Your {service_name} verification completed successfully. Receipt: NSK-{verification_id[-8:].upper()}",
            notification_type="success",
            verification_id=verification_id
        )
        
        return receipt
        
    except Exception as e:
        print(f"Receipt processing error: {e}")
        return None