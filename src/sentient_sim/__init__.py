"""Minimal-prior open-ended agent simulation.

The package measures adaptive and emergent behavior. It does not provide a
test for consciousness, which currently has no accepted behavioral criterion.
"""

from .config import SimulationConfig
from .world import World

__all__ = ["SimulationConfig", "World"]
__version__ = "0.3.0"

