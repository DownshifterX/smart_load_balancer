"""
app/core/raft.py
----------------
Simulates the Raft Consensus Protocol for a high-availability control plane.
This simulates 3 nodes communicating, managing leader elections, and heartbeats.
If the leader dies, elections occur and requests are dropped until a new leader emerges.
"""

import time
import random
from enum import Enum
from typing import Optional

class NodeState(Enum):
    FOLLOWER = "FOLLOWER"
    CANDIDATE = "CANDIDATE"
    LEADER = "LEADER"
    DEAD = "DEAD"

class RaftNode:
    """A simulated Raft control plane node."""
    
    def __init__(self, node_id: str):
        self.id = node_id
        self.state = NodeState.FOLLOWER
        self.current_term = 0
        self.voted_for: Optional[str] = None
        self.leader_id: Optional[str] = None
        
        # True if user killed this node via UI
        self.is_dead = False
        
        # Timing (simulated in seconds relative to time.time())
        self.last_heartbeat = time.time()
        self.election_timeout = random.uniform(0.15, 0.3)  # 150ms-300ms
        
        self.votes_received = 0

    def reset_election_timeout(self):
        self.election_timeout = random.uniform(0.15, 0.3)
        self.last_heartbeat = time.time()

    def kill(self):
        self.is_dead = True
        self.state = NodeState.DEAD
        
    def revive(self):
        self.is_dead = False
        self.state = NodeState.FOLLOWER
        self.current_term = 0
        self.voted_for = None
        self.leader_id = None
        self.reset_election_timeout()

    def to_dict(self):
        return {
            "id": self.id,
            "state": self.state.value,
            "term": self.current_term,
            "leader_id": self.leader_id,
        }

class RaftCluster:
    """Orchestrates the Raft nodes and simulates network communication."""
    
    def __init__(self):
        # Create 3-node cluster
        self.nodes = [
            RaftNode("CTRL-ALPHA"),
            RaftNode("CTRL-BETA"),
            RaftNode("CTRL-GAMMA")
        ]
        
    def get_leader(self) -> Optional[RaftNode]:
        """Returns the active leader node, if any."""
        for n in self.nodes:
            if n.state == NodeState.LEADER and not n.is_dead:
                return n
        return None

    def kill_node(self, node_id: str):
        for n in self.nodes:
            if n.id == node_id:
                n.kill()

    def revive_node(self, node_id: str):
        for n in self.nodes:
            if n.id == node_id:
                n.revive()

    def simulate_tick(self):
        """Simulate time advancing. Handle heartbeats and elections."""
        now = time.time()
        leader = self.get_leader()
        
        # 1. Leader sends heartbeats
        if leader:
            for n in self.nodes:
                if n.is_dead or n.id == leader.id:
                    continue
                # Follower receives heartbeat
                if n.current_term < leader.current_term:
                    n.current_term = leader.current_term
                n.state = NodeState.FOLLOWER
                n.leader_id = leader.id
                n.voted_for = None
                n.reset_election_timeout()
        
        # 2. Check for election timeouts
        for n in self.nodes:
            if n.is_dead or n.state == NodeState.LEADER:
                continue
                
            elapsed = now - n.last_heartbeat
            if elapsed > n.election_timeout:
                # Time to start an election!
                n.state = NodeState.CANDIDATE
                n.current_term += 1
                n.voted_for = n.id
                n.votes_received = 1
                n.leader_id = None
                n.reset_election_timeout()
                
                # Request votes from others
                for peer in self.nodes:
                    if peer.is_dead or peer.id == n.id:
                        continue
                        
                    # Peer logic to grant vote
                    if peer.current_term < n.current_term:
                        peer.current_term = n.current_term
                        peer.state = NodeState.FOLLOWER
                        peer.voted_for = n.id
                        peer.leader_id = None
                        n.votes_received += 1
                        
                # Check if we won
                if n.votes_received > (len(self.nodes) / 2):
                    n.state = NodeState.LEADER
                    n.leader_id = n.id
                    # Immediately send heartbeats
                    for peer in self.nodes:
                        if not peer.is_dead and peer.id != n.id:
                            peer.state = NodeState.FOLLOWER
                            peer.leader_id = n.id
                            peer.current_term = n.current_term
                            peer.reset_election_timeout()
                    break # Only one node can become leader per tick
                    
    def to_dict(self):
        return {
            "has_leader": self.get_leader() is not None,
            "leader_id": self.get_leader().id if self.get_leader() else None,
            "nodes": [n.to_dict() for n in self.nodes]
        }
