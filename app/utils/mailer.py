"""
app/utils/mailer.py
--------------------
Utility for sending emails via SMTP (using aiosmtplib).
"""

import aiosmtplib
import uuid
import time
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("Mailer")

async def send_feedback_email(name: str, email: str, message: str):
    """
    Send a feedback email to the administrator.
    If SMTP settings are missing, it logs the message instead.
    """
    admin_email = "arorapratham758@gmail.com"
    
    # Check if we have core SMTP configuration
    if not settings.SMTP_HOST or not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning("SMTP NOT CONFIGURED. Simulating email delivery...")
        logger.info(f"--- SIMULATED EMAIL TO {admin_email} ---")
        return True

    # Create the email message with gold-standard headers
    msg = EmailMessage()
    msg["Subject"] = f"NEXUS Feedback: {name}"
    msg["From"] = settings.SMTP_USER
    msg["To"] = admin_email
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain="nexus.simulator")
    msg["MIME-Version"] = "1.0"
    
    msg.set_content(f"Feedback from: {name} <{email}>\n\nMessage:\n{message}")

    # Smart Protocol Detection and Password Sanitization
    # Port 465 usually expects implicit SSL/TLS (use_tls=True)
    # Port 587 usually expects explicit STARTTLS (starttls=True)
    use_tls_direct = (settings.SMTP_PORT == 465)
    use_starttls = (settings.SMTP_PORT == 587 or settings.SMTP_TLS)

    # Sanitize password: remove spaces (common with Gmail copy-paste)
    clean_password = settings.SMTP_PASSWORD.replace(" ", "").strip()

    # Manual SMTP Handshake (More robust across different library versions)
    smtp = aiosmtplib.SMTP(
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        use_tls=use_tls_direct,
        timeout=10,
    )

    try:
        await smtp.connect()
        
        # If we're on Port 587, we need explicit STARTTLS
        if use_starttls and not use_tls_direct:
            await smtp.starttls()

        # Perform Authentication
        await smtp.login(settings.SMTP_USER, clean_password)

        # Transmit Payload
        await smtp.send_message(msg)
        
        logger.info(f"Email sent successfully to {admin_email}")
        return True
    except aiosmtplib.SMTPAuthenticationError:
        logger.error("SMTP Authentication Failed: Check your username and App Password.")
        raise
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        raise
    finally:
        if smtp.is_connected:
            await smtp.quit()



