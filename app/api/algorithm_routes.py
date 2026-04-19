"""
app/api/algorithm_routes.py
-----------------------------
API routes for algorithm management:
list available algorithms, get/switch current, performance comparison.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.algorithms import list_algorithms, ALGORITHM_REGISTRY

router = APIRouter(prefix="/api/algorithms", tags=["algorithms"])

# Reference to simulation engine
engine = None


def set_engine(sim_engine):
    global engine
    engine = sim_engine


class SwitchAlgorithmRequest(BaseModel):
    algorithm: str


@router.get("")
async def get_algorithms():
    """List all available load balancing algorithms."""
    algorithms = list_algorithms()
    # Mark the current one
    for algo in algorithms:
        algo["active"] = algo["id"] == engine.current_algorithm_name
    return {"algorithms": algorithms}


@router.get("/current")
async def get_current_algorithm():
    """Get the currently active algorithm."""
    return {
        "algorithm": engine.current_algorithm_name,
        "name": engine.algorithm.name,
        "description": engine.algorithm.description,
    }


@router.post("/switch")
async def switch_algorithm(body: SwitchAlgorithmRequest):
    """Switch to a different load balancing algorithm."""
    if body.algorithm not in ALGORITHM_REGISTRY:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown algorithm: {body.algorithm}. Available: {list(ALGORITHM_REGISTRY.keys())}"
        )
    engine.switch_algorithm(body.algorithm)
    return {
        "status": "ok",
        "algorithm": engine.current_algorithm_name,
        "name": engine.algorithm.name,
    }


@router.get("/compare")
async def compare_algorithms():
    """Get performance comparison data for all tested algorithms."""
    return {"comparison": engine.metrics.algorithm_stats}
