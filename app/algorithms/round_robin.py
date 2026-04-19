"""
app/algorithms/round_robin.py
------------------------------
Round Robin: Distributes requests evenly across servers in sequential
cyclic order. Simple, fair, but doesn't consider server load or speed.
"""

from app.algorithms.base import LoadBalancerAlgorithm


class RoundRobinAlgorithm(LoadBalancerAlgorithm):
    name = "Round Robin"
    description = "Distributes requests evenly in sequential cyclic order. Simple and fair, but ignores server load and capacity differences."

    def __init__(self):
        self._index = 0

    def select_server(self, servers: list, request=None):
        if not servers:
            return None
        self._index = self._index % len(servers)
        selected = servers[self._index]
        self._index += 1
        return selected

    def reset(self):
        self._index = 0
