"""
app/core/server_node.py
------------------------
Virtual server node model for the load balancing simulator.
Each ServerNode simulates a backend server with realistic metrics
that evolve over time based on load.
"""

import time
import random
import uuid
from dataclasses import dataclass, field
from enum import Enum


class ServerStatus(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    OVERLOADED = "OVERLOADED"
    DOWN = "DOWN"


# Geo-region mapping (Name -> (Lat, Lng))
REGION_COORDS = {
    "US-East": (39.04, -77.48),    # Ashburn, VA
    "US-West": (37.33, -121.88),   # San Jose, CA
    "EU-West": (53.34, -6.26),     # Dublin
    "EU-Central": (50.11, 8.68),   # Frankfurt
    "AP-South": (19.07, 72.87),    # Mumbai
    "AP-East": (22.31, 114.16)     # Hong Kong
}
REGIONS = list(REGION_COORDS.keys())


@dataclass
class ServerNode:
    """Represents a single simulated backend server."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    name: str = ""
    region: str = ""
    lat: float = 0.0
    lng: float = 0.0
    weight: int = 1
    max_connections: int = 100
    response_time_base: float = 50.0  # Base response time in ms
    failure_rate: float = 0.01  # Chance of request failure (0-1)

    # Runtime state
    healthy: bool = True
    enabled: bool = True
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    active_connections: int = 0
    total_requests: int = 0
    success_count: int = 0
    error_count: int = 0
    avg_response_time: float = 50.0
    _response_times: list = field(default_factory=list, repr=False)

    # Simulation overrides
    _force_failure: bool = False
    _force_latency: float = 0.0  # Extra latency in ms
    _force_overload: bool = False

    # Connection draining state
    _draining: bool = False

    def __post_init__(self):
        if not self.name:
            self.name = f"NODE-{self.id.upper()[:6]}"
        if not self.region:
            self.region = random.choice(REGIONS)
        if self.region in REGION_COORDS:
            base_lat, base_lng = REGION_COORDS[self.region]
            # Add small random jitter (+/- 1.5 degrees) to avoid exact overlap on globe
            self.lat = base_lat + random.uniform(-1.5, 1.5)
            self.lng = base_lng + random.uniform(-1.5, 1.5)

    def update_config(self, name: str, region: str, weight: int, max_connections: int):
        """Update server configuration dynamically."""
        if name: self.name = name
        if weight: self.weight = weight
        if max_connections: self.max_connections = max_connections
        if region and region in REGIONS:
            self.region = region
            base_lat, base_lng = REGION_COORDS[self.region]
            self.lat = base_lat + random.uniform(-1.5, 1.5)
            self.lng = base_lng + random.uniform(-1.5, 1.5)

    @property
    def status(self) -> ServerStatus:
        """Derive status from current metrics."""
        if not self.healthy or not self.enabled:
            return ServerStatus.DOWN
        if self._force_overload:
            return ServerStatus.OVERLOADED
        if self.cpu_usage > 90 or self.active_connections >= self.max_connections:
            return ServerStatus.OVERLOADED
        if self.cpu_usage > 70 or self.active_connections > self.max_connections * 0.75:
            return ServerStatus.DEGRADED
        return ServerStatus.HEALTHY

    @property
    def connection_utilization(self) -> float:
        """Percentage of max connections in use."""
        if self.max_connections == 0:
            return 100.0
        return min(100.0, (self.active_connections / self.max_connections) * 100)

    def can_accept_request(self) -> bool:
        """Check if this server can accept a new request."""
        if not self.healthy or not self.enabled:
            return False
        if self._draining:
            return False
        if self.active_connections >= self.max_connections:
            return False
        return True

    def process_request(self) -> dict:
        """
        Simulate processing a single request.
        Returns a result dict with response time and success/failure.
        """
        self.total_requests += 1
        self.active_connections += 1

        # Calculate response time
        base = self.response_time_base
        # Add load-based latency (more connections = slower)
        load_factor = self.active_connections / max(1, self.max_connections)
        load_latency = base * load_factor * 2
        # Add randomness
        jitter = random.uniform(-base * 0.2, base * 0.3)
        # Add forced latency
        extra = self._force_latency

        response_time = max(1.0, base + load_latency + jitter + extra)

        # Determine success/failure
        effective_failure_rate = self.failure_rate
        if self._force_failure:
            effective_failure_rate = 1.0
        if self._force_overload and load_factor > 0.8:
            effective_failure_rate = min(1.0, effective_failure_rate + 0.3)

        success = random.random() > effective_failure_rate

        if success:
            self.success_count += 1
        else:
            self.error_count += 1

        # Track response time
        self._response_times.append(response_time)
        if len(self._response_times) > 100:
            self._response_times = self._response_times[-100:]
        self.avg_response_time = sum(self._response_times) / len(self._response_times)

        return {
            "success": success,
            "response_time": round(response_time, 2),
            "server_id": self.id,
            "server_name": self.name,
        }

    def release_connection(self):
        """Release a connection after request is complete."""
        self.active_connections = max(0, self.active_connections - 1)

    def simulate_tick(self):
        """
        Called each simulation tick to evolve server state.
        Naturally decreases connections and fluctuates CPU/memory.
        """
        # Naturally release some connections over time
        if self.active_connections > 0:
            released = random.randint(0, max(1, self.active_connections // 3))
            self.active_connections = max(0, self.active_connections - released)

        # CPU correlates with active connections + noise
        target_cpu = (self.active_connections / max(1, self.max_connections)) * 85
        if self._force_overload:
            target_cpu = random.uniform(85, 99)
        noise = random.uniform(-5, 5)
        self.cpu_usage = max(0, min(100, target_cpu + noise))

        # Memory is more stable, drifts slowly
        target_mem = 20 + (self.active_connections / max(1, self.max_connections)) * 50
        mem_noise = random.uniform(-2, 2)
        self.memory_usage = max(0, min(100, (self.memory_usage * 0.8) + (target_mem + mem_noise) * 0.2))

        # If forced failure, mark unhealthy
        if self._force_failure:
            self.healthy = False

    def simulate_failure(self):
        """Simulate a server crash."""
        self._force_failure = True
        self.healthy = False
        self.active_connections = 0
        self.cpu_usage = 0
        self.memory_usage = 0

    def simulate_latency(self, extra_ms: float = 500.0):
        """Inject artificial latency."""
        self._force_latency = extra_ms

    def simulate_overload(self):
        """Put server in overload state."""
        self._force_overload = True

    def recover(self):
        """Recover from all simulated issues."""
        self._force_failure = False
        self._force_latency = 0.0
        self._force_overload = False
        self.healthy = True

    def reset_metrics(self):
        """Reset all counters."""
        self.total_requests = 0
        self.success_count = 0
        self.error_count = 0
        self.active_connections = 0
        self.cpu_usage = 0
        self.memory_usage = 0
        self.avg_response_time = self.response_time_base
        self._response_times.clear()

    def to_dict(self) -> dict:
        """Serialize to dictionary for API/WebSocket responses."""
        return {
            "id": self.id,
            "name": self.name,
            "region": self.region,
            "lat": self.lat,
            "lng": self.lng,
            "weight": self.weight,
            "status": self.status.value,
            "healthy": self.healthy,
            "enabled": self.enabled,
            "cpu_usage": round(self.cpu_usage, 1),
            "memory_usage": round(self.memory_usage, 1),
            "active_connections": self.active_connections,
            "max_connections": self.max_connections,
            "connection_utilization": round(self.connection_utilization, 1),
            "total_requests": self.total_requests,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "avg_response_time": round(self.avg_response_time, 2),
            "response_time_base": self.response_time_base,
            "failure_rate": self.failure_rate,
        }
