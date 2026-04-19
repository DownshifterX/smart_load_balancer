"""
app/api/simulation_routes.py
------------------------------
API routes for controlling the simulation:
start, stop, reset, traffic modes, spikes, manual requests.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/simulation", tags=["simulation"])

# Reference to simulation engine — set by main.py
engine = None


def set_engine(sim_engine):
    global engine
    engine = sim_engine


class TrafficModeRequest(BaseModel):
    mode: str


class CustomRPSRequest(BaseModel):
    rps: int


class SpikeRequest(BaseModel):
    duration_ticks: int = 10
    multiplier: int = 5


class ManualRequestBody(BaseModel):
    source_ip: Optional[str] = None


class SettingsUpdateRequest(BaseModel):
    tick_interval_ms: Optional[int] = None
    sticky_sessions: Optional[bool] = None
    auto_scaling: Optional[bool] = None
    auto_scale_min: Optional[int] = None
    auto_scale_max: Optional[int] = None
    auto_scale_up_threshold: Optional[int] = None
    auto_scale_down_threshold: Optional[int] = None


@router.post("/start")
async def start_simulation():
    """Start the simulation loop."""
    await engine.start()
    return {"status": "started", "message": "Simulation started"}


@router.post("/stop")
async def stop_simulation():
    """Stop the simulation loop."""
    await engine.stop()
    return {"status": "stopped", "message": "Simulation stopped"}


@router.post("/reset")
async def reset_simulation():
    """Reset all simulation state and metrics."""
    engine.reset()
    return {"status": "reset", "message": "Simulation reset"}


@router.get("/status")
async def get_status():
    """Get current simulation status."""
    return engine.get_status()


@router.post("/traffic")
async def set_traffic_mode(body: TrafficModeRequest):
    """Set traffic generation mode."""
    try:
        engine.set_traffic_mode(body.mode)
        return {"status": "ok", "traffic_mode": body.mode}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/custom-rps")
async def set_custom_rps(body: CustomRPSRequest):
    """Set custom requests per tick."""
    engine.set_custom_rps(body.rps)
    return {"status": "ok", "rps": engine.custom_rps}


@router.post("/spike")
async def trigger_spike(body: SpikeRequest):
    """Trigger a traffic spike."""
    engine.trigger_spike(body.duration_ticks, body.multiplier)
    return {"status": "ok", "message": f"Spike triggered: {body.multiplier}x for {body.duration_ticks} ticks"}


@router.post("/request")
async def send_manual_request(body: ManualRequestBody):
    """Send a single manual request."""
    result = engine.send_manual_request(body.source_ip)
    return result


@router.get("/settings")
async def get_settings():
    """Get current global simulation settings."""
    state = engine.get_full_state()
    return state["simulation"]


@router.post("/settings")
async def update_settings(body: SettingsUpdateRequest):
    """Update global simulation settings."""
    engine.update_settings(body.model_dump(exclude_none=True))
    return {"status": "ok", "settings": engine.get_status()}


# ── Raft Control Plane endpoints

@router.post("/raft/kill/{node_id}")
async def kill_raft_node(node_id: str):
    """Kill a specific Raft Control Node."""
    engine.raft.kill_node(node_id)
    return {"status": "ok", "message": f"Killed Raft node: {node_id}"}


@router.post("/raft/recover/{node_id}")
async def recover_raft_node(node_id: str):
    """Recover a specific Raft Control Node."""
    engine.raft.revive_node(node_id)
    return {"status": "ok", "message": f"Recovered Raft node: {node_id}"}
