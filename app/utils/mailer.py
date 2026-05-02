"""
app/utils/mailer.py
--------------------
Utility for sending emails via HTTP API (Resend).
"""

import httpx
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("Mailer")

async def send_feedback_email(name: str, email: str, message: str):
    """
    Send a feedback email to the administrator using the Resend API.
    If the API key is missing, it logs the message instead.
    """
    admin_email = "arorapratham758@gmail.com"
    
    # Check if we have the API key configured
    if not settings.RESEND_API_KEY or "YOUR_KEY_HERE" in settings.RESEND_API_KEY:
        logger.warning("RESEND_API_KEY NOT CONFIGURED. Simulating email delivery...")
        logger.info(f"--- SIMULATED EMAIL TO {admin_email} ---")
        return True

    # Resend API endpoint and headers
    url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {settings.RESEND_API_KEY.strip()}",
        "Content-Type": "application/json"
    }

    # Payload for the email
    payload = {
        "from": "NEXUS Simulator <onboarding@resend.dev>",
        "to": [admin_email],
        "subject": f"NEXUS Feedback: {name}",
        "text": f"Feedback from: {name} <{email}>\n\nMessage:\n{message}"
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            
            if response.status_code == 200 or response.status_code == 201:
                logger.info(f"Email sent successfully to {admin_email} via Resend")
                return True
            else:
                error_msg = f"Resend API Error {response.status_code}: {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
    except httpx.RequestError as e:
        logger.error(f"HTTP Request failed while connecting to Resend: {e}")
        raise
