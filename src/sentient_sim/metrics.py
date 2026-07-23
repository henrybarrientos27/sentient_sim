from __future__ import annotations

import math
from collections import Counter
from typing import Iterable

import numpy as np

from .world import World


def _mean(values: Iterable[float]) -> float:
    items = list(values)
    return float(np.mean(items)) if items else 0.0


def _lineage_entropy(world: World) -> float:
    counts = Counter(agent.root_identifier for agent in world.agents)
    total = sum(counts.values())
    if total <= 1 or len(counts) <= 1:
        return 0.0
    probabilities = [count / total for count in counts.values()]
    entropy = -sum(p * math.log(p) for p in probabilities)
    return float(entropy / math.log(len(counts)))


def _local_coordination(world: World) -> float:
    similarities: list[float] = []
    for index, first in enumerate(world.agents):
        norm_first = float(np.linalg.norm(first.velocity))
        if norm_first < 1e-9:
            continue
        for second in world.agents[index + 1 :]:
            if world._distance(first.position, second.position) > world.config.communication_radius:
                continue
            norm_second = float(np.linalg.norm(second.velocity))
            if norm_second < 1e-9:
                continue
            cosine = float(np.dot(first.velocity, second.velocity) / (norm_first * norm_second))
            similarities.append((cosine + 1.0) / 2.0)
    return _mean(similarities)


def _signal_outcome_correlation(world: World) -> float:
    if len(world.signal_outcome_trace) < 20:
        return 0.0
    data = np.asarray(world.signal_outcome_trace, dtype=np.float64)
    if float(np.std(data[:, 0])) < 1e-9 or float(np.std(data[:, 1])) < 1e-9:
        return 0.0
    value = float(np.corrcoef(data[:, 0], data[:, 1])[0, 1])
    return abs(value) if np.isfinite(value) else 0.0


def measure(world: World) -> dict[str, float | int]:
    """Descriptive behavior measures, none of which is a sentience score."""
    agents = world.agents
    actions = np.asarray(
        [agent.previous_action for agent in agents], dtype=np.float64
    ) if agents else np.empty((0, world.config.actuator_dim))
    behavioral_diversity = float(np.mean(np.std(actions, axis=0))) if len(actions) > 1 else 0.0
    return {
        "tick": world.tick,
        "population": len(agents),
        "births": world.births,
        "deaths": world.deaths,
        "max_generation": max((agent.generation for agent in agents), default=0),
        "mean_age": _mean(agent.age for agent in agents),
        "mean_energy": _mean(agent.energy for agent in agents),
        "resource_fraction": float(np.mean(world.resource) / world.config.resource_capacity),
        "environmental_trace_power": float(np.mean(np.abs(world.trace))),
        "environmental_trace_structure": float(np.std(world.trace)),
        "prediction_error": _mean(agent.stats.prediction_error for agent in agents),
        "learning_progress": _mean(agent.stats.learning_progress for agent in agents),
        "memory_dependence": _mean(agent.memory_dependence() for agent in agents),
        "signal_power": _mean(float(np.linalg.norm(agent.emitted_signal)) for agent in agents),
        "signal_influence": _mean(agent.stats.signal_influence for agent in agents),
        "signal_outcome_correlation": _signal_outcome_correlation(world),
        "local_coordination": _local_coordination(world),
        "behavioral_diversity": behavioral_diversity,
        "lineage_entropy": _lineage_entropy(world),
    }
