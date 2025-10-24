# Email Service Module
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


class EmailService:
    """Email service for sending notifications"""

    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@namaskah.app")
        self.base_url = os.getenv("BASE_URL", "https://namaskah.app")

    def send_email(self, to_email, subject, body):
        """Send HTML email"""
        if not self.smtp_user or not self.smtp_password:
            print(f"⚠️ Email not configured - would send: {subject} to {to_email}")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_email
            msg["To"] = to_email

            html_part = MIMEText(body, "html")
            msg.attach(html_part)

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            print(f"✅ Email sent: {subject} to {to_email}")
            return True

        except Exception as e:
            print(f"❌ Email error: {e}")
            return False

    def send_verification_email(self, email, token):
        """Send email verification"""
        subject = "Verify Your Email - Namaskah SMS"
        body = f"""
        <h2>Welcome to Namaskah SMS!</h2>
        <p>Please verify your email address by clicking the link below:</p>
        <p><a href="{self.base_url}/auth/verify?token={token}" style="background: #10b981; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;">Verify Email</a></p>
        <p>If the button doesn't work, copy this link: {self.base_url}/auth/verify?token={token}</p>
        <p>This link expires in 24 hours.</p>
        """
        return self.send_email(email, subject, body)

    def send_welcome_email(self, email):
        """Send welcome email after verification"""
        subject = "Welcome to Namaskah SMS! 🎉"
        body = f"""
        <h2>Welcome to Namaskah SMS!</h2>
        <p>Your email has been verified successfully. You're all set to start using our SMS verification service.</p>
        <p><strong>What's next?</strong></p>
        <ul>
            <li>🎁 You have 1 FREE verification to get started</li>
            <li>💰 Fund your wallet for more verifications</li>
            <li>📱 Choose from 1,807+ supported services</li>
        </ul>
        <p><a href="{self.base_url}/app" style="background: #10b981; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;">Start Verifying</a></p>
        """
        return self.send_email(email, subject, body)

    def send_password_reset_email(self, email, token):
        """Send password reset email"""
        subject = "Reset Your Password - Namaskah SMS"
        body = f"""
        <h2>Password Reset Request</h2>
        <p>You requested to reset your password. Click the link below to set a new password:</p>
        <p><a href="{self.base_url}/reset-password?token={token}" style="background: #ef4444; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;">Reset Password</a></p>
        <p>If you didn't request this, please ignore this email.</p>
        <p>This link expires in 1 hour.</p>
        """
        return self.send_email(email, subject, body)


# Global email service instance
email_service = EmailService()
