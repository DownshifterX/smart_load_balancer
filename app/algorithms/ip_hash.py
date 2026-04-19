"""
app/algorithms/ip_hash.py
--------------------------
IP Hash: Hashes the client's IP address to deterministically select
a server. Provides session persistence — same IP always hits the
same server (unless the server pool changes).
"""

import hashlib
from app.algorithms.base import LoadBalancerAlgorithm


class IPHashAlgorithm(LoadBalancerAlgorithm):
    name = "IP Hash"
    description = "Hashes client IP to deterministically route to the same server. Provides natural session persistence without explicit session tracking."

    def select_server(self, servers: list, request=None):
        if not servers:
            return None

        # Use source IP from request, or fallback to first server
        ip = "0.0.0.0"
        if request and hasattr(request, "source_ip"):
            ip = request.source_ip

        # Hash the IP and map to a server index
        hash_val = int(hashlib.md5(ip.encode()).hexdigest(), 16)
        index = hash_val % len(servers)
        return servers[index]
