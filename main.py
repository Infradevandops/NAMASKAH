import os
import random
from typing import Dict

from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

# Load environment variables from .env file
load_dotenv()

# --- Twilio Configuration ---
# Get credentials from environment variables
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

# Check if Twilio credentials are set to prevent runtime errors
if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
    raise EnvironmentError(
        "Critical: Twilio environment variables (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER) are not set."
    )

# Initialize Twilio client
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# --- FastAPI App Initialization ---
app = FastAPI()

# Mount static files (for CSS, JS, images, etc.)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")

# --- In-memory storage for verification data ---
# In a production app, use a more persistent store like Redis or a database.
verification_data_store: Dict[str, Dict] = {}


def generate_verification_code(length: int = 6) -> str:
    """Generates a random numeric verification code."""
    return "".join([str(random.randint(0, 9)) for _ in range(length)])


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
            body=f"Your Resume Kraft verification code is: {verification_code}",
            from_=TWILIO_PHONE_NUMBER,
            to=phone,
        )
        print(f"SMS sent to {phone}. Message SID: {message.sid}")
    except TwilioRestException as e:
        print(f"Error sending SMS: {e}")
        # Return an error to the user on the verification page if SMS fails
        return templates.TemplateResponse(
            "verify.html",
            {
                "request": request,
                "phone": phone,
                "error": "Could not send verification code. Please check the phone number and try again.",
            },
        )

    # Redirect to the verification page
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
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 10000)), reload=True)