"""
app/api/feedback_routes.py
-------------------------
API routes for user feedback, sending emails to the architect.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, EmailStr
from typing import Optional
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
    except Exception as e:
        logger.error(f"Feedback submission failed: {e}")
        error_msg = str(e)
        
        # Determine specific error type for better user guidance
        if "Request failed" in error_msg:
            detail = "CONNECTION FAILED: Could not reach Resend API servers."
        elif "401" in error_msg or "unauthorized" in error_msg.lower() or "missing" in error_msg.lower():
            detail = "AUTHENTICATION FAILED: Check your Resend API Key."
        else:
            detail = f"TRANSMISSION FAILED: {error_msg}"
            
        raise HTTPException(status_code=500, detail=detail)

