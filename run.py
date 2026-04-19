"""
run.py — Entry point for the Smart Load Balancer Simulator
Usage: python run.py
"""

import uvicorn
from app.config import settings

if __name__ == "__main__":
    try:
        uvicorn.run(
            "app.main:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=True,
            log_level=settings.LOG_LEVEL.lower(),
        )
    except Exception as e:
        if "address already in use" in str(e).lower() or "10048" in str(e):
            print("\n" + "!"*60)
            print(f" ERROR: Port {settings.PORT} is already occupied.")
            print(" Ensure no other instances are running or choose a different PORT in .env")
            print("!"*60 + "\n")
        else:
            raise e
