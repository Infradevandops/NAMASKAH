"""
Email Service Module for Namaskah SMS
Supports multiple email providers with fallback options
"""
import os
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@namaskah.app")
        
        # SendGrid API
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        
        # Mailgun API
        self.mailgun_api_key = os.getenv("MAILGUN_API_KEY")
        self.mailgun_domain = os.getenv("MAILGUN_DOMAIN")
        
        # AWS SES
        self.aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.aws_region = os.getenv("AWS_REGION", "us-east-1")
        
        self.base_url = os.getenv("BASE_URL", "http://localhost:8000")
    
    def send_email(self, to_email: str, subject: str, html_body: str, text_body: str = None) -> bool:
        """Send email using the first available provider"""
        
        # Try SendGrid first (best for production)
        if self.sendgrid_api_key:
            if self._send_via_sendgrid(to_email, subject, html_body, text_body):
                return True
        
        # Try Mailgun
        if self.mailgun_api_key and self.mailgun_domain:
            if self._send_via_mailgun(to_email, subject, html_body, text_body):
                return True
        
        # Try AWS SES
        if self.aws_access_key and self.aws_secret_key:
            if self._send_via_ses(to_email, subject, html_body, text_body):
                return True
        
        # Fallback to SMTP (Gmail, etc.)
        if self.smtp_host and self.smtp_user and self.smtp_password:
            return self._send_via_smtp(to_email, subject, html_body, text_body)
        
        logger.warning(f"No email provider configured, skipping email to {to_email}")
        return False
    
    def _send_via_smtp(self, to_email: str, subject: str, html_body: str, text_body: str = None) -> bool:
        """Send email via SMTP (Gmail, etc.)"""
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            if text_body:
                msg.attach(MIMEText(text_body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent via SMTP: {subject} to {to_email}")
            return True
        except Exception as e:
            logger.error(f"SMTP email failed: {e}")
            return False
    
    def _send_via_sendgrid(self, to_email: str, subject: str, html_body: str, text_body: str = None) -> bool:
        """Send email via SendGrid API"""
        try:
            url = "https://api.sendgrid.com/v3/mail/send"
            headers = {
                "Authorization": f"Bearer {self.sendgrid_api_key}",
                "Content-Type": "application/json"
            }
            
            content = [{"type": "text/html", "value": html_body}]
            if text_body:
                content.insert(0, {"type": "text/plain", "value": text_body})
            
            data = {
                "personalizations": [{"to": [{"email": to_email}]}],
                "from": {"email": self.from_email, "name": "Namaskah SMS"},
                "subject": subject,
                "content": content
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=10)
            response.raise_for_status()
            
            logger.info(f"Email sent via SendGrid: {subject} to {to_email}")
            return True
        except Exception as e:
            logger.error(f"SendGrid email failed: {e}")
            return False
    
    def _send_via_mailgun(self, to_email: str, subject: str, html_body: str, text_body: str = None) -> bool:
        """Send email via Mailgun API"""
        try:
            url = f"https://api.mailgun.net/v3/{self.mailgun_domain}/messages"
            auth = ("api", self.mailgun_api_key)
            
            data = {
                "from": f"Namaskah SMS <{self.from_email}>",
                "to": to_email,
                "subject": subject,
                "html": html_body
            }
            
            if text_body:
                data["text"] = text_body
            
            response = requests.post(url, auth=auth, data=data, timeout=10)
            response.raise_for_status()
            
            logger.info(f"Email sent via Mailgun: {subject} to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Mailgun email failed: {e}")
            return False
    
    def _send_via_ses(self, to_email: str, subject: str, html_body: str, text_body: str = None) -> bool:
        """Send email via AWS SES"""
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            client = boto3.client(
                'ses',
                region_name=self.aws_region,
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key
            )
            
            body = {"Html": {"Data": html_body, "Charset": "UTF-8"}}
            if text_body:
                body["Text"] = {"Data": text_body, "Charset": "UTF-8"}
            
            response = client.send_email(
                Source=self.from_email,
                Destination={"ToAddresses": [to_email]},
                Message={
                    "Subject": {"Data": subject, "Charset": "UTF-8"},
                    "Body": body
                }
            )
            
            logger.info(f"Email sent via AWS SES: {subject} to {to_email}")
            return True
        except ImportError:
            logger.error("boto3 not installed for AWS SES")
            return False
        except Exception as e:
            logger.error(f"AWS SES email failed: {e}")
            return False
    
    def send_verification_email(self, email: str, token: str, user_name: str = None) -> bool:
        """Send email verification email"""
        verification_url = f"{self.base_url}/auth/verify?token={token}"
        
        subject = "Verify Your Email - Namaskah SMS"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Verify Your Email</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 28px;">Welcome to Namaskah SMS!</h1>
            </div>
            
            <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #ddd;">
                <h2 style="color: #333; margin-top: 0;">Verify Your Email Address</h2>
                
                <p>Hi{f" {user_name}" if user_name else ""},</p>
                
                <p>Thank you for signing up for Namaskah SMS! To complete your registration and start using our SMS verification services, please verify your email address.</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verification_url}" 
                       style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                              color: white; 
                              padding: 15px 30px; 
                              text-decoration: none; 
                              border-radius: 5px; 
                              font-weight: bold; 
                              display: inline-block;">
                        Verify Email Address
                    </a>
                </div>
                
                <p>Or copy and paste this link into your browser:</p>
                <p style="background: #fff; padding: 10px; border: 1px solid #ddd; border-radius: 5px; word-break: break-all;">
                    {verification_url}
                </p>
                
                <div style="background: #e8f4fd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #0066cc;">What's Next?</h3>
                    <ul style="margin: 0; padding-left: 20px;">
                        <li>Get 1 free SMS verification</li>
                        <li>Access 1,807+ supported services</li>
                        <li>Fund your wallet and start verifying</li>
                        <li>Use our API for automation</li>
                    </ul>
                </div>
                
                <p><strong>Important:</strong> This verification link expires in 24 hours for security reasons.</p>
                
                <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                
                <p style="font-size: 14px; color: #666;">
                    If you didn't create an account with Namaskah SMS, you can safely ignore this email.
                </p>
                
                <p style="font-size: 14px; color: #666;">
                    Need help? Contact us at <a href="mailto:support@namaskah.app">support@namaskah.app</a>
                </p>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        Welcome to Namaskah SMS!
        
        Hi{f" {user_name}" if user_name else ""},
        
        Thank you for signing up! Please verify your email address by clicking the link below:
        
        {verification_url}
        
        This link expires in 24 hours.
        
        What's next?
        - Get 1 free SMS verification
        - Access 1,807+ supported services  
        - Fund your wallet and start verifying
        - Use our API for automation
        
        If you didn't create this account, you can ignore this email.
        
        Need help? Contact support@namaskah.app
        
        Best regards,
        Namaskah SMS Team
        """
        
        return self.send_email(email, subject, html_body, text_body)
    
    def send_password_reset_email(self, email: str, token: str, user_name: str = None) -> bool:
        """Send password reset email"""
        reset_url = f"{self.base_url}/auth/reset-password?token={token}"
        
        subject = "Reset Your Password - Namaskah SMS"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Reset Your Password</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 28px;">Password Reset Request</h1>
            </div>
            
            <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #ddd;">
                <h2 style="color: #333; margin-top: 0;">Reset Your Password</h2>
                
                <p>Hi{f" {user_name}" if user_name else ""},</p>
                
                <p>We received a request to reset your password for your Namaskah SMS account. If you made this request, click the button below to reset your password:</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}" 
                       style="background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%); 
                              color: white; 
                              padding: 15px 30px; 
                              text-decoration: none; 
                              border-radius: 5px; 
                              font-weight: bold; 
                              display: inline-block;">
                        Reset Password
                    </a>
                </div>
                
                <p>Or copy and paste this link into your browser:</p>
                <p style="background: #fff; padding: 10px; border: 1px solid #ddd; border-radius: 5px; word-break: break-all;">
                    {reset_url}
                </p>
                
                <div style="background: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #ffc107;">
                    <p style="margin: 0;"><strong>Security Notice:</strong> This password reset link expires in 1 hour for your security.</p>
                </div>
                
                <p><strong>If you didn't request this password reset:</strong></p>
                <ul>
                    <li>You can safely ignore this email</li>
                    <li>Your password will remain unchanged</li>
                    <li>Consider changing your password if you suspect unauthorized access</li>
                </ul>
                
                <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                
                <p style="font-size: 14px; color: #666;">
                    Need help? Contact us at <a href="mailto:support@namaskah.app">support@namaskah.app</a>
                </p>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        Password Reset Request - Namaskah SMS
        
        Hi{f" {user_name}" if user_name else ""},
        
        We received a request to reset your password. Click the link below to reset it:
        
        {reset_url}
        
        This link expires in 1 hour for security.
        
        If you didn't request this reset, you can safely ignore this email.
        
        Need help? Contact support@namaskah.app
        
        Best regards,
        Namaskah SMS Team
        """
        
        return self.send_email(email, subject, html_body, text_body)
    
    def send_welcome_email(self, email: str, user_name: str = None) -> bool:
        """Send welcome email after successful verification"""
        subject = "Welcome to Namaskah SMS - Your Account is Ready!"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Welcome to Namaskah SMS</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #10ac84 0%, #1dd1a1 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 28px;">🎉 Welcome to Namaskah SMS!</h1>
            </div>
            
            <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #ddd;">
                <h2 style="color: #333; margin-top: 0;">Your Account is Ready!</h2>
                
                <p>Hi{f" {user_name}" if user_name else ""},</p>
                
                <p>Congratulations! Your email has been verified and your Namaskah SMS account is now active. You're ready to start using our SMS verification services.</p>
                
                <div style="background: #e8f5e8; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #10ac84;">🎁 Your Free Credits</h3>
                    <p style="margin: 0;">You've received <strong>1 free SMS verification</strong> to get started!</p>
                </div>
                
                <h3 style="color: #333;">Quick Start Guide:</h3>
                <ol style="padding-left: 20px;">
                    <li><strong>Create Your First Verification</strong><br>
                        Choose from 1,807+ supported services like WhatsApp, Telegram, Google, Discord, and more.</li>
                    <li><strong>Fund Your Wallet</strong><br>
                        Add credits via Paystack (NGN) for continued usage. Minimum funding: $5 USD.</li>
                    <li><strong>Use Our API</strong><br>
                        Integrate SMS verification into your applications with our RESTful API.</li>
                    <li><strong>Get Support</strong><br>
                        Need help? Our support team responds within 24 hours.</li>
                </ol>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{self.base_url}/app" 
                       style="background: linear-gradient(135deg, #10ac84 0%, #1dd1a1 100%); 
                              color: white; 
                              padding: 15px 30px; 
                              text-decoration: none; 
                              border-radius: 5px; 
                              font-weight: bold; 
                              display: inline-block;">
                        Start Using Namaskah SMS
                    </a>
                </div>
                
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h4 style="margin-top: 0; color: #333;">Pricing Overview:</h4>
                    <ul style="margin: 0; padding-left: 20px;">
                        <li><strong>Tier 1 Services:</strong> N0.75 ($1.50) - WhatsApp, Telegram, Discord</li>
                        <li><strong>Tier 2 Services:</strong> N1.00 ($2.00) - Instagram, Facebook, Twitter</li>
                        <li><strong>Voice Verification:</strong> SMS price + N0.30 ($0.60)</li>
                        <li><strong>Volume Discounts:</strong> Up to 15% off for high usage</li>
                    </ul>
                </div>
                
                <h3 style="color: #333;">Useful Links:</h3>
                <ul style="padding-left: 20px;">
                    <li><a href="{self.base_url}/api-docs">API Documentation</a></li>
                    <li><a href="{self.base_url}/faq">Frequently Asked Questions</a></li>
                    <li><a href="{self.base_url}/contact">Contact Support</a></li>
                    <li><a href="{self.base_url}/status">Service Status</a></li>
                </ul>
                
                <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                
                <p>Thank you for choosing Namaskah SMS for your verification needs!</p>
                
                <p style="font-size: 14px; color: #666;">
                    Questions? Reply to this email or contact <a href="mailto:support@namaskah.app">support@namaskah.app</a>
                </p>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        Welcome to Namaskah SMS!
        
        Hi{f" {user_name}" if user_name else ""},
        
        Congratulations! Your account is now active and ready to use.
        
        🎁 You've received 1 free SMS verification to get started!
        
        Quick Start:
        1. Create your first verification from 1,807+ services
        2. Fund your wallet via Paystack (minimum $5 USD)  
        3. Use our API for automation
        4. Get support within 24 hours
        
        Pricing:
        - Tier 1: N0.75 ($1.50) - WhatsApp, Telegram, Discord
        - Tier 2: N1.00 ($2.00) - Instagram, Facebook, Twitter
        - Voice: SMS price + N0.30 ($0.60)
        - Volume discounts up to 15% off
        
        Get started: {self.base_url}/app
        API Docs: {self.base_url}/api-docs
        Support: support@namaskah.app
        
        Thank you for choosing Namaskah SMS!
        """
        
        return self.send_email(email, subject, html_body, text_body)

# Global email service instance
email_service = EmailService()