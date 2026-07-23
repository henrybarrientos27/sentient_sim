from __future__ import annotations

from collections import defaultdict, deque
from typing import Any

import numpy as np

from .agent import Agent
from .config import SimulationConfig


class World:
    """Local numerical physics with a hidden, randomized agent interface."""

    def __init__(self, config: SimulationConfig, initialize: bool = True) -> None:
        config.validate()
        self.config = config
        self.rng = np.random.default_rng(config.seed)
        self.tick = 0
        self.births = 0
        self.deaths = 0
        self.next_agent_identifier = 0
        self.signal_outcome_trace: deque[tuple[float, float]] = deque(maxlen=5000)

        self.sensor_permutation = self.rng.permutation(config.sensor_dim)
        self.sensor_signs = self.rng.choice(np.array([-1.0, 1.0]), size=config.sensor_dim)
        self.action_permutation = self.rng.permutation(config.actuator_dim)
        self.action_signs = self.rng.choice(np.array([-1.0, 1.0]), size=config.actuator_dim)

        self.resource = np.zeros((config.height, config.width), dtype=np.float64)
        self.trace = np.zeros((config.height, config.width), dtype=np.float64)
        self.agents: list[Agent] = []
        self._occupancy = np.zeros((config.height, config.width), dtype=np.int32)
        self._spatial_buckets: dict[tuple[int, int], list[Agent]] = {}
        if initialize:
            self.resource = self._make_resource_field()
            for _ in range(config.initial_agents):
                self.agents.append(self._new_root_agent())

    def _make_resource_field(self) -> np.ndarray:
        field = self.rng.random((self.config.height, self.config.width))
        for _ in range(5):
            field = (
                field
                + np.roll(field, 1, axis=0)
                + np.roll(field, -1, axis=0)
                + np.roll(field, 1, axis=1)
                + np.roll(field, -1, axis=1)
            ) / 5.0
        field -= field.min()
        field /= max(float(field.max()), 1e-9)
        return (0.25 + 0.75 * field) * self.config.resource_capacity

    def _new_root_agent(self) -> Agent:
        identifier = self.next_agent_identifier
        self.next_agent_identifier += 1
        position = np.array(
            [self.rng.uniform(0, self.config.width), self.rng.uniform(0, self.config.height)],
            dtype=np.float64,
        )
        return Agent(identifier, identifier, None, 0, position, self.config, self.rng)

    def _toroidal_delta(self, first: np.ndarray, second: np.ndarray) -> np.ndarray:
        delta = second - first
        spans = np.array([self.config.width, self.config.height], dtype=np.float64)
        return (delta + spans / 2.0) % spans - spans / 2.0

    def _distance(self, first: np.ndarray, second: np.ndarray) -> float:
        return float(np.linalg.norm(self._toroidal_delta(first, second)))

    def _build_spatial_cache(self) -> None:
        occupancy = np.zeros((self.config.height, self.config.width), dtype=np.int32)
        buckets: defaultdict[tuple[int, int], list[Agent]] = defaultdict(list)
        for agent in self.agents:
            cell = (
                int(np.floor(agent.position[0])) % self.config.width,
                int(np.floor(agent.position[1])) % self.config.height,
            )
            occupancy[cell[1], cell[0]] += 1
            buckets[cell].append(agent)
        self._occupancy = occupancy
        self._spatial_buckets = dict(buckets)

    def _nearby_agents(self, target: Agent) -> list[Agent]:
        radius = int(np.ceil(self.config.communication_radius))
        x = int(np.floor(target.position[0])) % self.config.width
        y = int(np.floor(target.position[1])) % self.config.height
        cells = {
            ((x + dx) % self.config.width, (y + dy) % self.config.height)
            for dy in range(-radius, radius + 1)
            for dx in range(-radius, radius + 1)
        }
        nearby: list[Agent] = []
        for cell in sorted(cells):
            nearby.extend(self._spatial_buckets.get(cell, ()))
        return nearby

    def _incoming_signal(self, target: Agent) -> np.ndarray:
        if not self.config.signaling_enabled:
            return np.zeros(self.config.signal_dim, dtype=np.float64)
        weighted = np.zeros(self.config.signal_dim, dtype=np.float64)
        total_weight = 0.0
        for source in self._nearby_agents(target):
            if source is target:
                continue
            distance = self._distance(target.position, source.position)
            if distance <= self.config.communication_radius:
                weight = 1.0 - distance / self.config.communication_radius
                weighted += weight * source.emitted_signal
                total_weight += weight
        return weighted / total_weight if total_weight > 0 else weighted

    def _raw_observation(self, agent: Agent, include_signals: bool = True) -> np.ndarray:
        x = int(np.floor(agent.position[0])) % self.config.width
        y = int(np.floor(agent.position[1])) % self.config.height
        resource_patch: list[float] = []
        occupancy_patch: list[float] = []
        trace_patch: list[float] = []
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                px, py = (x + dx) % self.config.width, (y + dy) % self.config.height
                resource_patch.append(self.resource[py, px] / self.config.resource_capacity)
                count = int(self._occupancy[py, px])
                if px == x and py == y:
                    count -= 1
                occupancy_patch.append(np.tanh(max(0, count) / 3.0))
                trace_patch.append(self.trace[py, px])

        internal = [
            np.tanh(agent.energy / self.config.initial_energy - 1.0),
            np.tanh(agent.pending_reward * 20.0),
            np.tanh(agent.age / 1000.0),
            agent.velocity[0] / max(self.config.max_speed, 1e-9),
            agent.velocity[1] / max(self.config.max_speed, 1e-9),
        ]
        incoming = self._incoming_signal(agent) if include_signals else np.zeros(self.config.signal_dim)
        raw = np.asarray(
            resource_patch + occupancy_patch + trace_patch + internal + incoming.tolist(),
            dtype=np.float64,
        )
        return np.clip(raw, -1.0, 1.0)

    def _encode_observation(self, raw: np.ndarray) -> np.ndarray:
        return raw[self.sensor_permutation] * self.sensor_signs

    def _decode_action(self, action: np.ndarray) -> np.ndarray:
        return action[self.action_permutation] * self.action_signs

    def step(self) -> None:
        if not self.agents:
            return
        self.tick += 1
        cfg = self.config
        self.resource += cfg.resource_regen * (cfg.resource_capacity - self.resource)
        np.clip(self.resource, 0.0, cfg.resource_capacity, out=self.resource)
        self.trace *= 1.0 - cfg.trace_decay
        self._build_spatial_cache()

        decisions: list[tuple[Agent, np.ndarray, np.ndarray, float]] = []
        for agent in list(self.agents):
            raw = self._raw_observation(agent, include_signals=True)
            incoming_norm = float(np.linalg.norm(raw[-cfg.signal_dim :])) if cfg.signal_dim else 0.0
            observation = self._encode_observation(raw)
            action = agent.decide(observation, agent.pending_reward, cfg, self.rng)

            if cfg.signaling_enabled:
                raw_without_signal = raw.copy()
                raw_without_signal[-cfg.signal_dim :] = 0.0
                no_signal = self._encode_observation(raw_without_signal)
                counterfactual = agent.counterfactual_mean(no_signal, cfg)
                actual_mean = agent._last_actor_mean
                agent.stats.signal_influence = float(
                    np.linalg.norm(actual_mean - counterfactual) / np.sqrt(cfg.actuator_dim)
                )
            else:
                agent.stats.signal_influence = 0.0
            decisions.append((agent, self._decode_action(action), action, incoming_norm))

        order = self.rng.permutation(len(decisions))
        for index in order:
            agent, physical, _anonymous_action, incoming_norm = decisions[int(index)]
            energy_before = agent.energy
            velocity = np.clip(physical[:2], -1.0, 1.0) * cfg.max_speed
            agent.velocity = velocity
            agent.position[0] = (agent.position[0] + velocity[0]) % cfg.width
            agent.position[1] = (agent.position[1] + velocity[1]) % cfg.height

            x = int(np.floor(agent.position[0])) % cfg.width
            y = int(np.floor(agent.position[1])) % cfg.height
            coupling = max(0.0, float(physical[2]))
            extracted = min(float(self.resource[y, x]), cfg.harvest_rate * coupling)
            self.resource[y, x] -= extracted

            trace_write = float(physical[3]) if cfg.environmental_memory_enabled else 0.0
            if cfg.environmental_memory_enabled:
                self.trace[y, x] = float(
                    np.clip(self.trace[y, x] + cfg.trace_write_rate * trace_write, -1.0, 1.0)
                )
            if cfg.signaling_enabled:
                agent.emitted_signal = np.clip(physical[4 : 4 + cfg.signal_dim], -1.0, 1.0)
            else:
                agent.emitted_signal.fill(0.0)
            cost = (
                cfg.basal_cost
                + cfg.movement_cost * float(np.linalg.norm(velocity))
                + cfg.signal_cost * float(np.linalg.norm(agent.emitted_signal))
                + cfg.trace_write_cost * abs(trace_write)
            )
            agent.energy = min(
                cfg.max_energy,
                agent.energy + cfg.harvest_efficiency * extracted - cost,
            )
            agent.pending_reward = agent.energy - energy_before
            agent.age += 1
            self.signal_outcome_trace.append((incoming_norm, agent.pending_reward))

        newborns: list[Agent] = []
        for parent in list(self.agents):
            if len(self.agents) + len(newborns) >= cfg.max_agents:
                break
            if (
                parent.energy >= cfg.reproduction_threshold
                and self.rng.random() < cfg.reproduction_probability
            ):
                transferred = parent.energy * cfg.offspring_fraction
                parent.energy -= transferred
                offset = self.rng.normal(0.0, 0.5, size=2)
                position = (parent.position + offset) % np.array([cfg.width, cfg.height])
                child = parent.offspring(self.next_agent_identifier, position, cfg, self.rng)
                self.next_agent_identifier += 1
                child.energy = transferred
                newborns.append(child)
        self.births += len(newborns)
        self.agents.extend(newborns)

        survivors = [agent for agent in self.agents if np.isfinite(agent.energy) and agent.energy > 0.0]
        self.deaths += len(self.agents) - len(survivors)
        self.agents = survivors

    def to_state(self) -> dict[str, Any]:
        return {
            "format_version": 2,
            "config": self.config.to_dict(),
            "tick": self.tick,
            "births": self.births,
            "deaths": self.deaths,
            "next_agent_identifier": self.next_agent_identifier,
            "rng_state": self.rng.bit_generator.state,
            "sensor_permutation": self.sensor_permutation.tolist(),
            "sensor_signs": self.sensor_signs.tolist(),
            "action_permutation": self.action_permutation.tolist(),
            "action_signs": self.action_signs.tolist(),
            "resource": self.resource.tolist(),
            "trace": self.trace.tolist(),
            "signal_outcome_trace": list(self.signal_outcome_trace),
            "agents": [agent.to_state() for agent in self.agents],
        }

    @classmethod
    def from_state(cls, state: dict[str, Any]) -> "World":
        if state.get("format_version") != 2:
            raise ValueError("unsupported checkpoint format")
        config = SimulationConfig.from_dict(state["config"])
        world = cls(config, initialize=False)
        world.tick = int(state["tick"])
        world.births = int(state["births"])
        world.deaths = int(state["deaths"])
        world.next_agent_identifier = int(state["next_agent_identifier"])
        world.rng.bit_generator.state = state["rng_state"]
        world.sensor_permutation = np.asarray(state["sensor_permutation"], dtype=np.int64)
        world.sensor_signs = np.asarray(state["sensor_signs"], dtype=np.float64)
        world.action_permutation = np.asarray(state["action_permutation"], dtype=np.int64)
        world.action_signs = np.asarray(state["action_signs"], dtype=np.float64)
        world.resource = np.asarray(state["resource"], dtype=np.float64)
        world.trace = np.asarray(state["trace"], dtype=np.float64)
        world.signal_outcome_trace = deque(
            (tuple(item) for item in state.get("signal_outcome_trace", [])), maxlen=5000
        )
        world.agents = [Agent.from_state(item, config) for item in state["agents"]]
        world._build_spatial_cache()
        return world
