"""
app/core/metrics.py
--------------------
Metrics collector that aggregates simulation statistics.
Maintains rolling windows for time-series data and computes
percentiles, RPS, success rates, and per-server breakdowns.
"""

import time
from collections import deque
from app.utils.logger import get_logger

logger = get_logger("Metrics")


class MetricsCollector:
    """Aggregates and tracks simulation metrics over time."""

    def __init__(self, window_seconds: int = 60):
        self.window_seconds = window_seconds

        # Counters
        self.total_requests = 0
        self.total_success = 0
        self.total_failed = 0
        self.total_retries = 0

        # Rolling window for RPS calculation
        self._request_timestamps = deque()
        self._response_times = deque()

        # Time-series data (last N ticks)
        self.rps_history = deque(maxlen=120)
        self.response_time_history = deque(maxlen=120)
        self.active_connections_history = deque(maxlen=120)
        self.success_rate_history = deque(maxlen=120)

        # Per-algorithm performance tracking
        self.algorithm_stats: dict[str, dict] = {}

        # Start time
        self.start_time = time.time()

    def record_request(self, response_time: float, success: bool, retried: bool = False):
        """Record a completed request."""
        now = time.time()
        self.total_requests += 1

        if success:
            self.total_success += 1
        else:
            self.total_failed += 1

        if retried:
            self.total_retries += 1

        self._request_timestamps.append(now)
        self._response_times.append((now, response_time))

        # Prune old entries outside the window
        cutoff = now - self.window_seconds
        while self._request_timestamps and self._request_timestamps[0] < cutoff:
            self._request_timestamps.popleft()
        while self._response_times and self._response_times[0][0] < cutoff:
            self._response_times.popleft()

    def record_tick(self, active_connections: int):
        """Record per-tick aggregate metrics for time-series."""
        now = time.time()

        rps = self.current_rps
        avg_rt = self.avg_response_time
        success_rate = self.success_rate

        self.rps_history.append({"time": now, "value": rps})
        self.response_time_history.append({"time": now, "value": avg_rt})
        self.active_connections_history.append({"time": now, "value": active_connections})
        self.success_rate_history.append({"time": now, "value": success_rate})

    def record_algorithm_snapshot(self, algorithm_name: str, avg_response: float, 
                                  success_rate: float, distribution_score: float):
        """Store performance snapshot for algorithm comparison."""
        self.algorithm_stats[algorithm_name] = {
            "avg_response_time": round(avg_response, 2),
            "success_rate": round(success_rate, 2),
            "distribution_score": round(distribution_score, 2),
            "total_requests": self.total_requests,
            "timestamp": time.time(),
        }

    @property
    def current_rps(self) -> float:
        """Requests per second over the rolling window."""
        if not self._request_timestamps:
            return 0.0
        now = time.time()
        cutoff = now - min(5, self.window_seconds)  # Use 5s window for RPS
        count = sum(1 for t in self._request_timestamps if t >= cutoff)
        elapsed = min(5, now - self.start_time) if now - self.start_time < 5 else 5
        return round(count / max(0.1, elapsed), 1)

    @property
    def avg_response_time(self) -> float:
        """Average response time over the rolling window."""
        if not self._response_times:
            return 0.0
        times = [rt for _, rt in self._response_times]
        return round(sum(times) / len(times), 2)

    @property
    def success_rate(self) -> float:
        """Overall success rate as percentage."""
        if self.total_requests == 0:
            return 100.0
        return round((self.total_success / self.total_requests) * 100, 1)

    @property
    def p95_response_time(self) -> float:
        """95th percentile response time."""
        if not self._response_times:
            return 0.0
        times = sorted([rt for _, rt in self._response_times])
        idx = int(len(times) * 0.95)
        return round(times[min(idx, len(times) - 1)], 2)

    @property
    def p99_response_time(self) -> float:
        """99th percentile response time."""
        if not self._response_times:
            return 0.0
        times = sorted([rt for _, rt in self._response_times])
        idx = int(len(times) * 0.99)
        return round(times[min(idx, len(times) - 1)], 2)

    @property
    def uptime(self) -> float:
        """Seconds since metrics collection started."""
        return round(time.time() - self.start_time, 1)

    def reset(self):
        """Reset all metrics."""
        self.total_requests = 0
        self.total_success = 0
        self.total_failed = 0
        self.total_retries = 0
        self._request_timestamps.clear()
        self._response_times.clear()
        self.rps_history.clear()
        self.response_time_history.clear()
        self.active_connections_history.clear()
        self.success_rate_history.clear()
        self.algorithm_stats.clear()
        self.start_time = time.time()

    def to_dict(self) -> dict:
        """Current aggregate metrics snapshot."""
        return {
            "total_requests": self.total_requests,
            "total_success": self.total_success,
            "total_failed": self.total_failed,
            "total_retries": self.total_retries,
            "current_rps": self.current_rps,
            "avg_response_time": self.avg_response_time,
            "p95_response_time": self.p95_response_time,
            "p99_response_time": self.p99_response_time,
            "success_rate": self.success_rate,
            "uptime": self.uptime,
        }

    def history_to_dict(self) -> dict:
        """Time-series data for charts."""
        return {
            "rps": list(self.rps_history),
            "response_time": list(self.response_time_history),
            "active_connections": list(self.active_connections_history),
            "success_rate": list(self.success_rate_history),
        }
