"""
app/api/server_routes.py
-------------------------
API routes for managing simulated server nodes:
list, add, remove, toggle health, adjust weight, simulate failures.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/servers", tags=["servers"])

# Reference to simulation engine
engine = None


def set_engine(sim_engine):
    global engine
    engine = sim_engine


class AddServerRequest(BaseModel):
    name: Optional[str] = None
    region: Optional[str] = ""
    weight: int = 1
    max_connections: int = 100
    response_time_base: float = 50.0


class UpdateServerRequest(BaseModel):
    name: Optional[str] = None
    region: Optional[str] = None
    weight: Optional[int] = None
    max_connections: Optional[int] = None


class UpdateWeightRequest(BaseModel):
    weight: int


class LatencyRequest(BaseModel):
    latency_ms: float = 500.0


@router.get("")
async def list_servers():
    """List all servers with their current state."""
    return {"servers": [s.to_dict() for s in engine.servers]}


@router.post("")
async def add_server(body: AddServerRequest):
    """Add a new server node."""
    try:
        server = engine.add_server(
            name=body.name,
            region=body.region,
            weight=body.weight,
            max_connections=body.max_connections,
            response_time_base=body.response_time_base,
        )
        return {"status": "ok", "server": server.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{server_id}")
async def edit_server(server_id: str, body: UpdateServerRequest):
    """Edit server configuration dynamically."""
    server = engine.update_server(
        server_id,
        name=body.name,
        region=body.region,
        weight=body.weight,
        max_connections=body.max_connections,
    )
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    return {"status": "ok", "server": server.to_dict()}


@router.delete("/{server_id}")
async def remove_server(server_id: str):
    """Remove a server by ID."""
    if engine.remove_server(server_id):
        return {"status": "ok", "message": f"Server {server_id} removed"}
    raise HTTPException(status_code=404, detail="Server not found")


@router.post("/{server_id}/toggle")
async def toggle_server(server_id: str):
    """Toggle server healthy/unhealthy."""
    server = engine.get_server(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    if server.healthy and server.enabled:
        server.healthy = False
        server.enabled = False
        status = "disabled"
    else:
        server.recover()
        server.enabled = True
        status = "enabled"

    return {"status": "ok", "server_status": status, "server": server.to_dict()}


@router.put("/{server_id}/weight")
async def update_weight(server_id: str, body: UpdateWeightRequest):
    """Update server weight."""
    server = engine.get_server(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    server.weight = max(1, min(10, body.weight))
    return {"status": "ok", "weight": server.weight, "server": server.to_dict()}


@router.post("/{server_id}/simulate-failure")
async def simulate_failure(server_id: str):
    """Simulate a server crash."""
    server = engine.get_server(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    server.simulate_failure()
    return {"status": "ok", "message": f"{server.name} crashed", "server": server.to_dict()}


@router.post("/{server_id}/simulate-latency")
async def simulate_latency(server_id: str, body: LatencyRequest):
    """Inject artificial latency."""
    server = engine.get_server(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    server.simulate_latency(body.latency_ms)
    return {"status": "ok", "message": f"{server.name} latency +{body.latency_ms}ms", "server": server.to_dict()}


@router.post("/{server_id}/simulate-overload")
async def simulate_overload(server_id: str):
    """Put server in overload state."""
    server = engine.get_server(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    server.simulate_overload()
    return {"status": "ok", "message": f"{server.name} overloaded", "server": server.to_dict()}


@router.post("/{server_id}/recover")
async def recover_server(server_id: str):
    """Recover server from all simulated issues."""
    server = engine.get_server(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    server.recover()
    return {"status": "ok", "message": f"{server.name} recovered", "server": server.to_dict()}
