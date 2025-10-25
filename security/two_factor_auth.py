# Two-Factor Authentication for Admin
import pyotp
import qrcode
from io import BytesIO
import base64
from fastapi import HTTPException
from pydantic import BaseModel

class TwoFactorAuth:
    def __init__(self):
        self.issuer = "Namaskah SMS"
    
    def generate_secret(self, user_email: str) -> dict:
        """Generate TOTP secret and QR code"""
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        
        # Generate QR code
        provisioning_uri = totp.provisioning_uri(
            name=user_email,
            issuer_name=self.issuer
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        qr_code = base64.b64encode(buffer.getvalue()).decode()
        
        return {
            "secret": secret,
            "qr_code": f"data:image/png;base64,{qr_code}",
            "manual_entry": secret
        }
    
    def verify_token(self, secret: str, token: str) -> bool:
        """Verify TOTP token"""
        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(token, valid_window=1)
        except:
            return False

class TwoFactorRequest(BaseModel):
    token: str

# Global 2FA instance
two_factor = TwoFactorAuth()