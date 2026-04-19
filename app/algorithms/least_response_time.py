"""
app/algorithms/least_response_time.py
--------------------------------------
Least Response Time: Routes to the server with the lowest average
response time. Optimizes for speed. Falls back to least connections
when response times are equal.
"""

from app.algorithms.base import LoadBalancerAlgorithm


class LeastResponseTimeAlgorithm(LoadBalancerAlgorithm):
    name = "Least Response Time"
    description = "Routes requests to the server with the lowest average response time. Optimizes for speed and adapts to varying server performance."

    def select_server(self, servers: list, request=None):
        if not servers:
            return None
        # Sort by response time first, then by connections as tiebreaker
        return min(servers, key=lambda s: (s.avg_response_time, s.active_connections))
