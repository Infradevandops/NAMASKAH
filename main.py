import os
import random
import asyncio
from typing import Dict, Optional, List
import logging
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

# Import our custom clients
from textverified_client import TextVerifiedClient
from groq_client import GroqAIClient

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- API Configuration ---
# Twilio Configuration
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

# TextVerified Configuration
TEXTVERIFIED_API_KEY = os.getenv("TEXTVERIFIED_API_KEY")
TEXTVERIFIED_EMAIL = os.getenv("TEXTVERIFIED_EMAIL")

# Groq Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama3-8b-8192")

# Check if credentials are set
if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
    logger.warning("Twilio credentials not fully configured. SMS service may not be available.")

if not all([TEXTVERIFIED_API_KEY, TEXTVERIFIED_EMAIL]):
    logger.warning("TextVerified credentials not configured. Verification service may not be available.")

if not GROQ_API_KEY:
    logger.warning("Groq API key not configured. AI assistance may not be available.")

# Initialize clients
twilio_client = None
textverified_client = None
groq_client = None

if all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
    twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    logger.info("Twilio client initialized successfully")

if all([TEXTVERIFIED_API_KEY, TEXTVERIFIED_EMAIL]):
    textverified_client = TextVerifiedClient(TEXTVERIFIED_API_KEY, TEXTVERIFIED_EMAIL)
    logger.info("TextVerified client initialized successfully")

if GROQ_API_KEY:
    groq_client = GroqAIClient(GROQ_API_KEY, GROQ_MODEL)
    logger.info("Groq AI client initialized successfully")

# --- FastAPI App Initialization ---
app = FastAPI(
    title="SMSPROJ - Communication Platform",
    description="Comprehensive SMS and voice communication platform with AI assistance",
    version="1.0.0"
)

# Mount static files (for CSS, JS, images, etc.)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")

# --- In-memory storage for verification data ---
# In a production app, use a more persistent store like Redis or a database.
verification_data_store: Dict[str, Dict] = {}
textverified_store: Dict[str, Dict] = {}

# --- Pydantic Models ---
class VerificationRequest(BaseModel):
    service_name: str
    capability: str = "sms"

class VerificationResponse(BaseModel):
    verification_id: str
    status: str
    message: str

class SMSRequest(BaseModel):
    to_number: str
    message: str
    from_number: Optional[str] = None

class AIRequest(BaseModel):
    conversation_history: List[Dict[str, str]]
    context: Optional[str] = None

# --- Utility Functions ---
def generate_verification_code(length: int = 6) -> str:
    """Generates a random numeric verification code."""
    return "".join([str(random.randint(0, 9)) for _ in range(length)])

# --- Health Check Endpoint ---
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "app_name": "SMSPROJ",
        "version": "1.0.0",
        "services": {
            "twilio": twilio_client is not None,
            "textverified": textverified_client is not None,
            "groq": groq_client is not None
        }
    }

# --- Application Info ---
@app.get("/api/info")
async def get_app_info():
    """Get application information."""
    return {
        "app_name": "SMSPROJ",
        "version": "1.0.0",
        "description": "Comprehensive communication platform",
        "features": [
            "SMS verification with TextVerified",
            "International SMS support",
            "AI-powered conversation assistance",
            "Health monitoring",
            "RESTful API"
        ],
        "endpoints": {
            "health": "/health",
            "verification": "/api/verification/*",
            "sms": "/api/sms/*",
            "ai": "/api/ai/*",
            "account": "/api/account/*",
            "services": "/api/services/*"
        }
    }

# --- Account Information Endpoints ---
@app.get("/api/account/textverified/balance")
async def get_textverified_balance():
    """Get TextVerified account balance."""
    if not textverified_client:
        raise HTTPException(status_code=503, detail="TextVerified service is not configured")
    
    try:
        balance = await textverified_client.check_balance()
        return {
            "service": "TextVerified",
            "balance": balance,
            "currency": "USD"
        }
    except Exception as e:
        logger.error(f"Failed to get TextVerified balance: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get balance: {str(e)}")

@app.get("/api/services/textverified")
async def get_textverified_services():
    """Get available TextVerified services."""
    if not textverified_client:
        raise HTTPException(status_code=503, detail="TextVerified service is not configured")
    
    try:
        services = await textverified_client.get_service_list()
        return {
            "service": "TextVerified",
            "count": len(services),
            "services": services
        }
    except Exception as e:
        logger.error(f"Failed to get TextVerified services: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get services: {str(e)}")

# --- SMS API Endpoints ---
@app.post("/api/sms/send")
async def send_sms(request: SMSRequest):
    """Send SMS using Twilio."""
    if not twilio_client:
        raise HTTPException(status_code=503, detail="Twilio SMS service is not configured")
    
    try:
        from_number = request.from_number or TWILIO_PHONE_NUMBER
        message = twilio_client.messages.create(
            body=request.message,
            from_=from_number,
            to=request.to_number
        )
        
        logger.info(f"SMS sent to {request.to_number}. Message SID: {message.sid}")
        return {
            "status": "sent",
            "message_sid": message.sid,
            "to": request.to_number,
            "from": from_number,
            "message": "SMS sent successfully"
        }
    except TwilioRestException as e:
        logger.error(f"Failed to send SMS: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send SMS: {str(e)}")

# --- New TextVerified API Endpoints ---
@app.post("/api/verification/create")
async def create_verification(request: VerificationRequest):
    """
    Create a new verification using TextVerified API.
    Returns a verification ID that can be used to check status and retrieve messages.
    """
    if not textverified_client:
        raise HTTPException(status_code=503, detail="TextVerified service is not configured")
    
    try:
        verification_id = await textverified_client.create_verification(
            service_name=request.service_name,
            capability=request.capability
        )
        
        # Store verification info
        textverified_store[verification_id] = {
            "service_name": request.service_name,
            "capability": request.capability,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        
        logger.info(f"Created verification {verification_id} for service {request.service_name}")
        return VerificationResponse(
            verification_id=verification_id,
            status="created",
            message=f"TextVerified verification created for {request.service_name}"
        )
    except Exception as e:
        logger.error(f"Failed to create verification: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create verification: {str(e)}")

@app.get("/api/verification/{verification_id}/status")
async def get_verification_status(verification_id: str):
    """Get the status of a verification."""
    if not textverified_client:
        raise HTTPException(status_code=503, detail="TextVerified service is not configured")
    
    try:
        details = await textverified_client.get_verification_details(verification_id)
        is_completed = textverified_client.check_verification_completed(details)
        status = "completed" if is_completed else "pending"
        
        # Update our local store
        if verification_id in textverified_store:
            textverified_store[verification_id]["status"] = status
        
        return {
            "verification_id": verification_id,
            "status": status,
            "details": details
        }
    except Exception as e:
        logger.error(f"Failed to get verification status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get verification status: {str(e)}")

@app.get("/api/verification/{verification_id}/number")
async def get_verification_number(verification_id: str):
    """Get the phone number for a verification."""
    if not textverified_client:
        raise HTTPException(status_code=503, detail="TextVerified service is not configured")
    
    try:
        number = await textverified_client.get_verification_number(verification_id)
        logger.info(f"Retrieved number for verification {verification_id}")
        return {
            "verification_id": verification_id,
            "number": number,
            "message": f"Use this number: {number}"
        }
    except Exception as e:
        logger.error(f"Failed to get verification number: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get verification number: {str(e)}")

@app.get("/api/verification/{verification_id}/messages")
async def get_verification_messages(verification_id: str):
    """Get SMS messages received for a verification."""
    if not textverified_client:
        raise HTTPException(status_code=503, detail="TextVerified service is not configured")
    
    try:
        messages = await textverified_client.get_sms_messages(verification_id)
        logger.info(f"Retrieved {len(messages)} messages for verification {verification_id}")
        return {
            "verification_id": verification_id,
            "messages": messages,
            "count": len(messages)
        }
    except Exception as e:
        logger.error(f"Failed to get verification messages: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get verification messages: {str(e)}")

@app.delete("/api/verification/{verification_id}")
async def cancel_verification(verification_id: str):
    """Cancel a verification."""
    if not textverified_client:
        raise HTTPException(status_code=503, detail="TextVerified service is not configured")
    
    try:
        success = await textverified_client.cancel_verification(verification_id)
        
        # Update our local store
        if verification_id in textverified_store:
            textverified_store[verification_id]["status"] = "cancelled"
        
        return {
            "verification_id": verification_id,
            "cancelled": success,
            "message": "Verification cancelled successfully" if success else "Failed to cancel verification"
        }
    except Exception as e:
        logger.error(f"Failed to cancel verification: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel verification: {str(e)}")

# --- AI Assistant Endpoints ---
@app.post("/api/ai/suggest-response")
async def suggest_response(request: AIRequest):
    """Get AI-powered response suggestions for SMS conversations."""
    if not groq_client:
        raise HTTPException(status_code=503, detail="Groq AI service is not configured")
    
    try:
        suggestion = await groq_client.suggest_sms_response(
            conversation_history=request.conversation_history,
            context=request.context
        )
        
        return {
            "suggestion": suggestion,
            "model": GROQ_MODEL,
            "service": "Groq"
        }
    except Exception as e:
        logger.error(f"Failed to generate AI response: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate AI response: {str(e)}")

@app.post("/api/ai/analyze-intent")
async def analyze_intent(message: str):
    """Analyze the intent and sentiment of a message."""
    if not groq_client:
        raise HTTPException(status_code=503, detail="Groq AI service is not configured")
    
    try:
        analysis = await groq_client.analyze_message_intent(message)
        return analysis
    except Exception as e:
        logger.error(f"Failed to analyze message intent: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze intent: {str(e)}")

@app.get("/api/ai/help/{service_name}")
async def get_service_help(service_name: str, step: str = "general"):
    """Get contextual help for setting up services."""
    if not groq_client:
        raise HTTPException(status_code=503, detail="Groq AI service is not configured")
    
    try:
        help_text = await groq_client.help_with_service_setup(service_name, step)
        return {
            "service": service_name,
            "step": step,
            "help": help_text
        }
    except Exception as e:
        logger.error(f"Failed to generate help text: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate help: {str(e)}")

# --- Original Resume Verification Endpoints (Legacy) ---
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serves the initial form page."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate", response_class=HTMLResponse)
async def start_verification(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    experience: str = Form(...),
):
    """
    Handles the initial form submission.
    Generates a verification code, stores user data, sends an SMS,
    and returns the verification page.
    """
    if not twilio_client:
        return templates.TemplateResponse(
            "verify.html",
            {
                "request": request,
                "phone": phone,
                "error": "SMS service is not configured. Please contact administrator.",
            },
        )

    verification_code = generate_verification_code()

    # Store the resume data and verification code temporarily, keyed by phone number
    verification_data_store[phone] = {
        "code": verification_code,
        "resume_data": {
            "name": name,
            "email": email,
            "phone": phone,
            "experience": experience,
        },
    }

    try:
        message = twilio_client.messages.create(
            body=f"Your SMSPROJ verification code is: {verification_code}",
            from_=TWILIO_PHONE_NUMBER,
            to=phone,
        )
        logger.info(f"SMS sent to {phone}. Message SID: {message.sid}")
    except TwilioRestException as e:
        logger.error(f"Error sending SMS: {e}")
        return templates.TemplateResponse(
            "verify.html",
            {
                "request": request,
                "phone": phone,
                "error": "Could not send verification code. Please check the phone number and try again.",
            },
        )

    return templates.TemplateResponse("verify.html", {"request": request, "phone": phone})

@app.post("/verify", response_class=HTMLResponse)
async def verify_code(request: Request, phone: str = Form(...), code: str = Form(...)):
    """Verifies the SMS code. If correct, displays the result."""
    stored_data = verification_data_store.get(phone)

    if not stored_data or stored_data["code"] != code:
        return templates.TemplateResponse(
            "verify.html",
            {"request": request, "phone": phone, "error": "Invalid verification code. Please try again."},
        )

    # Verification successful, retrieve resume data and clear the stored entry
    resume_data = stored_data["resume_data"]
    del verification_data_store[phone]

    return templates.TemplateResponse(
        "result.html", {"request": request, "resume": resume_data}
    )

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting SMSPROJ application...")
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)