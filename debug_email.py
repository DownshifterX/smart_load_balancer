import asyncio
import sys
import traceback
import os
from dotenv import load_dotenv

# Add current directory to path so we can import app modules
sys.path.append(os.getcwd())

# Force load .env
load_dotenv()

from app.utils.mailer import send_feedback_email
from app.config import settings

async def run_diagnostic():
    print("=" * 60)
    print(" [TOOL] NEXUS // EMAIL DIAGNOSTIC TOOL")
    print("=" * 60)
    
    print(f"\n[1] Checking Config:")
    print(f"    - Host:     {settings.SMTP_HOST}")
    print(f"    - Port:     {settings.SMTP_PORT}")
    print(f"    - User:     {settings.SMTP_USER}")
    print(f"    - Password: {'*'*len(settings.SMTP_PASSWORD) if settings.SMTP_PASSWORD else 'MISSING'}")
    print(f"    - TLS:      {settings.SMTP_TLS}")

    if not settings.SMTP_PASSWORD or "YOUR_APP_PASSWORD" in settings.SMTP_PASSWORD:
        print("\n[!] ERROR: SMTP_PASSWORD is not set correctly in your .env file.")
        return

    print("\n[2] Attempting to send test email...")
    print("    (This may take up to 20 seconds if it's timing out)\n")
    
    try:
        success = await send_feedback_email(
            name="Diagnostic Test",
            email="diagnostic@test.com",
            message="This is a local diagnostic test to find why mail isn't sending."
        )
        if success:
            print("\n[SUCCESS] Email sent successfully!")
            print("    Check your inbox (and spam folder) for 'NEXUS Feedback: Diagnostic Test'")
    except Exception as e:
        print("\n" + "!" * 60)
        print(" [FAILED] The email engine encountered an error.")
        print("!" * 60)
        print("\nERROR TYPE:", type(e).__name__)
        print("MESSAGE:   ", str(e))
        print("\nFULL TRACEBACK:")
        traceback.print_exc()
        print("\n" + "!" * 60)
        
        print("\n[FIXES] COMMON FIXES:")
        error_str = str(e).lower()
        if "timeout" in error_str or "10060" in error_str:
            print("  - Connection Timed Out. Your ISP likely blocks Port 465.")
            print("  - FIX: Try changing SMTP_PORT to 587 in .env and restart.")
        elif "certificate verify failed" in error_str:
            print("  - SSL Certificate Error. Your local Python can't find root CAs.")
            print("  - FIX: Run 'pip install certifi' and I will update the code to use it.")
        elif "authentication" in error_str or "535" in error_str:
            print("  - Password Rejected. Did you use a standard password or an 'App Password'?")
            print("  - FIX: You MUST use a 16-character Gmail App Password (no spaces).")
        elif "already using tls" in error_str:
            print("  - Protocol Conflict. The connection is already encrypted.")
            print("  - FIX: I will update the mailer logic to handle this correctly.")

if __name__ == "__main__":
    asyncio.run(run_diagnostic())
