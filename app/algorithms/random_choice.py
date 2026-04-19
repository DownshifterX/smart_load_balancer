"""
app/algorithms/random_choice.py
--------------------------------
Random: Picks a server at random with uniform probability.
Simple but can lead to uneven distribution with small sample sizes.
"""

import random
from app.algorithms.base import LoadBalancerAlgorithm


class RandomChoiceAlgorithm(LoadBalancerAlgorithm):
    name = "Random"
    description = "Selects a server at random with uniform probability. Simple and stateless, but may produce uneven distribution with small sample sizes."

    def select_server(self, servers: list, request=None):
        if not servers:
            return None
        return random.choice(servers)
