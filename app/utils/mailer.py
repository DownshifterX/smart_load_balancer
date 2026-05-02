"""
app/utils/mailer.py
--------------------
Utility for sending emails via standard SMTP.
"""

import aiosmtplib
from email.message import EmailMessage
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("Mailer")

async def send_feedback_email(name: str, email: str, message: str):
    """
    Send a feedback email to the administrator using SMTP.
    If the SMTP password is missing, it logs the message instead.
    """
    admin_email = "arorapratham758@gmail.com"
    
    # Check if we have the password configured
    if not settings.SMTP_PASSWORD or "YOUR_APP_PASSWORD" in settings.SMTP_PASSWORD:
        logger.warning("SMTP_PASSWORD NOT CONFIGURED. Simulating email delivery...")
        logger.info(f"--- SIMULATED EMAIL TO {admin_email} ---")
        logger.info(f"From: {name} <{email}>")
        logger.info(f"Message: {message}")
        return True

    # Prepare Email Message
    msg = EmailMessage()
    msg["Subject"] = f"NEXUS Feedback: {name}"
    msg["From"] = f"NEXUS Simulator <{settings.SMTP_USER}>"
    msg["To"] = admin_email
    msg.set_content(f"Feedback from: {name} <{email}>\n\nMessage:\n{message}")

    # Port 465 usually expects implicit SSL/TLS (use_tls=True)
    # Port 587 usually expects explicit STARTTLS (starttls=True)
    use_tls_direct = (settings.SMTP_PORT == 465)
    
    # Sanitize password: remove spaces (common with Gmail copy-paste)
    clean_password = settings.SMTP_PASSWORD.replace(" ", "").strip()

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=clean_password,
            use_tls=use_tls_direct,
            start_tls=settings.SMTP_TLS if not use_tls_direct else False,
            timeout=15,
        )
        
        logger.info(f"Email sent successfully to {admin_email} via SMTP")
        return True
    except aiosmtplib.SMTPAuthenticationError:
        logger.error("SMTP Authentication Failed: Check your username and App Password.")
        raise
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        raise
