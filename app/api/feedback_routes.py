"""
app/api/feedback_routes.py
-------------------------
API routes for user feedback, sending emails to the architect.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, EmailStr
from typing import Optional
import aiosmtplib
from app.utils.mailer import send_feedback_email
from app.utils.logger import get_logger

logger = get_logger("FeedbackAPI")

router = APIRouter(prefix="/api/feedback", tags=["feedback"])

class FeedbackRequest(BaseModel):
    name: str
    email: EmailStr
    message: str

@router.post("")
async def submit_feedback(body: FeedbackRequest):
    """Submit user feedback and send it via email (Synchronous for real-time error reporting)."""
    try:
        # We now await the call directly to provide real-time status to the dashboard
        await send_feedback_email(
            name=body.name, 
            email=body.email, 
            message=body.message
        )
        return {"status": "ok", "message": "Feedback submitted successfully. Thank you!"}
    except aiosmtplib.SMTPAuthenticationError:
        logger.error("Feedback failed: SMTP Authentication Error")
        raise HTTPException(
            status_code=401, 
            detail="AUTHENTICATION FAILED: Check your Gmail App Password. (Ensure it is 16 characters long)"
        )
    except Exception as e:
        logger.error(f"Feedback submission failed: {e}")
        error_msg = str(e)
        
        # Determine specific error type for better user guidance
        if "connect" in error_msg.lower():
            detail = "CONNECTION FAILED: Could not reach Gmail servers. (Check port or firewall)"
        elif "authentication" in error_msg.lower() or "535" in error_msg:
            detail = "AUTHENTICATION FAILED: Check your Gmail App Password."
        elif "tls" in error_msg.lower() or "ssl" in error_msg.lower():
            detail = "ENCRYPTION ERROR: SSL/TLS handshake failed."
        else:
            detail = f"TRANSMISSION FAILED: {error_msg}"
            
        raise HTTPException(status_code=500, detail=detail)

