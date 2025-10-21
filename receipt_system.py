"""Receipt and Notification System for Successful Verifications"""
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Boolean, Float, Text
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import json
import requests
from email_service import email_service

class VerificationReceipt:
    """Model for verification receipts"""
    __tablename__ = "verification_receipts"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    verification_id = Column(String, nullable=False)
    service_name = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    amount_spent = Column(Float, nullable=False)
    isp_carrier = Column(String)
    area_code = Column(String)
    success_timestamp = Column(DateTime, nullable=False)
    receipt_data = Column(Text)  # JSON data
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class NotificationPreferences:
    """Model for user notification preferences"""
    __tablename__ = "notification_preferences"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, unique=True, nullable=False)
    in_app_notifications = Column(Boolean, default=True)
    email_notifications = Column(Boolean, default=True)
    receipt_notifications = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime)

class InAppNotification:
    """Model for in-app notifications"""
    __tablename__ = "in_app_notifications"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String, default="receipt")  # receipt, success, info
    is_read = Column(Boolean, default=False)
    verification_id = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class ReceiptService:
    """Service for generating and sending receipts"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_receipt(
        self,
        user_id: str,
        verification_id: str,
        service_name: str,
        phone_number: str,
        amount_spent: float,
        isp_carrier: Optional[str] = None,
        area_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate receipt for successful verification"""
        
        # Extract area code from phone number if not provided
        if not area_code and phone_number and len(phone_number) >= 10:
            area_code = phone_number[:3]
        
        # Create receipt data
        receipt_data = {
            "verification_id": verification_id,
            "service_name": service_name.title(),
            "phone_number": phone_number,
            "amount_spent": amount_spent,
            "amount_usd": round(amount_spent * 2, 2),  # 1N = $2 USD
            "isp_carrier": isp_carrier or "Unknown",
            "area_code": area_code or "Unknown",
            "success_timestamp": datetime.now(timezone.utc).isoformat(),
            "receipt_number": f"NSK-{verification_id[-8:].upper()}",
            "transaction_type": "SMS Verification"
        }
        
        # Store receipt in database
        receipt = VerificationReceipt(
            id=f"receipt_{datetime.now(timezone.utc).timestamp()}",
            user_id=user_id,
            verification_id=verification_id,
            service_name=service_name,
            phone_number=phone_number,
            amount_spent=amount_spent,
            isp_carrier=isp_carrier,
            area_code=area_code,
            success_timestamp=datetime.now(timezone.utc),
            receipt_data=json.dumps(receipt_data)
        )
        
        self.db.add(receipt)
        self.db.commit()
        
        return receipt_data
    
    def send_receipt_notifications(
        self,
        user_id: str,
        user_email: str,
        receipt_data: Dict[str, Any]
    ):
        """Send receipt via in-app and email notifications"""
        
        # Check user notification preferences
        prefs = self.db.query(NotificationPreferences).filter(
            NotificationPreferences.user_id == user_id
        ).first()
        
        if not prefs:
            # Create default preferences
            prefs = NotificationPreferences(
                id=f"pref_{datetime.now(timezone.utc).timestamp()}",
                user_id=user_id,
                in_app_notifications=True,
                email_notifications=True,
                receipt_notifications=True
            )
            self.db.add(prefs)
            self.db.commit()
        
        # Send in-app notification
        if prefs.in_app_notifications and prefs.receipt_notifications:
            self._create_in_app_notification(user_id, receipt_data)
        
        # Send email notification
        if prefs.email_notifications and prefs.receipt_notifications and user_email:
            self._send_email_receipt(user_email, receipt_data)
    
    def _create_in_app_notification(self, user_id: str, receipt_data: Dict[str, Any]):
        """Create in-app notification for successful verification"""
        
        notification = InAppNotification(
            id=f"notif_{datetime.now(timezone.utc).timestamp()}",
            user_id=user_id,
            title="✅ Verification Successful",
            message=f"Your {receipt_data['service_name']} verification completed successfully. Receipt #{receipt_data['receipt_number']}",
            type="receipt",
            verification_id=receipt_data['verification_id']
        )
        
        self.db.add(notification)
        self.db.commit()
    
    def _send_email_receipt(self, user_email: str, receipt_data: Dict[str, Any]):
        """Send email receipt to user"""
        
        subject = f"📧 Verification Receipt #{receipt_data['receipt_number']} - Namaskah SMS"
        
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px 10px 0 0; text-align: center;">
                <h1 style="margin: 0; font-size: 28px;">✅ Verification Successful</h1>
                <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">Your SMS verification completed successfully</p>
            </div>
            
            <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #e9ecef;">
                <h2 style="color: #333; margin-top: 0;">Receipt Details</h2>
                
                <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #28a745;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #666;">Receipt Number:</td>
                            <td style="padding: 8px 0; color: #333;">{receipt_data['receipt_number']}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #666;">Service Used:</td>
                            <td style="padding: 8px 0; color: #333;">{receipt_data['service_name']}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #666;">Phone Number:</td>
                            <td style="padding: 8px 0; color: #333; font-family: monospace;">{receipt_data['phone_number']}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #666;">ISP/Carrier:</td>
                            <td style="padding: 8px 0; color: #333;">{receipt_data['isp_carrier']}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #666;">Area Code:</td>
                            <td style="padding: 8px 0; color: #333;">{receipt_data['area_code']}</td>
                        </tr>
                        <tr style="border-top: 2px solid #e9ecef;">
                            <td style="padding: 12px 0 8px 0; font-weight: bold; color: #666;">Amount Charged:</td>
                            <td style="padding: 12px 0 8px 0; color: #333; font-weight: bold;">N{receipt_data['amount_spent']:.2f} (${receipt_data['amount_usd']:.2f} USD)</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #666;">Completed At:</td>
                            <td style="padding: 8px 0; color: #333;">{datetime.fromisoformat(receipt_data['success_timestamp'].replace('Z', '+00:00')).strftime('%B %d, %Y at %I:%M %p UTC')}</td>
                        </tr>
                    </table>
                </div>
                
                <div style="background: #e8f5e8; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <p style="margin: 0; color: #155724; font-weight: bold;">✅ Transaction Completed Successfully</p>
                    <p style="margin: 5px 0 0 0; color: #155724; font-size: 14px;">Your verification was processed and SMS messages were delivered to the number above.</p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://namaskah.app/app" style="background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">View Dashboard</a>
                </div>
                
                <div style="border-top: 1px solid #e9ecef; padding-top: 20px; margin-top: 30px; text-align: center; color: #666; font-size: 14px;">
                    <p>Need help? Contact us at <a href="mailto:support@namaskah.app" style="color: #667eea;">support@namaskah.app</a></p>
                    <p style="margin: 10px 0 0 0;">
                        <a href="https://namaskah.app/app?settings=notifications" style="color: #667eea; text-decoration: none;">Manage notification preferences</a>
                    </p>
                </div>
            </div>
        </div>
        """
        
        try:
            email_service.send_email(user_email, subject, html_body)
        except Exception as e:
            print(f"Failed to send receipt email: {e}")
    
    def get_user_receipts(self, user_id: str, limit: int = 50):
        """Get user's verification receipts"""
        
        receipts = self.db.query(VerificationReceipt).filter(
            VerificationReceipt.user_id == user_id
        ).order_by(VerificationReceipt.created_at.desc()).limit(limit).all()
        
        return [
            {
                "id": r.id,
                "receipt_number": f"NSK-{r.verification_id[-8:].upper()}",
                "service_name": r.service_name,
                "phone_number": r.phone_number,
                "amount_spent": r.amount_spent,
                "amount_usd": round(r.amount_spent * 2, 2),
                "isp_carrier": r.isp_carrier,
                "area_code": r.area_code,
                "success_timestamp": r.success_timestamp.isoformat(),
                "verification_id": r.verification_id
            }
            for r in receipts
        ]

class NotificationService:
    """Service for managing notifications"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_notifications(self, user_id: str, unread_only: bool = False, limit: int = 50):
        """Get user's in-app notifications"""
        
        query = self.db.query(InAppNotification).filter(
            InAppNotification.user_id == user_id
        )
        
        if unread_only:
            query = query.filter(InAppNotification.is_read == False)
        
        notifications = query.order_by(
            InAppNotification.created_at.desc()
        ).limit(limit).all()
        
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
    
    def mark_notification_read(self, notification_id: str, user_id: str):
        """Mark notification as read"""
        
        notification = self.db.query(InAppNotification).filter(
            InAppNotification.id == notification_id,
            InAppNotification.user_id == user_id
        ).first()
        
        if notification:
            notification.is_read = True
            self.db.commit()
            return True
        return False
    
    def mark_all_read(self, user_id: str):
        """Mark all notifications as read for user"""
        
        self.db.query(InAppNotification).filter(
            InAppNotification.user_id == user_id,
            InAppNotification.is_read == False
        ).update({"is_read": True})
        self.db.commit()
    
    def get_notification_preferences(self, user_id: str):
        """Get user notification preferences"""
        
        prefs = self.db.query(NotificationPreferences).filter(
            NotificationPreferences.user_id == user_id
        ).first()
        
        if not prefs:
            # Create default preferences
            prefs = NotificationPreferences(
                id=f"pref_{datetime.now(timezone.utc).timestamp()}",
                user_id=user_id
            )
            self.db.add(prefs)
            self.db.commit()
        
        return {
            "in_app_notifications": prefs.in_app_notifications,
            "email_notifications": prefs.email_notifications,
            "receipt_notifications": prefs.receipt_notifications
        }
    
    def update_notification_preferences(
        self,
        user_id: str,
        in_app_notifications: bool = None,
        email_notifications: bool = None,
        receipt_notifications: bool = None
    ):
        """Update user notification preferences"""
        
        prefs = self.db.query(NotificationPreferences).filter(
            NotificationPreferences.user_id == user_id
        ).first()
        
        if not prefs:
            prefs = NotificationPreferences(
                id=f"pref_{datetime.now(timezone.utc).timestamp()}",
                user_id=user_id
            )
            self.db.add(prefs)
        
        if in_app_notifications is not None:
            prefs.in_app_notifications = in_app_notifications
        if email_notifications is not None:
            prefs.email_notifications = email_notifications
        if receipt_notifications is not None:
            prefs.receipt_notifications = receipt_notifications
        
        prefs.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        
        return self.get_notification_preferences(user_id)

def process_successful_verification(
    db: Session,
    user_id: str,
    user_email: str,
    verification_id: str,
    service_name: str,
    phone_number: str,
    amount_spent: float,
    isp_carrier: Optional[str] = None
) -> Dict[str, Any]:
    """Process successful verification and send receipt"""
    
    receipt_service = ReceiptService(db)
    
    # Generate receipt
    receipt_data = receipt_service.generate_receipt(
        user_id=user_id,
        verification_id=verification_id,
        service_name=service_name,
        phone_number=phone_number,
        amount_spent=amount_spent,
        isp_carrier=isp_carrier
    )
    
    # Send notifications
    receipt_service.send_receipt_notifications(
        user_id=user_id,
        user_email=user_email,
        receipt_data=receipt_data
    )
    
    return receipt_data