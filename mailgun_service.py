"""
Mailgun Email Service for Namaskah SMS
Professional email templates with error handling
"""
import requests
import os
from datetime import datetime, timezone
from typing import Dict, Optional

class MailgunService:
    def __init__(self):
        self.domain = os.getenv("MAILGUN_DOMAIN")
        self.api_key = os.getenv("MAILGUN_API_KEY")
        self.base_url = f"https://api.mailgun.net/v3/{self.domain}"
        self.from_email = f"Namaskah SMS <noreply@{self.domain}>"
    
    def _send_email(self, to: str, subject: str, html: str, text: str = None) -> Dict:
        """Base email sending method with error handling"""
        try:
            response = requests.post(
                f"{self.base_url}/messages",
                auth=("api", self.api_key),
                data={
                    "from": self.from_email,
                    "to": to,
                    "subject": subject,
                    "html": html,
                    "text": text or self._html_to_text(html)
                },
                timeout=10
            )
            
            if response.status_code == 200:
                return {"success": True, "message_id": response.json().get("id")}
            else:
                return {"success": False, "error": response.text}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text fallback"""
        import re
        text = re.sub('<[^<]+?>', '', html)
        return text.strip()
    
    def send_verification_email(self, email: str, token: str) -> Dict:
        """Send email verification with professional template"""
        base_url = os.getenv("BASE_URL", "http://localhost:8000")
        verify_url = f"{base_url}/auth/verify?token={token}"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Verify Your Email - Namaskah SMS</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #2563eb;">Namaskah SMS</h1>
                    <p style="color: #666;">Instant SMS Verification Service</p>
                </div>
                
                <h2>Welcome! Please verify your email</h2>
                <p>Thanks for signing up for Namaskah SMS. To complete your registration, please verify your email address.</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verify_url}" 
                       style="background: #2563eb; color: white; padding: 12px 30px; 
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Verify Email Address
                    </a>
                </div>
                
                <p style="color: #666; font-size: 14px;">
                    If the button doesn't work, copy and paste this link:<br>
                    <a href="{verify_url}">{verify_url}</a>
                </p>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                <p style="color: #999; font-size: 12px;">
                    This email was sent to {email}. If you didn't sign up for Namaskah SMS, you can ignore this email.
                </p>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(
            to=email,
            subject="Verify Your Email - Namaskah SMS",
            html=html
        )
    
    def send_test_email(self, email: str) -> Dict:
        """Send test email to verify Mailgun setup"""
        html = """
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #16a34a;">✅ Mailgun Test Successful!</h1>
                <p>If you're reading this, your Mailgun integration is working perfectly.</p>
                
                <div style="background: #f0f9ff; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0;">Setup Complete</h3>
                    <p>✅ Mailgun API connected<br>
                       ✅ Email templates working<br>
                       ✅ Ready for production</p>
                </div>
                
                <p>You can now proceed with implementing the full email service.</p>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(
            to=email,
            subject="Mailgun Test - Namaskah SMS Setup Complete",
            html=html
        )
    
    def send_password_reset_email(self, email: str, token: str) -> Dict:
        """Send password reset email"""
        base_url = os.getenv("BASE_URL", "http://localhost:8000")
        reset_url = f"{base_url}/auth/reset-password?token={token}"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #2563eb;">Password Reset Request</h1>
                <p>You requested a password reset for your Namaskah SMS account.</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}" 
                       style="background: #dc2626; color: white; padding: 12px 30px; 
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Reset Password
                    </a>
                </div>
                
                <p style="color: #666;">This link expires in 1 hour for security.</p>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(
            to=email,
            subject="Reset Your Password - Namaskah SMS",
            html=html
        )
    
    def send_welcome_email(self, email: str) -> Dict:
        """Send welcome email after verification"""
        base_url = os.getenv("BASE_URL", "http://localhost:8000")
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #2563eb;">Welcome to Namaskah SMS! 🎉</h1>
                <p>Your email has been verified successfully. You're ready to start using our SMS verification service.</p>
                
                <h3>What's Next?</h3>
                <ul>
                    <li>✅ <strong>1 Free Verification</strong> - Already added to your account</li>
                    <li>📱 <strong>1,800+ Services</strong> - WhatsApp, Telegram, Google, Discord & more</li>
                    <li>💰 <strong>Affordable Pricing</strong> - Starting at N1 ($2) per verification</li>
                </ul>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{base_url}/app" 
                       style="background: #16a34a; color: white; padding: 12px 30px; 
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Start Your First Verification
                    </a>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(
            to=email,
            subject="Welcome to Namaskah SMS! Your account is ready 🚀",
            html=html
        )

# Initialize service
mailgun_service = MailgunService()