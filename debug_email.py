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
    print(" [TOOL] NEXUS // EMAIL DIAGNOSTIC TOOL (RESEND API)")
    print("=" * 60)
    
    print(f"\n[1] Checking Config:")
    print(f"    - RESEND_API_KEY: {'*'*15 + settings.RESEND_API_KEY[-4:] if settings.RESEND_API_KEY else 'MISSING'}")

    if not settings.RESEND_API_KEY or "YOUR_KEY_HERE" in settings.RESEND_API_KEY:
        print("\n[!] ERROR: RESEND_API_KEY is not set correctly in your .env file.")
        print("    Please create a free account at resend.com, generate an API key,")
        print("    and paste it into your .env file.")
        return

    print("\n[2] Attempting to send test email via Resend API...")
    print("    (This should be fast, using standard HTTPS)\n")
    
    try:
        success = await send_feedback_email(
            name="Diagnostic Test",
            email="diagnostic@test.com",
            message="This is a local diagnostic test to find why mail isn't sending."
        )
        if success:
            print("\n[SUCCESS] Email sent successfully via Resend API!")
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
        if "401" in error_str or "unauthorized" in error_str:
            print("  - API Key Rejected. The API key in your .env is invalid.")
            print("  - FIX: Generate a new key in the Resend dashboard.")
        elif "request failed" in error_str:
            print("  - Connection Error. Could not reach api.resend.com.")
            print("  - FIX: Check your internet connection. (HTTPS Port 443 must be open).")

if __name__ == "__main__":
    asyncio.run(run_diagnostic())
