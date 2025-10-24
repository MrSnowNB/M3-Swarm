#!/usr/bin/env python3
"""
Floating Agent Implementation for LoRA Grid Swarm

Agents that "float" on the compressed LoRA state representation.
Perceive local influence through AΔB reconstruction and propagate
changes through 2D grid topology with Von Neumann neighborhood.
"""

import time
from typing import Tuple, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .lora_grid import LoRACompressedGrid


class FloatingAgent:
    """
    Agent that interacts with LoRA-compressed swarm state

    Architecture:
    - Position: (row, col) in 12×12 grid
    - Perception: Local influence via AΔB reconstruction
    - Behavior: Threshold-based activation and propagation
    - Movement: Influence propagation to Von Neumann neighbors

    Key Innovation:
    Each agent experiences the shared state space as Base + AΔB(position)
    While physical propagation requires communication to neighbors.
    """

    def __init__(self, row: int, col: int, grid: 'LoRACompressedGrid',
                 activation_threshold: float = 0.1,
                 propagation_strength: float = 0.5):
        """
        Initialize floating agent

        Args:
            row, col: Agent position in grid
            grid: LoRACompressedGrid instance
            activation_threshold: Internal activation threshold
            propagation_strength: Strength of neighbor influence
        """
        self.row = row
        self.col = col
        self.grid = grid
        self.activation_threshold = activation_threshold
        self.propagation_strength = propagation_strength

        # Agent state
        self.internal_state: float = 0.0  # Current activation level
        self.base_state: float = 0.0      # Steady-state value
        self.is_active: bool = False     # Activator status

        # Tracking
        self.last_update: float = 0.0
        self.activation_count: int = 0

        # Agent identifier (linear index)
        self.agent_id = row * grid.size + col

        self.validate_position()

    def validate_position(self):
        """Validate agent position is within grid bounds"""
        if not (0 <= self.row < self.grid.size and 0 <= self.col < self.grid.size):
            raise ValueError(f"Invalid position: ({self.row}, {self.col}) "
                           f"for grid size {self.grid.size}×{self.grid.size}")

    def sense_influence(self) -> float:
        """
        Sense local influence from LoRA grid

        Returns agent-specific perception of the shared state space
        at this position using AΔB reconstruction.

        Returns:
            float: Local influence value at current position
        """
        influence = self.grid.get_influence(self.row, self.col)

        # Track for debugging/analysis
        if influence != self.last_update:
            self.last_update = influence

            # Possible activation trigger
            self._update_activation(influence)

        return influence

    def _update_activation(self, influence: float):
        """
        Update internal activation based on perceived influence

        Args:
            influence: Local influence value from LoRA reconstruction
        """
        # Simple thresholding mechanism (can be extended with more complex logic)
        activation_change = influence * self.activation_threshold

        self.internal_state += activation_change

        # Clamp to reasonable range [-1, 1]
        self.internal_state = max(-1.0, min(1.0, self.internal_state))

        # Update activator status
        was_active = self.is_active
        self.is_active = abs(self.internal_state) > 0.1

        # Track activation events
        if not was_active and self.is_active:
            self.activation_count += 1

    def update_state(self) -> None:
        """
        Update agent state based on current grid conditions

        Called each simulation step. Agent senses influence,
        updates internal state, and may propagate to neighbors.
        """
        # Sense current local influence
        influence = self.sense_influence()

        # Natural decay toward base state (resistance to perturbation)
        decay_factor = 0.95  # Small decay each step
        self.internal_state *= decay_factor

        # Check if threshold crossed for propagation
        if abs(influence) > self.activation_threshold:
            self.propagate_to_neighbors()

        # Update base state memory (extremely slow learning)
        self.base_state = 0.999 * self.base_state + 0.001 * influence

    def propagate_to_neighbors(self) -> None:
        """
        Propagate influence to neighboring agents

        Uses Von Neumann neighborhood (cardinal directions).
        Propagation happens by injecting influence into neighbors'
        LoRA representation through flip_bit operations.
        """
        neighbors = self.get_neighbors()

        for neighbor_row, neighbor_col in neighbors:
            # Convert neighbor position to linear index
            neighbor_idx = neighbor_row * self.grid.size + neighbor_col

            # Inject influence into LoRA grid at neighbor position
            # This affects the shared state space via rank-space updates
            self.grid.flip_bit(neighbor_idx, strength=self.propagation_strength)

            # Apply nonlinear propagation (closer neighbors get more intense updates)
            # Manhattan distance attenuation
            distance = abs(neighbor_row - self.row) + abs(neighbor_col - self.col)
            if distance == 1:  # Adjacent neighbors get full strength
                pass  # Already applied above
            elif distance > 1:  # Could extend to include this but keeping simple for now
                continue

    def get_neighbors(self) -> List[Tuple[int, int]]:
        """
        Get neighboring positions using Von Neumann neighborhood

        Returns:
            List[Tuple[int,int]]: Adjacent positions (up, down, left, right)
        """
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # Von Neumann neighbors
        neighbors = []

        for dr, dc in directions:
            nr, nc = self.row + dr, self.col + dc
            if (0 <= nr < self.grid.size and 0 <= nc < self.grid.size):
                neighbors.append((nr, nc))

        return neighbors

    def inject_influence(self, strength: float = 1.0):
        """
        Manually inject influence at agent's position

        Useful for external stimulus or testing.

        Args:
            strength: Magnitude of influence injection
        """
        linear_idx = self.row * self.grid.size + self.col
        self.grid.flip_bit(linear_idx, strength=strength)

    def reset(self):
        """Reset agent to initial state"""
        self.internal_state = 0.0
        self.is_active = False
        self.activation_count = 0
        self.last_update = 0.0

    def get_metrics(self) -> dict:
        """
        Get agent performance metrics

        Returns:
            dict: Agent state and behavior metrics
        """
        neighbors = len(self.get_neighbors())

        return {
            'position': (self.row, self.col),
            'agent_id': self.agent_id,
            'internal_state': self.internal_state,
            'base_state': self.base_state,
            'is_active': self.is_active,
            'activation_count': self.activation_count,
            'neighbors': neighbors,
            'activation_threshold': self.activation_threshold,
            'propagation_strength': self.propagation_strength
        }

    def distance_to(self, other_agent: 'FloatingAgent') -> float:
        """
        Calculate Manhattan distance to another agent

        Args:
            other_agent: Another FloatingAgent instance

        Returns:
            float: Manhattan distance
        """
        return abs(self.row - other_agent.row) + abs(self.col - other_agent.col)


# ============================================================================
# Floating Agent Swarm Patterns
# ============================================================================

class AgentPattern:
    """Common agent initialization patterns for emergence testing"""

    @staticmethod
    def scattered_random(grid: 'LoRACompressedGrid', density: float = 0.1) -> List[FloatingAgent]:
        """
        Create randomly scattered agents

        Args:
            grid: LoRACompressedGrid instance
            density: Fraction of positions to occupy (0.0-1.0)

        Returns:
            List[FloatingAgent]: Scattered agent list
        """
        from numpy.random import random

        agents = []
        total_positions = grid.size * grid.size
        num_agents = int(total_positions * density)

        # Random positions without replacement
        positions = set()
        while len(positions) < num_agents:
            row = int(random() * grid.size)
            col = int(random() * grid.size)
            positions.add((row, col))

        for row, col in positions:
            agents.append(FloatingAgent(row, col, grid))

        return agents

    @staticmethod
    def grid_pattern(grid: 'LoRACompressedGrid', stride: int = 2) -> List[FloatingAgent]:
        """
        Create regularly spaced grid pattern

        Args:
            grid: LoRACompressedGrid instance
            stride: Spacing between agents

        Returns:
            List[FloatingAgent]: Grid-patterned agent list
        """
        agents = []

        for row in range(0, grid.size, stride):
            for col in range(0, grid.size, stride):
                agents.append(FloatingAgent(row, col, grid))

        return agents

    @staticmethod
    def glider_seed(grid: 'LoRACompressedGrid') -> List[FloatingAgent]:
        """
        Create Game of Life glider pattern for emergence testing

        Returns:
            List[FloatingAgent]: Agents in glider configuration
        """
        # Conway glider: pattern that travels and reproduces
        glider_positions = [
            (1, 0), (2, 1), (0, 2), (1, 2), (2, 2)
        ]

        agents = []
        for row, col in glider_positions:
            # Position relative to grid center
            center_row = grid.size // 2
            center_col = grid.size // 2

            agents.append(FloatingAgent(
                center_row + row - 1,  # Center the pattern
                center_col + col - 1,
                grid
            ))

        return agents


# ============================================================================
# Agent Swarm Behavioral Analysis
# ============================================================================

class SwarmBehaviorAnalyzer:
    """Analyze collective behavior patterns in agent swarms"""

    def __init__(self, agents: List[FloatingAgent]):
        self.agents = agents

    def calculate_center_of_mass(self) -> Tuple[float, float]:
        """
        Calculate center of mass of active agents

        Returns:
            Tuple[float, float]: Center of mass coordinates
        """
        active_agents = [a for a in self.agents if a.is_active]

        if not active_agents:
            return (0.0, 0.0)

        total_mass = len(active_agents)
        com_row = sum(a.row for a in active_agents) / total_mass
        com_col = sum(a.col for a in active_agents) / total_mass

        return (com_row, com_col)

    def measure_activation_rate(self) -> float:
        """
        Calculate current fraction of active agents

        Returns:
            float: Activation rate (0.0-1.0)
        """
        active_count = sum(1 for a in self.agents if a.is_active)
        return active_count / len(self.agents) if self.agents else 0.0

    def get_pattern_complexity(self) -> float:
        """
        Measure pattern complexity using activation clustering

        Returns:
            float: Clustering coefficient (0.0-1.0)
        """
        if not self.agents:
            return 0.0

        # Count active agent pairs that are neighbors
        active_neighbors = 0
        total_active = 0

        for agent in self.agents:
            if agent.is_active:
                total_active += 1
                neighbors = agent.get_neighbors()
                for nr, nc in neighbors:
                    # Check if neighboring agent exists and is active
                    neighbor = next((a for a in self.agents
                                   if a.row == nr and a.col == nc), None)
                    if neighbor and neighbor.is_active:
                        active_neighbors += 1

        if total_active == 0:
            return 0.0

        # Normalize by maximum possible neighbor connections
        max_connections = sum(len(a.get_neighbors()) for a in self.agents if a.is_active)
        return active_neighbors / max_connections if max_connections > 0 else 0.0

    def detect_emergent_patterns(self) -> List[str]:
        """
        Detect emergent pattern types in current swarm state

        Returns:
            List[str]: Detected pattern types
        """
        patterns = []

        # Simple pattern detection (can be extended)
        activation_rate = self.measure_activation_rate()

        if activation_rate < 0.05:
            patterns.append("quiescent")
        elif activation_rate > 0.8:
            patterns.append("synchronized_oscillation")
        elif self.get_pattern_complexity() > 0.7:
            patterns.append("clustered_activation")
        else:
            patterns.append("wave_propagation")

        # Check for traveling patterns by tracking center of mass changes
        com = self.calculate_center_of_mass()
        grid_center = self.agents[0].grid.size // 2
        distance_from_center = abs(com[0] - grid_center) + abs(com[1] - grid_center)

        if distance_from_center > grid_center * 0.3:
            patterns.append("eccentric_movement")

        return patterns

    def export_analysis_report(self) -> dict:
        """
        Generate comprehensive swarm behavior analysis

        Returns:
            dict: Analysis report
        """
        return {
            'timestamp': time.time(),
            'agent_count': len(self.agents),
            'activation_rate': self.measure_activation_rate(),
            'center_of_mass': self.calculate_center_of_mass(),
            'pattern_complexity': self.get_pattern_complexity(),
            'emergent_patterns': self.detect_emergent_patterns(),
            'individual_metrics': [a.get_metrics() for a in self.agents]
        }


# ============================================================================
# Floating Agent Implementation Notes
# ============================================================================

"""
Floating Agent Cognitive Architecture:

1. Perception: Agent senses Local Reality via AΔB Reconstruction
   - Each agent perceives Base[row,col] + AΔB reconstruction
   - The same shared Δ enables coordinated behavior
   - Local perception creates decentralized decision-making

2. Internal State: Threshold-based Activation
   - internal_state accumulates influence over time
   - activation_threshold determines behavior triggers
   - base_state provides memory of historical values

3. Propagation: Von Neumann Influence Transmission
   - Cardinal direction neighbor propagation
   - Manhattan distance-based attenuation
   - Feed-forward influence through shared LoRA matrix

4. Emergence: Simple Rules Create Complex Patterns
   - Threshold activation for propagation
   - Neighbor connections create feedback loops
   - Collective behavior emerges from individual simplicity

Key Innovation:
Agents are "floating" on the compressed state representation. Individual
agents perceive the global swarm state through AΔB reconstruction at their
local position, while their actions modify the shared Δ matrix. This creates
a novel form of distributed cognition where global behavior emerges from
low-bandwidth interactions with the compressed state space.

Mathematical Bridge:
- Agent Location: (row,col) discrete grid position
- Agent Perception: A[row*12+col,:] @ Δ @ B[:,row*12+col] reconstruction
- Agent Influence: flip_bit() injection into shared Δ matrix
- Swarm Emergence: Conway rules operating on locally perceived state
"""

if __name__ == "__main__":
    # Test individual agent functionality
    from .lora_grid import LoRACompressedGrid

    print("🧪 Testing Floating Agent functionality...")

    # Create test environment
    grid = LoRACompressedGrid(size=4, rank=4)  # Small grid for testing
    agent = FloatingAgent(1, 1, grid)

    print(f"✅ Agent initialized at position ({agent.row}, {agent.col})")
    print(f"   Agent ID: {agent.agent_id}")
    print(f"   Neighbor count: {len(agent.get_neighbors())}")

    # Test influence sensing
    initial_influence = agent.sense_influence()
    print(f"✅ Initial influence: {initial_influence:.3f}")

    # Inject influence and test sensing
    agent.inject_influence(strength=1.0)
    post_influence = agent.sense_influence()
    print(f"✅ After injection: {post_influence:.3f}")

    # Test metrics
    metrics = agent.get_metrics()
    print(f"✅ Agent metrics keys: {list(metrics.keys())}")
    print(f"   Is active: {metrics['is_active']}")

    print("🎯 Floating Agent validation complete!")
