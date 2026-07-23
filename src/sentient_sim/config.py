from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(slots=True)
class SimulationConfig:
    """Physics and learning parameters.

    Agents never receive these field names. Their interfaces are permuted and
    sign-flipped numerical channels, so the names only describe host physics.
    """

    seed: int = 7
    width: int = 32
    height: int = 32
    initial_agents: int = 48
    max_agents: int = 256
    hidden_dim: int = 24
    signal_dim: int = 6

    initial_energy: float = 1.0
    max_energy: float = 2.5
    basal_cost: float = 0.0025
    movement_cost: float = 0.0015
    signal_cost: float = 0.0005
    harvest_rate: float = 0.075
    harvest_efficiency: float = 0.42
    resource_regen: float = 0.012
    resource_capacity: float = 1.0
    max_speed: float = 0.75
    communication_radius: float = 4.0
    trace_decay: float = 0.002
    trace_write_rate: float = 0.06
    trace_write_cost: float = 0.0005

    reproduction_threshold: float = 1.65
    reproduction_probability: float = 0.035
    offspring_fraction: float = 0.42
    mutation_scale: float = 0.035

    prediction_learning_rate: float = 0.012
    representation_learning_rate: float = 0.0015
    actor_learning_rate: float = 0.008
    curiosity_scale: float = 0.03
    exploration_std: float = 0.16
    weight_clip: float = 3.0

    learning_enabled: bool = True
    recurrent_memory: bool = True
    signaling_enabled: bool = True
    environmental_memory_enabled: bool = True

    @property
    def sensor_dim(self) -> int:
        # Three anonymous 3x3 fields (resource, occupancy, writable trace), five
        # internal/kinetic scalars, and anonymous communication bandwidth.
        return 9 + 9 + 9 + 5 + self.signal_dim

    @property
    def actuator_dim(self) -> int:
        # Two kinetic channels, two field-coupling channels, and signal channels.
        return 4 + self.signal_dim

    def validate(self) -> None:
        integer_fields = {
            "width": self.width,
            "height": self.height,
            "initial_agents": self.initial_agents,
            "max_agents": self.max_agents,
            "hidden_dim": self.hidden_dim,
            "signal_dim": self.signal_dim,
        }
        for name, value in integer_fields.items():
            if value <= 0:
                raise ValueError(f"{name} must be positive")
        if self.initial_agents > self.max_agents:
            raise ValueError("initial_agents cannot exceed max_agents")
        if not 0.0 < self.offspring_fraction < 0.5:
            raise ValueError("offspring_fraction must be between 0 and 0.5")
        if self.resource_capacity <= 0 or self.initial_energy <= 0:
            raise ValueError("resource_capacity and initial_energy must be positive")
        if self.max_energy <= self.reproduction_threshold:
            raise ValueError("max_energy must exceed reproduction_threshold")
        if self.exploration_std <= 0:
            raise ValueError("exploration_std must be positive")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SimulationConfig":
        known = cls.__dataclass_fields__
        config = cls(**{key: value for key, value in data.items() if key in known})
        config.validate()
        return config
