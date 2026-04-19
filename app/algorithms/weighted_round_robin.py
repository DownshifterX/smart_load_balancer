"""
app/algorithms/weighted_round_robin.py
---------------------------------------
Weighted Round Robin: Like Round Robin but servers with higher weight
receive proportionally more requests. Useful when servers have different
capacities.
"""

from app.algorithms.base import LoadBalancerAlgorithm


class WeightedRoundRobinAlgorithm(LoadBalancerAlgorithm):
    name = "Weighted Round Robin"
    description = "Like Round Robin but distributes requests proportionally to server weights. Servers with higher weight handle more traffic."

    def __init__(self):
        self._index = 0
        self._current_weight = 0
        self._max_weight = 0
        self._gcd_weight = 0

    def _gcd(self, a, b):
        while b:
            a, b = b, a % b
        return a

    def select_server(self, servers: list, request=None):
        if not servers:
            return None

        if len(servers) == 1:
            return servers[0]

        weights = [s.weight for s in servers]
        max_w = max(weights)
        gcd_w = weights[0]
        for w in weights[1:]:
            gcd_w = self._gcd(gcd_w, w)

        # Smooth Weighted Round Robin
        n = len(servers)
        while True:
            self._index = (self._index + 1) % n
            if self._index == 0:
                self._current_weight -= gcd_w
                if self._current_weight <= 0:
                    self._current_weight = max_w
                    if self._current_weight == 0:
                        return servers[0]

            if servers[self._index].weight >= self._current_weight:
                return servers[self._index]

    def reset(self):
        self._index = 0
        self._current_weight = 0
