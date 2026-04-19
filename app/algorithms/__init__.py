"""
Load balancing algorithm registry.
Import all algorithms here for dynamic lookup.
"""

from app.algorithms.round_robin import RoundRobinAlgorithm
from app.algorithms.weighted_round_robin import WeightedRoundRobinAlgorithm
from app.algorithms.least_connections import LeastConnectionsAlgorithm
from app.algorithms.ip_hash import IPHashAlgorithm
from app.algorithms.random_choice import RandomChoiceAlgorithm
from app.algorithms.least_response_time import LeastResponseTimeAlgorithm

# Registry: name → class
ALGORITHM_REGISTRY = {
    "round_robin": RoundRobinAlgorithm,
    "weighted_round_robin": WeightedRoundRobinAlgorithm,
    "least_connections": LeastConnectionsAlgorithm,
    "ip_hash": IPHashAlgorithm,
    "random": RandomChoiceAlgorithm,
    "least_response_time": LeastResponseTimeAlgorithm,
}


def get_algorithm(name: str):
    """Get an algorithm instance by name."""
    cls = ALGORITHM_REGISTRY.get(name)
    if cls is None:
        raise ValueError(f"Unknown algorithm: {name}. Available: {list(ALGORITHM_REGISTRY.keys())}")
    return cls()


def list_algorithms() -> list[dict]:
    """Return metadata for all registered algorithms."""
    return [
        {
            "id": name,
            "name": cls.name,
            "description": cls.description,
        }
        for name, cls in ALGORITHM_REGISTRY.items()
    ]
