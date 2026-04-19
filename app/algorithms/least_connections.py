"""
app/algorithms/least_connections.py
------------------------------------
Least Connections: Routes each request to the server with the fewest
active connections. Adapts well to varying request durations.
"""

from app.algorithms.base import LoadBalancerAlgorithm


class LeastConnectionsAlgorithm(LoadBalancerAlgorithm):
    name = "Least Connections"
    description = "Routes requests to the server with the fewest active connections. Adapts well when requests have varying processing times."

    def select_server(self, servers: list, request=None):
        if not servers:
            return None
        return min(servers, key=lambda s: s.active_connections)
