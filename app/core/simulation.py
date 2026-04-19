"""
app/core/simulation.py
-----------------------
The simulation engine — heart of the load balancer simulator.
Manages the async tick loop, generates simulated requests,
routes them through the selected algorithm, updates server states,
collects metrics, and broadcasts updates via WebSocket.
"""

import asyncio
import time
import random
from collections import deque
from app.core.server_node import ServerNode
from app.core.request_model import SimulatedRequest
from app.core.metrics import MetricsCollector
from app.core.alerts import AlertManager
from app.core.raft import RaftCluster
from app.algorithms import get_algorithm, ALGORITHM_REGISTRY
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("SimulationEngine")


# Traffic mode → requests per tick
TRAFFIC_MODES = {
    "stopped": 0,
    "slow": 1,
    "normal": 3,
    "heavy": 8,
    "burst": 20,
}


class SimulationEngine:
    """
    Core simulation engine that orchestrates the entire load balancing simulation.
    Runs an async tick loop that generates requests, routes them, and updates state.
    """

    def __init__(self):
        # Servers
        self.servers: list[ServerNode] = []
        self._server_counter = 0

        # Algorithm
        self.current_algorithm_name = settings.DEFAULT_ALGORITHM
        self.algorithm = get_algorithm(self.current_algorithm_name)

        # Metrics & Alerts
        self.metrics = MetricsCollector()
        self.alert_manager = AlertManager()

        # Simulation state
        self.running = False
        self.traffic_mode = settings.DEFAULT_TRAFFIC_MODE
        self.custom_rps: int = 5
        self.tick_interval = settings.SIMULATION_TICK_MS / 1000.0

        # Request log (recent requests for the frontend stream)
        self.request_log: deque = deque(maxlen=200)
        self.log_entries: deque = deque(maxlen=500)

        # Raft Control Plane
        self.raft = RaftCluster()

        # Sticky sessions
        self.sticky_sessions_enabled = False
        self._session_map: dict[str, str] = {}  # IP → server_id

        # Auto-scaling
        self.auto_scaling_enabled = False
        self.auto_scale_min = 2
        self.auto_scale_max = 8
        self.auto_scale_up_threshold = 70  # CPU %
        self.auto_scale_down_threshold = 20  # CPU %

        # Task reference
        self._task: asyncio.Task | None = None

        # WebSocket broadcast callback
        self._broadcast_callback = None

        # Initialize with default servers
        self._init_default_servers()

    def _init_default_servers(self):
        """Create initial set of servers."""
        default_configs = [
            {"name": "NODE-ALPHA", "weight": 1, "max_connections": 100, "response_time_base": 45},
            {"name": "NODE-BETA", "weight": 1, "max_connections": 120, "response_time_base": 55},
            {"name": "NODE-GAMMA", "weight": 2, "max_connections": 150, "response_time_base": 40},
            {"name": "NODE-DELTA", "weight": 1, "max_connections": 80, "response_time_base": 60},
        ]
        for cfg in default_configs:
            self.add_server(**cfg)

    def set_broadcast_callback(self, callback):
        """Set the WebSocket broadcast function."""
        self._broadcast_callback = callback

    # ── Server Management ────────────────────────────────────────────────

    def add_server(self, name: str = None, region: str = "", weight: int = 1,
                   max_connections: int = 100, response_time_base: float = 50) -> ServerNode:
        """Add a new server node to the simulation."""
        if len(self.servers) >= settings.MAX_SERVERS:
            raise ValueError(f"Maximum server limit ({settings.MAX_SERVERS}) reached")

        self._server_counter += 1
        server = ServerNode(
            name=name or f"NODE-{self._server_counter:03d}",
            region=region,
            weight=weight,
            max_connections=max_connections,
            response_time_base=response_time_base,
        )
        self.servers.append(server)
        self._add_log("SYSTEM", f"Server {server.name} ({server.region}) added to pool")
        logger.info(f"Server added: {server.name} [{server.region}]")
        return server

    def update_server(self, server_id: str, name: str = None, region: str = None, weight: int = None, max_connections: int = None) -> ServerNode | None:
        """Update an existing server's configuration dynamically."""
        for srv in self.servers:
            if srv.id == server_id:
                srv.update_config(name, region, weight, max_connections)
                self._add_log("SYSTEM", f"Server {srv.name} config updated")
                return srv
        return None

    def remove_server(self, server_id: str) -> bool:
        """Remove a server by ID."""
        for i, srv in enumerate(self.servers):
            if srv.id == server_id:
                removed = self.servers.pop(i)
                # Clean up session map
                self._session_map = {
                    k: v for k, v in self._session_map.items() if v != server_id
                }
                self._add_log("SYSTEM", f"Server {removed.name} removed from pool")
                logger.info(f"Server removed: {removed.name}")
                return True
        return False

    def get_server(self, server_id: str) -> ServerNode | None:
        """Get a server by ID."""
        for srv in self.servers:
            if srv.id == server_id:
                return srv
        return None

    def get_healthy_servers(self) -> list[ServerNode]:
        """Get all servers that can accept requests."""
        return [s for s in self.servers if s.can_accept_request()]

    # ── Algorithm Management ─────────────────────────────────────────────

    def switch_algorithm(self, algorithm_name: str):
        """Switch to a different load balancing algorithm."""
        self.algorithm = get_algorithm(algorithm_name)
        old_name = self.current_algorithm_name
        self.current_algorithm_name = algorithm_name
        self._add_log("SYSTEM", f"Algorithm switched: {old_name} → {algorithm_name}")
        logger.info(f"Algorithm switched to: {algorithm_name}")

    # ── Traffic Controls ─────────────────────────────────────────────────

    def set_traffic_mode(self, mode: str):
        """Set traffic generation mode."""
        if mode not in TRAFFIC_MODES and mode != "custom":
            raise ValueError(f"Unknown traffic mode: {mode}. Available: {list(TRAFFIC_MODES.keys()) + ['custom']}")
        self.traffic_mode = mode
        self._add_log("TRAFFIC", f"Traffic mode set to: {mode}")

    def set_custom_rps(self, rps: int):
        """Set custom requests per tick."""
        self.custom_rps = max(1, min(50, rps))
        self.traffic_mode = "custom"
        self._add_log("TRAFFIC", f"Custom traffic rate set: {self.custom_rps} req/tick")

    def trigger_spike(self, duration_ticks: int = 10, multiplier: int = 5):
        """Trigger a traffic spike by temporarily increasing traffic."""
        self._spike_remaining = duration_ticks
        self._spike_multiplier = multiplier
        self._add_log("TRAFFIC", f"⚡ Traffic spike triggered: {multiplier}x for {duration_ticks} ticks")

    # ── Simulation Control ───────────────────────────────────────────────

    async def start(self):
        """Start the simulation loop."""
        if self.running:
            return
        self.running = True
        self._spike_remaining = 0
        self._spike_multiplier = 1
        self._task = asyncio.create_task(self._tick_loop())
        self._add_log("SYSTEM", "▶ Simulation STARTED")
        logger.info("Simulation started")

    async def stop(self):
        """Stop the simulation loop."""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        self._add_log("SYSTEM", "⏹ Simulation STOPPED")
        logger.info("Simulation stopped")

    def reset(self):
        """Reset all simulation state."""
        for srv in self.servers:
            srv.reset_metrics()
            srv.recover()
        self.metrics.reset()
        self.alert_manager.reset()
        self.request_log.clear()
        self.log_entries.clear()
        self._session_map.clear()
        self.algorithm.reset()
        self._add_log("SYSTEM", "🔄 Simulation RESET")
        logger.info("Simulation reset")

    # ── Main Tick Loop ───────────────────────────────────────────────────

    async def _tick_loop(self):
        """Main simulation loop — runs each tick."""
        logger.info(f"Tick loop started (interval: {self.tick_interval}s)")
        while self.running:
            try:
                await self._process_tick()
                await asyncio.sleep(self.tick_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Tick error: {e}")
                await asyncio.sleep(self.tick_interval)

    async def _process_tick(self):
        """Process a single simulation tick."""
        # Tick the Raft control plane
        self.raft.simulate_tick()
        has_leader = self.raft.get_leader() is not None
        
        # Determine how many requests to generate
        num_requests = self._get_requests_per_tick()

        # Generate and route requests
        tick_requests = []
        for _ in range(num_requests):
            req = SimulatedRequest()
            
            if not has_leader:
                # RAFT ELECTION: Control plane is down, drop traffic!
                req.complete("NONE", "ELECTION_DOWNTIME", 0, False)
                self.metrics.record_request(0, False)
                self.request_log.append(req.to_dict())
                if random.random() < 0.1: # Don't spam logs
                    self._add_log("CRITICAL", f"REQ {req.id} dropped: Raft election in progress")
            else:
                result = self._route_request(req)
                
            tick_requests.append(req)

        # Update server states
        for srv in self.servers:
            srv.simulate_tick()

        total_connections = sum(s.active_connections for s in self.servers)
        self.metrics.record_tick(total_connections)

        # Record algorithm snapshot
        self.metrics.record_algorithm_snapshot(
            self.current_algorithm_name,
            self.metrics.avg_response_time,
            self.metrics.success_rate,
            100.0  # Placeholder for distribution score
        )

        # Evaluate alerts
        server_dicts = [s.to_dict() for s in self.servers]
        self.alert_manager.evaluate(
            server_dicts,
            self.metrics.to_dict(),
            self.current_algorithm_name
        )

        # Auto-scaling check
        if self.auto_scaling_enabled:
            self._check_auto_scaling()

        # Broadcast update via WebSocket
        if self._broadcast_callback:
            state = self.get_full_state()
            await self._broadcast_callback(state)

    def _get_requests_per_tick(self) -> int:
        """Calculate how many requests to generate this tick."""
        if self.traffic_mode == "custom":
            base = self.custom_rps
        else:
            base = TRAFFIC_MODES.get(self.traffic_mode, 0)

        # Apply spike multiplier
        if hasattr(self, "_spike_remaining") and self._spike_remaining > 0:
            base *= self._spike_multiplier
            self._spike_remaining -= 1
            if self._spike_remaining == 0:
                self._add_log("TRAFFIC", "Traffic spike ended")

        # Add some randomness
        if base > 0:
            base = max(1, base + random.randint(-1, 2))

        return base

    def _route_request(self, request: SimulatedRequest) -> dict | None:
        """Route a single request through the load balancer."""
        healthy = self.get_healthy_servers()

        if not healthy:
            request.complete("NONE", "NO_SERVER", 0, False)
            self.metrics.record_request(0, False)
            self.request_log.append(request.to_dict())
            self._add_log("ERROR", f"REQ {request.id} — No healthy servers available")
            return None

        # Sticky sessions: check if this IP has a session
        selected = None
        if self.sticky_sessions_enabled and request.source_ip in self._session_map:
            session_server_id = self._session_map[request.source_ip]
            selected = next((s for s in healthy if s.id == session_server_id), None)

        # Use algorithm to select server
        if selected is None:
            selected = self.algorithm.select_server(healthy, request)

        if selected is None:
            request.complete("NONE", "NO_SERVER", 0, False)
            self.metrics.record_request(0, False)
            self.request_log.append(request.to_dict())
            return None

        # Process request on selected server
        result = selected.process_request()
        request.complete(selected.id, selected.name, result["response_time"], result["success"])

        # Update session map for sticky sessions
        if self.sticky_sessions_enabled:
            self._session_map[request.source_ip] = selected.id

        # Record metrics
        self.metrics.record_request(result["response_time"], result["success"])
        self.request_log.append(request.to_dict())

        # Log
        status = "✓" if result["success"] else "✗"
        self._add_log(
            "REQUEST",
            f"[{status}] REQ {request.id} → {selected.name} | {result['response_time']}ms | {request.source_ip}"
        )

        # Retry on failure
        if not result["success"] and len(healthy) > 1:
            request.retried = True
            request.retry_count += 1
            retry_servers = [s for s in healthy if s.id != selected.id]
            if retry_servers:
                retry_server = self.algorithm.select_server(retry_servers, request)
                if retry_server:
                    retry_result = retry_server.process_request()
                    self._add_log(
                        "RETRY",
                        f"REQ {request.id} retried → {retry_server.name} | {'✓' if retry_result['success'] else '✗'}"
                    )

        return result

    def send_manual_request(self, source_ip: str = None) -> dict:
        """Send a single manual request (from the UI)."""
        req = SimulatedRequest(source_ip=source_ip)
        result = self._route_request(req)
        return req.to_dict()

    # ── Auto-scaling ─────────────────────────────────────────────────────

    def _check_auto_scaling(self):
        """Check if auto-scaling should add or remove servers."""
        if not self.servers:
            return

        avg_cpu = sum(s.cpu_usage for s in self.servers if s.healthy) / max(1, len([s for s in self.servers if s.healthy]))

        if avg_cpu > self.auto_scale_up_threshold and len(self.servers) < self.auto_scale_max:
            new_srv = self.add_server()
            self._add_log("AUTOSCALE", f"↑ Scaled UP: Added {new_srv.name} (avg CPU: {avg_cpu:.0f}%)")

        elif avg_cpu < self.auto_scale_down_threshold and len(self.servers) > self.auto_scale_min:
            # Remove the server with lowest load
            candidates = sorted(self.servers, key=lambda s: s.active_connections)
            if candidates:
                self.remove_server(candidates[0].id)
                self._add_log("AUTOSCALE", f"↓ Scaled DOWN: Removed {candidates[0].name} (avg CPU: {avg_cpu:.0f}%)")

        # Reconciliation: Ensure MIN servers is met regardless of CPU
        while len(self.servers) < self.auto_scale_min:
            new_srv = self.add_server()
            self._add_log("AUTOSCALE", f"📡 RECONCILE: Added {new_srv.name} to meet MIN pool requirement")

        # Reconciliation: Ensure MAX servers is not exceeded
        while len(self.servers) > self.auto_scale_max:
            candidates = sorted(self.servers, key=lambda s: s.active_connections)
            self.remove_server(candidates[0].id)
            self._add_log("AUTOSCALE", f"📡 RECONCILE: Removed {candidates[0].name} to respect MAX pool limit")

    # ── Settings Management ──────────────────────────────────────────────

    def update_settings(self, config: dict):
        """Update global simulation settings."""
        if "tick_interval_ms" in config:
            self.tick_interval = max(100, min(5000, config["tick_interval_ms"])) / 1000.0
            logger.info(f"Tick interval updated to {self.tick_interval}s")

        if "sticky_sessions" in config:
            self.sticky_sessions_enabled = bool(config["sticky_sessions"])
            if not self.sticky_sessions_enabled:
                self._session_map.clear()

        if "auto_scaling" in config:
            self.auto_scaling_enabled = bool(config["auto_scaling"])

        if "auto_scale_min" in config:
            self.auto_scale_min = max(1, config["auto_scale_min"])
        
        if "auto_scale_max" in config:
            self.auto_scale_max = max(self.auto_scale_min, config["auto_scale_max"])

        if "auto_scale_up_threshold" in config:
            self.auto_scale_up_threshold = max(10, min(95, config["auto_scale_up_threshold"]))

        if "auto_scale_down_threshold" in config:
            self.auto_scale_down_threshold = max(5, min(self.auto_scale_up_threshold - 10, config["auto_scale_down_threshold"]))

        # Instant Reconciliation: Apply min/max checks immediately
        self._check_auto_scaling()
        
        self._add_log("SYSTEM", "Global settings updated")

    # ── Logging ──────────────────────────────────────────────────────────

    def _add_log(self, category: str, message: str):
        """Add an entry to the simulation log."""
        entry = {
            "timestamp": time.time(),
            "category": category,
            "message": message,
        }
        self.log_entries.append(entry)

    # ── State Serialization ──────────────────────────────────────────────

    def get_full_state(self) -> dict:
        """Get the complete simulation state for WebSocket broadcast."""
        return {
            "simulation": {
                "running": self.running,
                "traffic_mode": self.traffic_mode,
                "algorithm": self.current_algorithm_name,
                "algorithm_name": self.algorithm.name,
                "sticky_sessions": self.sticky_sessions_enabled,
                "auto_scaling": self.auto_scaling_enabled,
                "auto_scale_min": self.auto_scale_min,
                "auto_scale_max": self.auto_scale_max,
                "auto_scale_up_threshold": self.auto_scale_up_threshold,
                "auto_scale_down_threshold": self.auto_scale_down_threshold,
                "tick_interval_ms": int(self.tick_interval * 1000),
            },
            "servers": [s.to_dict() for s in self.servers],
            "metrics": self.metrics.to_dict(),
            "algorithm_stats": self.metrics.algorithm_stats,
            "raft": self.raft.to_dict(),
            "recent_requests": list(self.request_log)[-20:],
            "alerts": self.alert_manager.get_active(),
            "logs": list(self.log_entries)[-30:],
        }

    def get_status(self) -> dict:
        """Get current simulation status."""
        return {
            "running": self.running,
            "traffic_mode": self.traffic_mode,
            "algorithm": self.current_algorithm_name,
            "server_count": len(self.servers),
            "healthy_count": len(self.get_healthy_servers()),
            "sticky_sessions": self.sticky_sessions_enabled,
            "auto_scaling": self.auto_scaling_enabled,
        }
