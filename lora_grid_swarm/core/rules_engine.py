#!/usr/bin/env python3
"""
Conway Glider Rules Engine for LoRA Grid Swarm

Implements Conway's Game of Life rules adapted for LoRA-compressed swarm behavior.
Creates emergent patterns and traveling formations through simple threshold rules.

Adapts classical cellular automata to distributed swarm intelligence:
- Survival rules based on neighborhood activation density
- Birth rules for pattern emergence
- Death rules to prevent overgrowth and chaos
- Adapted to work with LoRA-compressed state representation
"""

from typing import Tuple, List, TYPE_CHECKING, Dict, Any
import time

if TYPE_CHECKING:
    from .floating_agent import FloatingAgent
    from .lora_grid import LoRACompressedGrid


class ConwayGliderRules:
    """
    Conway's Game of Life Rules Adapted for Swarm Emergence

    Classical Conway Rules:
    - Survival: Cell survives with 2-3 live neighbors
    - Death by underpopulation: Cell dies with < 2 neighbors
    - Death by overpopulation: Cell dies with > 3 neighbors
    - Birth: Dead cell becomes alive with exactly 3 neighbors

    Swarm Adaptation:
    - "Live" = actively propagating agent (abs(influence) > threshold)
    - "Neighbors" = agents in Von Neumann topology
    - "Death/Birth" = activation/inhibition through LoRA matrix influence
    - Emergent patterns travel through compressed state space
    """

    def __init__(self,
                 survival_min: int = 2,
                 survival_max: int = 3,
                 birth_count: int = 3,
                 overpopulation_threshold: int = 4):
        """
        Initialize Conway rule parameters

        Args:
            survival_min: Minimum neighbors for survival
            survival_max: Maximum neighbors for survival
            birth_count: Exact neighbors needed for birth
            overpopulation_threshold: Neighbors causing overpopulation death
        """
        self.survival_min = survival_min
        self.survival_max = survival_max
        self.birth_count = birth_count
        self.overpopulation_threshold = overpopulation_threshold

    def update_cell(self, agent: 'FloatingAgent', grid: 'LoRACompressedGrid') -> None:
        """
        Apply Conway rules to an agent within the LoRA grid context

        Args:
            agent: Agent to update
            grid: LoRACompressedGrid for neighborhood calculation
        """
        # Count active neighbors using von Neumann topology
        active_neighbors = self.count_active_neighbors(agent, grid)

        # Get current activation state from agent's perspective
        current_influence = agent.sense_influence()
        is_currently_active = abs(current_influence) > agent.activation_threshold

        # Determine next activation state based on Conway rules
        should_be_active = self._calculate_next_state(is_currently_active, active_neighbors)

        # Apply the state change through LoRA matrix manipulation
        self._apply_state_change(agent, should_be_active, grid)

        # Update agent's internal state to reflect the rule-based decision
        agent.is_active = should_be_active
        if should_be_active and not is_currently_active:
            agent.activation_count += 1

    def _calculate_next_state(self, is_currently_active: bool, active_neighbors: int) -> bool:
        """
        Calculate next activation state based on Conway rules

        Args:
            is_currently_active: Current activation state
            active_neighbors: Number of active neighbors

        Returns:
            bool: Next state (should be active)
        """
        if is_currently_active:
            # Survival rules
            if self.survival_min <= active_neighbors <= self.survival_max:
                return True  # Survives
            else:
                return False  # Dies (underpopulation or overpopulation)
        else:
            # Birth rule
            if active_neighbors == self.birth_count:
                return True  # Born
            else:
                return False  # Stays inactive

    def _apply_state_change(self, agent: 'FloatingAgent', should_be_active: bool,
                          grid: 'LoRACompressedGrid') -> None:
        """
        Apply the state change through LoRA matrix manipulation

        Args:
            agent: Agent being updated
            should_be_active: Desired activation state
            grid: LoRA grid for influence injection
        """
        current_influence = agent.sense_influence()
        current_active = abs(current_influence) > agent.activation_threshold

        if should_be_active and not current_active:
            # Birth/activation: Inject positive influence
            agent.inject_influence(strength=agent.propagation_strength)

        elif not should_be_active and current_active:
            # Death/inhibition: Inject negative influence to dampen
            agent.inject_influence(strength=-agent.propagation_strength * 0.5)

        # Note: For survival cases (should_be_active == current_active),
        # we allow natural LoRA decay and agent propagation to handle the pattern

    def count_active_neighbors(self, agent: 'FloatingAgent',
                             grid: 'LoRACompressedGrid') -> int:
        """
        Count active neighbors for Conway rule evaluation

        Uses von Neumann neighborhood (cardinal directions).
        An agent is "active" if its influence magnitude exceeds threshold.

        Args:
            agent: Agent to evaluate
            grid: LoRA grid for neighborhood influence sensing

        Returns:
            int: Number of active neighbors
        """
        neighbors = agent.get_neighbors()
        active_count = 0

        for nr, nc in neighbors:
            neighbor_influence = grid.get_influence(nr, nc)
            neighbor_active = abs(neighbor_influence) > agent.activation_threshold

            if neighbor_active:
                active_count += 1

        return active_count

    def calculate_neighbor_influence_strength(self, agent: 'FloatingAgent',
                                            grid: 'LoRACompressedGrid') -> float:
        """
        Calculate aggregate influence strength from active neighbors

        Provides finer-grained neighborhood influence beyond simple counting.

        Args:
            agent: Agent to evaluate
            grid: LoRA grid for influence sensing

        Returns:
            float: Sum of influence strengths from active neighbors
        """
        neighbors = agent.get_neighbors()
        total_influence = 0.0

        for nr, nc in neighbors:
            neighbor_influence = grid.get_influence(nr, nc)
            if abs(neighbor_influence) > agent.activation_threshold:
                total_influence += neighbor_influence

        return total_influence

    def detect_glider_patterns(self, agents: List['FloatingAgent'],
                             grid: 'LoRACompressedGrid') -> List[Dict[str, Any]]:
        """
        Detect emergent glider patterns in the swarm

        Looks for traveling, self-reproducing formations characteristic
        of Conway's Game of Life evolution.

        Args:
            agents: List of agents to analyze
            grid: LoRA grid for pattern detection

        Returns:
            List[Dict]: Detected glider patterns with metadata
        """
        # Create activation grid for pattern matching
        activation_grid = self._create_activation_grid(agents, grid)
        glider_patterns = []

        # Look for glider shapes (5-cell patterns) across the grid
        for row in range(grid.size - 2):  # Need 3x3 area minimum
            for col in range(grid.size - 2):
                if self._matches_glider_pattern(activation_grid, row, col):
                    glider_info = {
                        "position": (row, col),
                        "type": "glider_seed",
                        "agents_involved": self._get_agents_in_region(agents, row, col, 3, 3),
                        "confidence": self._calculate_pattern_confidence(activation_grid, row, col)
                    }
                    glider_patterns.append(glider_info)

        return glider_patterns

    def _create_activation_grid(self, agents: List['FloatingAgent'],
                               grid: 'LoRACompressedGrid') -> List[List[bool]]:
        """Create boolean activation grid from agent states"""
        activation = [[False for _ in range(grid.size)] for _ in range(grid.size)]

        for agent in agents:
            if agent.is_active:
                activation[agent.row][agent.col] = True

        return activation

    def _matches_glider_pattern(self, activation_grid: List[List[bool]],
                               start_row: int, start_col: int) -> bool:
        """
        Check if 3x3 region matches classic Game of Life glider pattern

        Glider pattern (rotates as it travels):
        . . #
        # . #
        . # .
        """
        pattern = [
            [False, False, True],
            [True, False, True],
            [False, True, False]
        ]

        for dr in range(3):
            for dc in range(3):
                expected = pattern[dr][dc]
                actual = activation_grid[start_row + dr][start_col + dc]
                if expected != actual:
                    return False
        return True

    def _get_agents_in_region(self, agents: List['FloatingAgent'],
                            start_row: int, start_col: int,
                            height: int, width: int) -> List['FloatingAgent']:
        """Get agents within a rectangular region"""
        region_agents = []
        for agent in agents:
            if (start_row <= agent.row < start_row + height and
                start_col <= agent.col < start_col + width):
                region_agents.append(agent)
        return region_agents

    def _calculate_pattern_confidence(self, activation_grid: List[List[bool]],
                                   start_row: int, start_col: int) -> float:
        """Calculate how well the pattern matches (for future extensions)"""
        # For now, return 1.0 for perfect matches
        # Could be extended to measure pattern stability, evolution likelihood, etc.
        return 1.0 if self._matches_glider_pattern(activation_grid, start_row, start_col) else 0.0


# ============================================================================
# Extended Pattern Classes
# ============================================================================

class PatternGenerator:
    """Generate classic Conway patterns for emergence studies"""

    @staticmethod
    def glider() -> List[Tuple[int, int]]:
        """Classic Game of Life glider pattern"""
        return [(0, 2), (1, 0), (1, 2), (2, 1), (2, 2)]

    @staticmethod
    def blinker() -> List[Tuple[int, int]]:
        """Oscillating pattern (period 2)"""
        return [(0, 1), (1, 1), (2, 1)]

    @staticmethod
    def beacon() -> List[Tuple[int, int]]:
        """Oscillating pattern (period 2)"""
        return [(0, 0), (0, 1), (1, 0), (2, 3), (3, 2), (3, 3)]

    @staticmethod
    def toad() -> List[Tuple[int, int]]:
        """Oscillating pattern (period 2)"""
        return [(0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2)]

    @staticmethod
    def block() -> List[Tuple[int, int]]:
        """Still life pattern (stable)"""
        return [(0, 0), (0, 1), (1, 0), (1, 1)]


class SwarmPatternAnalyzer:
    """
    Analyze emergent patterns in Conway rule-driven swarms

    Tracks pattern evolution, stability, and complexity metrics
    """

    def __init__(self, agents: List['FloatingAgent']):
        self.agents = agents
        self.pattern_history = []

    def snapshot_pattern_state(self) -> Dict[str, Any]:
        """Capture current pattern state for analysis"""
        state = {
            'timestamp': time.time(),
            'active_agents': sum(1 for a in self.agents if a.is_active),
            'activation_pattern': [(a.row, a.col) for a in self.agents if a.is_active],
            'cluster_centers': self._find_cluster_centers(),
            'pattern_density': self._calculate_pattern_density(),
            'spatial_dispersion': self._measure_spatial_dispersion()
        }

        self.pattern_history.append(state)
        return state

    def detect_pattern_evolution(self) -> Dict[str, Any]:
        """Analyze pattern changes over time"""
        if len(self.pattern_history) < 2:
            return {"evolution_type": "insufficient_data"}

        # Analyze pattern movement and transformation
        evolution = {
            "movement_vector": self._calculate_pattern_movement(),
            "pattern_stability": self._measure_pattern_stability(),
            "emergence_events": self._detect_emergence_events(),
            "dissipation_rate": self._measure_dissipation_rate()
        }

        # Classify evolution type
        if evolution["movement_vector"][0] > 0.5:  # Significant movement
            evolution["evolution_type"] = "traveling_pattern"
        elif evolution["pattern_stability"] > 0.8:
            evolution["evolution_type"] = "stable_configuration"
        elif evolution["emergence_events"] > 0:
            evolution["evolution_type"] = "chaotic_evolution"
        else:
            evolution["evolution_type"] = "dissipating_pattern"

        return evolution

    def _find_cluster_centers(self) -> List[Tuple[float, float]]:
        """Find centers of activation clusters"""
        if not any(a.is_active for a in self.agents):
            return []

        # Simple clustering: find dense regions
        clusters = []
        visited = set()

        for agent in self.agents:
            if agent.is_active and (agent.row, agent.col) not in visited:
                # Find connected component
                cluster = self._find_connected_component(agent, visited)
                if len(cluster) > 2:  # Only consider meaningful clusters
                    center = self._calculate_cluster_center(cluster)
                    clusters.append(center)

        return clusters

    def _find_connected_component(self, start_agent: 'FloatingAgent',
                                visited: set) -> List['FloatingAgent']:
        """Find connected component of active agents"""
        component = []
        queue = [start_agent]

        while queue:
            agent = queue.pop(0)
            if (agent.row, agent.col) in visited:
                continue

            visited.add((agent.row, agent.col))
            component.append(agent)

            # Check neighbors
            for nr, nc in agent.get_neighbors():
                neighbor = next((a for a in self.agents if a.row == nr and a.col == nc), None)
                if neighbor and neighbor.is_active:
                    queue.append(neighbor)

        return component

    def _calculate_cluster_center(self, cluster: List['FloatingAgent']) -> Tuple[float, float]:
        """Calculate center of mass for a cluster"""
        if not cluster:
            return (0.0, 0.0)

        sum_row = sum(a.row for a in cluster)
        sum_col = sum(a.col for a in cluster)
        n = len(cluster)

        return (sum_row / n, sum_col / n)

    def _calculate_pattern_density(self) -> float:
        """Calculate spatial density of activation"""
        active_count = sum(1 for a in self.agents if a.is_active)
        total_cells = len(self.agents)  # Assuming grid is fully populated
        return active_count / total_cells if total_cells > 0 else 0.0

    def _measure_spatial_dispersion(self) -> float:
        """Measure how spread out the activation patterns are"""
        active_positions = [(a.row, a.col) for a in self.agents if a.is_active]

        if len(active_positions) <= 1:
            return 0.0

        # Calculate average distance from center of mass
        center_row = sum(r for r, c in active_positions) / len(active_positions)
        center_col = sum(c for r, c in active_positions) / len(active_positions)

        total_distance = sum(abs(r - center_row) + abs(c - center_col)
                           for r, c in active_positions)

        return total_distance / len(active_positions)

    def _calculate_pattern_movement(self) -> Tuple[float, float]:
        """Calculate overall pattern movement vector"""
        if len(self.pattern_history) < 2:
            return (0.0, 0.0)

        # Simplified: compare center of mass movement
        recent = self.pattern_history[-2:]  # Last two snapshots

        if not recent[0]['activation_pattern'] or not recent[1]['activation_pattern']:
            return (0.0, 0.0)

        def center_of_mass(pattern):
            if not pattern:
                return (0.0, 0.0)
            return (sum(r for r, c in pattern) / len(pattern),
                   sum(c for r, c in pattern) / len(pattern))

        center1 = center_of_mass(recent[0]['activation_pattern'])
        center2 = center_of_mass(recent[1]['activation_pattern'])

        movement = (center2[0] - center1[0], center2[1] - center1[1])
        return movement

    def _measure_pattern_stability(self) -> float:
        """Measure how stable patterns are over time"""

        # TODO - implement the rest
        if len(self.pattern_history) < 3:
            return 0.5  # Neutral value for insufficient data

        # Placeholder - would implement proper stability analysis
        return 0.5

    def _detect_emergence_events(self) -> int:
        """Detect sudden pattern emergence events"""
        # Placeholder - would implement emergence detection
        return 0

    def _measure_dissipation_rate(self) -> float:
        """Measure how quickly patterns dissipate"""
        if len(self.pattern_history) < 2:
            return 0.0

        # Simple dissipation based on activation count trend
        recent_counts = [h['active_agents'] for h in self.pattern_history[-5:]]

        if len(recent_counts) < 2:
            return 0.0

        # Linear trend in activation counts
        # Negative trend indicates dissipation
        trend = recent_counts[-1] - recent_counts[0]
        return -trend / len(self.agents)  # Normalize to [0,1] range


# ============================================================================
# Conway Rules Implementation Notes
# ============================================================================

"""
Conway's Game of Life Adaptation for Swarm Emergence:

1. Original Conway Rules:
   - Any live cell with 2-3 neighbors survives
   - Any dead cell with exactly 3 neighbors becomes alive
   - All other cells die or stay dead

2. Swarm Adaptation:
   - "Live cell" = agent with |influence| > threshold
   - "Neighbors" = von Neumann neighbors in grid topology
   - "Death/Birth" = influence injection into LoRA Δ matrix
   - Emergent patterns travel through compressed state space

3. LoRA Integration:
   - Agent state represented in compressed matrix
   - Rule application modifies shared Δ matrix
   - Pattern emergence occurs through matrix reconstruction
   - Compression enables scalable pattern propagation

4. Key Extensions:
   - Influence strength weighting (not just binary alive/dead)
   - Decay integration with rule-based state changes
   - Pattern detection and evolution tracking
   - Multi-scale emergence analysis
"""

if __name__ == "__main__":
    # Test Conway rules basic functionality
    print("🧪 Testing Conway Glider Rules...")

    # Create test environment
    from .lora_grid import LoRACompressedGrid
    from .floating_agent import FloatingAgent

    grid = LoRACompressedGrid(size=4, rank=4)
    agent = FloatingAgent(2, 2, grid)  # Center agent
    rules = ConwayGliderRules()

    # Setup pretend neighborhood
    neighbors = agent.get_neighbors()
    print(f"✅ Agent at ({agent.row}, {agent.col}) has {len(neighbors)} neighbors")

    # Test rule counting
    active_neighbors = 3  # Simulate 3 active neighbors
    next_state = rules._calculate_next_state(agent.is_active, active_neighbors)
    print(f"✅ Conway rule: active={agent.is_active}, neighbors={active_neighbors} -> next={next_state}")

    # Test pattern generation
    glider = PatternGenerator.glider()
    print(f"✅ Glider pattern: {len(glider)} points - {glider}")

    print("🎯 Conway Glider Rules validation complete!")
