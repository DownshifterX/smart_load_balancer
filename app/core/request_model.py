"""
app/core/request_model.py
--------------------------
Simulated HTTP request model.
Each request gets a unique hex ID, random source IP, and tracks
which server handled it and the outcome.
"""

import time
import uuid
import random


class SimulatedRequest:
    """Represents a single simulated incoming HTTP request."""

    def __init__(self, source_ip: str = None):
        self.id = uuid.uuid4().hex[:12].upper()
        self.source_ip = source_ip or self._random_ip()
        
        # Generate random origin coordinates (avoiding extreme poles)
        self.client_lat = random.uniform(-60.0, 70.0)
        self.client_lng = random.uniform(-180.0, 180.0)
        
        self.timestamp = time.time()
        self.assigned_server_id: str | None = None
        self.assigned_server_name: str | None = None
        self.response_time: float | None = None
        self.success: bool | None = None
        self.retried: bool = False
        self.retry_count: int = 0
        self.completed: bool = False

    @staticmethod
    def _random_ip() -> str:
        """Generate a random IPv4 address."""
        return f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"

    def complete(self, server_id: str, server_name: str, response_time: float, success: bool):
        """Mark request as completed."""
        self.assigned_server_id = server_id
        self.assigned_server_name = server_name
        self.response_time = response_time
        self.success = success
        self.completed = True

    def to_dict(self) -> dict:
        """Serialize for API/WebSocket."""
        return {
            "id": self.id,
            "source_ip": self.source_ip,
            "client_lat": self.client_lat,
            "client_lng": self.client_lng,
            "timestamp": self.timestamp,
            "server_id": self.assigned_server_id,
            "server_name": self.assigned_server_name,
            "response_time": self.response_time,
            "success": self.success,
            "retried": self.retried,
            "retry_count": self.retry_count,
        }
