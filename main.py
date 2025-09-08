import os
import random
import asyncio
from typing import Dict, Optional, List
import logging
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from analytics import analytics
from health_monitor import health_monitor
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# Import database components
from database import check_database_connection, create_tables

from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

# Import our custom clients
from textverified_client import TextVerifiedClient
from groq_client import GroqAIClient
from mock_twilio_client import create_twilio_client, MockTwilioClient

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

# Use mock Twilio client if real credentials aren't available
USE_MOCK_TWILIO = os.getenv("USE_MOCK_TWILIO", "true").lower() == "true"

if USE_MOCK_TWILIO or not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
    twilio_client = create_twilio_client(use_mock=True)
    TWILIO_PHONE_NUMBER = TWILIO_PHONE_NUMBER or "+1555000001"  # Default mock number
    logger.info("Mock Twilio client initialized successfully")
else:
    twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    logger.info("Real Twilio client initialized successfully")

if all([TEXTVERIFIED_API_KEY, TEXTVERIFIED_EMAIL]):
    textverified_client = TextVerifiedClient(TEXTVERIFIED_API_KEY, TEXTVERIFIED_EMAIL)
    logger.info("TextVerified client initialized successfully")

if GROQ_API_KEY:
    groq_client = GroqAIClient(GROQ_API_KEY, GROQ_MODEL)
    logger.info("Groq AI client initialized successfully")

# --- FastAPI App Initialization ---
app = FastAPI(
    title="CumApp - Communication Platform",
    description="Comprehensive SMS and voice communication platform with AI assistance",
    version="1.1.0"
)

# Add JWT Authentication Middleware
try:
    from middleware.auth_middleware import JWTAuthMiddleware, RateLimitMiddleware
    
    # Add rate limiting middleware
    app.add_middleware(RateLimitMiddleware, requests_per_minute=100)
    
    # Add JWT authentication middleware with excluded paths
    excluded_paths = [
        "/health",
        "/docs",
        "/redoc", 
        "/openapi.json",
        "/api/auth/register",
        "/api/auth/login",
        "/api/auth/refresh",
        "/api/info",
        "/static",
        "/",
        "/chat"
    ]
    app.add_middleware(JWTAuthMiddleware, exclude_paths=excluded_paths)
    
    logger.info("JWT Authentication middleware added successfully")
except ImportError as e:
    logger.warning(f"Could not import JWT middleware: {e}")
except Exception as e:
    logger.warning(f"Error adding JWT middleware: {e}")

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database and check connections on startup"""
    logger.info("Initializing database...")
    
    # Check database connection
    if not check_database_connection():
        logger.error("Database connection failed!")
        return
    
    # Create tables if they don't exist
    try:
        create_tables()
        logger.info("Database initialization completed successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

# Include API routes
try:
    from api.auth_api import router as auth_router
    app.include_router(auth_router)
    logger.info("Authentication API routes included successfully")
except ImportError as e:
    logger.warning(f"Could not import authentication API: {e}")
except Exception as e:
    logger.warning(f"Error including authentication API: {e}")

try:
    from api.messaging_api import router as messaging_router
    app.include_router(messaging_router)
    logger.info("Messaging API routes included successfully")
except ImportError as e:
    logger.warning(f"Could not import messaging API: {e}")
except Exception as e:
    logger.warning(f"Error including messaging API: {e}")

try:
    from api.session_api import router as session_router
    app.include_router(session_router)
    logger.info("Session management API routes included successfully")
except ImportError as e:
    logger.warning(f"Could not import session API: {e}")
except Exception as e:
    logger.warning(f"Error including session API: {e}")

try:
    from api.conversation_api import router as conversation_router
    app.include_router(conversation_router)
    logger.info("Conversation API routes included successfully")
except ImportError as e:
    logger.warning(f"Could not import conversation API: {e}")
except Exception as e:
    logger.warning(f"Error including conversation API: {e}")

try:
    from api.websocket_api import router as websocket_router
    app.include_router(websocket_router)
    logger.info("WebSocket API routes included successfully")
except ImportError as e:
    logger.warning(f"Could not import WebSocket API: {e}")
except Exception as e:
    logger.warning(f"Error including WebSocket API: {e}")

try:
    from api.enhanced_chat_api import router as enhanced_chat_router
    app.include_router(enhanced_chat_router)
    logger.info("Enhanced Chat API routes included successfully")
except ImportError as e:
    logger.warning(f"Could not import Enhanced Chat API: {e}")
except Exception as e:
    logger.warning(f"Error including Enhanced Chat API: {e}")

try:
    from api.phone_number_api import router as phone_number_router
    app.include_router(phone_number_router)
    logger.info("Phone Number API routes included successfully")
except ImportError as e:
    logger.warning(f"Could not import Phone Number API: {e}")
except Exception as e:
    logger.warning(f"Error including Phone Number API: {e}")

try:
    from api.verification_api import router as verification_router
    app.include_router(verification_router)
    logger.info("Verification API routes included successfully")
except ImportError as e:
    logger.warning(f"Could not import Verification API: {e}")
except Exception as e:
    logger.warning(f"Error including Verification API: {e}")

# Mount static files (for CSS, JS, images, etc.)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")

# --- In-memory storage for TextVerified data ---
# In a production app, use a more persistent store like Redis or a database.
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

# --- Health Check Endpoint ---
@app.get("/health")
async def health_check():
    """Enhanced health check endpoint for monitoring."""
    health_status = health_monitor.get_health_status()
    health_status.update({
        "app_name": "CumApp",
        "services": {
            "twilio": twilio_client is not None,
            "textverified": textverified_client is not None,
            "groq": groq_client is not None
        }
    })
    return health_status

# --- Application Info ---
@app.get("/api/info")
async def get_app_info():
    """Get application information."""
    return {
        "app_name": "CumApp",
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
        analytics.track_event('sms_sent', {'to': request.to_number, 'message_sid': message.sid})
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
        analytics.track_event('verification_created', {'service': request.service_name, 'verification_id': verification_id})
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

# --- Mock Twilio Management Endpoints ---
@app.get("/api/mock/sms/history")
async def get_mock_sms_history(limit: int = 50):
    """Get SMS history from mock Twilio client."""
    if not isinstance(twilio_client, MockTwilioClient):
        raise HTTPException(status_code=400, detail="This endpoint is only available with mock Twilio client")
    
    history = twilio_client.get_message_history(limit)
    return {
        "messages": history,
        "count": len(history),
        "is_mock": True
    }

@app.get("/api/mock/calls/history")
async def get_mock_call_history(limit: int = 50):
    """Get call history from mock Twilio client."""
    if not isinstance(twilio_client, MockTwilioClient):
        raise HTTPException(status_code=400, detail="This endpoint is only available with mock Twilio client")
    
    history = twilio_client.get_call_history(limit)
    return {
        "calls": history,
        "count": len(history),
        "is_mock": True
    }

@app.post("/api/mock/sms/simulate-incoming")
async def simulate_incoming_sms(from_number: str, to_number: str, body: str):
    """Simulate receiving an incoming SMS."""
    if not isinstance(twilio_client, MockTwilioClient):
        raise HTTPException(status_code=400, detail="This endpoint is only available with mock Twilio client")
    
    event = twilio_client.simulate_incoming_sms(from_number, to_number, body)
    return {
        "status": "simulated",
        "event": event,
        "message": "Incoming SMS simulated successfully"
    }

@app.get("/api/mock/statistics")
async def get_mock_statistics():
    """Get usage statistics from mock Twilio client."""
    if not isinstance(twilio_client, MockTwilioClient):
        raise HTTPException(status_code=400, detail="This endpoint is only available with mock Twilio client")
    
    stats = twilio_client.get_usage_statistics()
    return {
        "statistics": stats,
        "is_mock": True,
        "note": "These are simulated statistics for development purposes"
    }

@app.get("/api/numbers/available/{country_code}")
async def get_available_numbers(country_code: str):
    """Get available phone numbers for purchase."""
    if isinstance(twilio_client, MockTwilioClient):
        numbers = twilio_client.get_available_phone_numbers(country_code.upper())
        return {
            "country_code": country_code.upper(),
            "available_numbers": numbers,
            "is_mock": True
        }
    else:
        # Real Twilio implementation would go here
        raise HTTPException(status_code=501, detail="Real Twilio number lookup not implemented yet")

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
        analytics.track_event('ai_analysis', {'message_length': len(message), 'intent': analysis.get('intent')})
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

# --- Main Application Routes ---
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serves the platform dashboard."""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/chat", response_class=HTMLResponse)
async def chat_interface(request: Request):
    """Serves the chat interface."""
    return templates.TemplateResponse("chat.html", {"request": request})

@app.get("/hub", response_class=HTMLResponse)
async def communication_hub(request: Request):
    """Serves the main communication hub interface."""
    return templates.TemplateResponse("communication_hub.html", {"request": request})

@app.get("/analytics", response_class=HTMLResponse)
async def analytics_dashboard(request: Request):
    """Serves the analytics dashboard."""
    return templates.TemplateResponse("analytics.html", {"request": request})

@app.get("/api/analytics/stats")
async def get_analytics_stats():
    """Get platform statistics."""
    return analytics.get_stats()

@app.get("/api/analytics/events")
async def get_analytics_events():
    """Get recent events."""
    return analytics.get_recent_events()

@app.get("/verification-history", response_class=HTMLResponse)
async def verification_history(request: Request):
    """Serves the verification history interface."""
    return templates.TemplateResponse("verification_history.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting CumApp application...")
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)