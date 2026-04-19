"""
app/api/metrics_routes.py
--------------------------
API routes for metrics, analytics, alerts, and logs.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api", tags=["metrics"])

# Reference to simulation engine
engine = None


def set_engine(sim_engine):
    global engine
    engine = sim_engine


@router.get("/metrics")
async def get_metrics():
    """Get current aggregate metrics."""
    return engine.metrics.to_dict()


@router.get("/metrics/history")
async def get_metrics_history():
    """Get time-series data for charts."""
    return engine.metrics.history_to_dict()


@router.get("/metrics/servers")
async def get_server_metrics():
    """Get per-server metrics."""
    return {"servers": [s.to_dict() for s in engine.servers]}


@router.get("/metrics/export")
async def export_metrics():
    """Export full metrics as JSON download."""
    data = {
        "metrics": engine.metrics.to_dict(),
        "history": engine.metrics.history_to_dict(),
        "servers": [s.to_dict() for s in engine.servers],
        "algorithm_comparison": engine.metrics.algorithm_stats,
        "alerts": engine.alert_manager.get_history(),
        "simulation": engine.get_status(),
    }
    return JSONResponse(content=data, headers={
        "Content-Disposition": "attachment; filename=lb_metrics_export.json"
    })


@router.get("/alerts")
async def get_alerts():
    """Get active alerts and recommendations."""
    return {
        "active": engine.alert_manager.get_active(),
        "history": engine.alert_manager.get_history(limit=50),
    }


@router.get("/logs")
async def get_logs():
    """Get recent log entries."""
    return {"logs": list(engine.log_entries)[-100:]}


@router.get("/analytics")
async def get_analytics():
    """Get analytics data: utilization, bottlenecks, recommendations."""
    servers = engine.servers
    healthy = [s for s in servers if s.healthy]

    # Server utilization distribution
    utilization = []
    for s in servers:
        utilization.append({
            "id": s.id,
            "name": s.name,
            "cpu": round(s.cpu_usage, 1),
            "memory": round(s.memory_usage, 1),
            "connections": s.connection_utilization,
            "requests": s.total_requests,
        })

    # Detect bottlenecks
    bottlenecks = []
    for s in servers:
        if s.status.value == "OVERLOADED":
            bottlenecks.append({
                "server": s.name,
                "reason": "CPU/connections at capacity",
                "cpu": round(s.cpu_usage, 1),
                "connections": s.active_connections,
            })

    # Load imbalance check
    if healthy:
        req_counts = [s.total_requests for s in healthy]
        avg_req = sum(req_counts) / len(req_counts) if req_counts else 0
        max_req = max(req_counts) if req_counts else 0
        min_req = min(req_counts) if req_counts else 0
        imbalance_ratio = max_req / max(1, avg_req)
    else:
        imbalance_ratio = 0

    return {
        "utilization": utilization,
        "bottlenecks": bottlenecks,
        "imbalance_ratio": round(imbalance_ratio, 2),
        "total_servers": len(servers),
        "healthy_servers": len(healthy),
        "algorithm_comparison": engine.metrics.algorithm_stats,
    }


@router.get("/settings")
async def get_settings():
    """Get current simulation settings."""
    return {
        "sticky_sessions": engine.sticky_sessions_enabled,
        "auto_scaling": engine.auto_scaling_enabled,
        "auto_scale_min": engine.auto_scale_min,
        "auto_scale_max": engine.auto_scale_max,
        "auto_scale_up_threshold": engine.auto_scale_up_threshold,
        "auto_scale_down_threshold": engine.auto_scale_down_threshold,
        "tick_interval_ms": int(engine.tick_interval * 1000),
        "traffic_mode": engine.traffic_mode,
        "algorithm": engine.current_algorithm_name,
    }


class SettingsUpdate:
    pass


@router.post("/settings")
async def update_settings(settings: dict):
    """Update simulation settings."""
    if "sticky_sessions" in settings:
        engine.sticky_sessions_enabled = bool(settings["sticky_sessions"])
    if "auto_scaling" in settings:
        engine.auto_scaling_enabled = bool(settings["auto_scaling"])
    if "auto_scale_min" in settings:
        engine.auto_scale_min = max(1, int(settings["auto_scale_min"]))
    if "auto_scale_max" in settings:
        engine.auto_scale_max = min(20, int(settings["auto_scale_max"]))
    if "auto_scale_up_threshold" in settings:
        engine.auto_scale_up_threshold = int(settings["auto_scale_up_threshold"])
    if "auto_scale_down_threshold" in settings:
        engine.auto_scale_down_threshold = int(settings["auto_scale_down_threshold"])
    if "tick_interval_ms" in settings:
        engine.tick_interval = max(100, int(settings["tick_interval_ms"])) / 1000.0

    return {"status": "ok", "message": "Settings updated"}
