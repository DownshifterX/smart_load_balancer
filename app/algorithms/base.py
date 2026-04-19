"""
app/algorithms/base.py
-----------------------
Abstract base class for load balancing algorithms.
All algorithms must implement the select_server method.
New algorithms can be added by subclassing and registering in __init__.py.
"""

from abc import ABC, abstractmethod


class LoadBalancerAlgorithm(ABC):
    """Base class for all load balancing algorithms."""

    name: str = "Base Algorithm"
    description: str = "Abstract base algorithm"

    @abstractmethod
    def select_server(self, servers: list, request=None):
        """
        Select the next server to handle a request.

        Args:
            servers: List of healthy ServerNode instances
            request: Optional SimulatedRequest for context (used by IP Hash)

        Returns:
            Selected ServerNode, or None if no servers available
        """
        pass

    def reset(self):
        """Reset any internal state. Override if needed."""
        pass
