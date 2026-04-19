"""
app/core/alerts.py
-------------------
Alert manager that monitors simulation state and generates
warnings, recommendations, and critical alerts based on
server health, load distribution, and performance patterns.
"""

import time
from collections import deque
from app.utils.logger import get_logger

logger = get_logger("AlertManager")


class AlertSeverity:
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class AlertManager:
    """Monitors simulation state and generates actionable alerts."""

    def __init__(self, max_history: int = 100):
        self.active_alerts: list[dict] = []
        self.alert_history: deque = deque(maxlen=max_history)
        self._last_check = 0
        self._check_interval = 2  # seconds between alert evaluations

    def evaluate(self, servers: list, metrics: dict, current_algorithm: str):
        """
        Evaluate current state and generate/clear alerts.
        Called each simulation tick.
        """
        now = time.time()
        if now - self._last_check < self._check_interval:
            return
        self._last_check = now

        new_alerts = []

        # Check each server
        for srv in servers:
            s = srv if isinstance(srv, dict) else srv.to_dict()

            # Overloaded server
            if s.get("status") == "OVERLOADED":
                new_alerts.append(self._make_alert(
                    AlertSeverity.CRITICAL,
                    f"{s['name']} is OVERLOADED",
                    f"CPU: {s.get('cpu_usage', 0)}% | Connections: {s.get('active_connections', 0)}/{s.get('max_connections', 0)}",
                    "server_overload",
                    s["id"],
                ))

            # Server down
            if s.get("status") == "DOWN":
                new_alerts.append(self._make_alert(
                    AlertSeverity.CRITICAL,
                    f"{s['name']} is DOWN — traffic rerouted",
                    f"Region: {s.get('region', 'unknown')} | Auto-failover active",
                    "server_down",
                    s["id"],
                ))

            # Degraded server
            if s.get("status") == "DEGRADED":
                new_alerts.append(self._make_alert(
                    AlertSeverity.WARNING,
                    f"{s['name']} performance degraded",
                    f"CPU: {s.get('cpu_usage', 0)}% | Response time: {s.get('avg_response_time', 0)}ms",
                    "server_degraded",
                    s["id"],
                ))

            # High error rate on a server
            total = s.get("total_requests", 0)
            errors = s.get("error_count", 0)
            if total > 10 and errors / total > 0.1:
                new_alerts.append(self._make_alert(
                    AlertSeverity.WARNING,
                    f"{s['name']} high error rate: {round(errors/total*100, 1)}%",
                    f"Errors: {errors}/{total} requests",
                    "high_error_rate",
                    s["id"],
                ))

        # Check overall metrics
        success_rate = metrics.get("success_rate", 100)
        if success_rate < 90:
            new_alerts.append(self._make_alert(
                AlertSeverity.CRITICAL,
                f"Overall success rate critically low: {success_rate}%",
                "Multiple servers may be experiencing issues",
                "low_success_rate",
            ))
        elif success_rate < 95:
            new_alerts.append(self._make_alert(
                AlertSeverity.WARNING,
                f"Success rate below threshold: {success_rate}%",
                "Monitor server health closely",
                "success_rate_warning",
            ))

        # Check load distribution imbalance
        healthy_servers = [s for s in servers if (s if isinstance(s, dict) else s.to_dict()).get("status") != "DOWN"]
        if len(healthy_servers) >= 2:
            connections = []
            for srv in healthy_servers:
                s = srv if isinstance(srv, dict) else srv.to_dict()
                connections.append(s.get("active_connections", 0))
            if max(connections) > 0:
                imbalance = max(connections) / max(1, (sum(connections) / len(connections)))
                if imbalance > 3.0:
                    new_alerts.append(self._make_alert(
                        AlertSeverity.WARNING,
                        "Load distribution imbalance detected",
                        f"Max/avg ratio: {imbalance:.1f}x | Consider switching algorithm",
                        "load_imbalance",
                    ))

        # Generate algorithm recommendations
        rps = metrics.get("current_rps", 0)
        avg_rt = metrics.get("avg_response_time", 0)

        if rps > 20 and current_algorithm == "round_robin":
            has_varied_weights = len(set(
                (s if isinstance(s, dict) else s.to_dict()).get("weight", 1) for s in servers
            )) > 1
            if has_varied_weights:
                new_alerts.append(self._make_alert(
                    AlertSeverity.INFO,
                    "Recommendation: Switch to Weighted Round Robin",
                    "Servers have different weights — WRR would distribute load more efficiently",
                    "algo_recommendation",
                ))

        if avg_rt > 200 and current_algorithm not in ("least_response_time",):
            new_alerts.append(self._make_alert(
                AlertSeverity.INFO,
                "Recommendation: Consider Least Response Time",
                f"Avg response time is {avg_rt}ms — LRT algorithm optimizes for speed",
                "algo_recommendation",
            ))

        # Update active alerts
        self.active_alerts = new_alerts
        for alert in new_alerts:
            self.alert_history.append(alert)

    def _make_alert(self, severity: str, title: str, message: str, 
                    category: str, server_id: str = None) -> dict:
        """Create an alert dict."""
        return {
            "severity": severity,
            "title": title,
            "message": message,
            "category": category,
            "server_id": server_id,
            "timestamp": time.time(),
        }

    def get_active(self) -> list[dict]:
        """Return currently active alerts."""
        return self.active_alerts

    def get_history(self, limit: int = 50) -> list[dict]:
        """Return recent alert history."""
        return list(self.alert_history)[-limit:]

    def reset(self):
        """Clear all alerts."""
        self.active_alerts.clear()
        self.alert_history.clear()
