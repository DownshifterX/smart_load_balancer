"""
app/main.py
------------
FastAPI application entry point.
Mounts all API routers, serves the frontend, and manages
the simulation engine lifecycle.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os

from app.core.simulation import SimulationEngine
from app.api import simulation_routes, server_routes, algorithm_routes, metrics_routes, websocket_routes, feedback_routes
from app.utils.logger import get_logger

logger = get_logger("Main")

# ── Create FastAPI app ────────────────────────────────────────────────────
app = FastAPI(
    title="Smart Load Balancer Simulator",
    description="Real-time load balancing simulator with Matrix-themed dashboard",
    version="1.0.0",
)

# ── CORS Middleware ───────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Create simulation engine ─────────────────────────────────────────────
engine = SimulationEngine()

# Wire engine into route modules
simulation_routes.set_engine(engine)
server_routes.set_engine(engine)
algorithm_routes.set_engine(engine)
metrics_routes.set_engine(engine)

# Set WebSocket broadcast callback
engine.set_broadcast_callback(websocket_routes.broadcast)

# ── Mount API routers ────────────────────────────────────────────────────
app.include_router(simulation_routes.router)
app.include_router(server_routes.router)
app.include_router(algorithm_routes.router)
app.include_router(metrics_routes.router)
app.include_router(websocket_routes.router)
app.include_router(feedback_routes.router)

# ── Serve Frontend Static Files ──────────────────────────────────────────
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")

# Mount static directories
if os.path.isdir(os.path.join(frontend_dir, "css")):
    app.mount("/css", StaticFiles(directory=os.path.join(frontend_dir, "css")), name="css")
if os.path.isdir(os.path.join(frontend_dir, "js")):
    app.mount("/js", StaticFiles(directory=os.path.join(frontend_dir, "js")), name="js")
if os.path.isdir(os.path.join(frontend_dir, "assets")):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dir, "assets")), name="assets")


@app.get("/")
async def serve_index():
    """Serve the main dashboard page."""
    index_path = os.path.join(frontend_dir, "index.html")
    return FileResponse(index_path)


@app.get("/health")
async def health_check():
    """Simple liveness check."""
    return {"status": "OK", "service": "Smart Load Balancer Simulator"}


# ── Lifecycle Events ─────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    logger.info("=" * 60)
    logger.info("  Smart Load Balancer Simulator — Starting Up")
    logger.info("=" * 60)
    logger.info(f"  Servers initialized: {len(engine.servers)}")
    logger.info(f"  Algorithm: {engine.current_algorithm_name}")
    logger.info(f"  Frontend: {frontend_dir}")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown():
    logger.info("Shutting down simulation engine...")
    await engine.stop()
    logger.info("Shutdown complete.")
