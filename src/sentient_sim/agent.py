from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any

import numpy as np

from .config import SimulationConfig


def _array(data: Any) -> np.ndarray:
    return np.asarray(data, dtype=np.float64)


@dataclass(slots=True)
class TransitionStats:
    prediction_error: float = 0.0
    learning_progress: float = 0.0
    reward: float = 0.0
    signal_influence: float = 0.0


class Agent:
    """A numerical predictive controller with persistent recurrent state.

    There are no emotion labels, words, symbols, roles, or scripted behaviors.
    The controller only sees anonymous numerical channels and improves a
    one-step world model and continuous policy from experience.
    """

    ARRAY_FIELDS = (
        "position",
        "velocity",
        "hidden",
        "previous_action",
        "emitted_signal",
        "w_input",
        "w_recurrent",
        "w_feedback",
        "hidden_bias",
        "w_actor",
        "actor_bias",
        "w_predictor",
        "predictor_bias",
    )

    def __init__(
        self,
        identifier: int,
        root_identifier: int,
        parent_identifier: int | None,
        generation: int,
        position: np.ndarray,
        config: SimulationConfig,
        rng: np.random.Generator,
    ) -> None:
        self.identifier = int(identifier)
        self.root_identifier = int(root_identifier)
        self.parent_identifier = parent_identifier
        self.generation = int(generation)
        self.position = _array(position)
        self.velocity = np.zeros(2, dtype=np.float64)
        self.energy = float(config.initial_energy)
        self.age = 0
        self.pending_reward = 0.0

        h, s, a = config.hidden_dim, config.sensor_dim, config.actuator_dim
        self.hidden = np.zeros(h, dtype=np.float64)
        self.previous_action = np.zeros(a, dtype=np.float64)
        self.emitted_signal = np.zeros(config.signal_dim, dtype=np.float64)

        self.w_input = rng.normal(0.0, 1.0 / np.sqrt(s), size=(h, s))
        recurrent = rng.normal(0.0, 1.0, size=(h, h))
        q, _ = np.linalg.qr(recurrent)
        self.w_recurrent = 0.82 * q
        self.w_feedback = rng.normal(0.0, 0.12 / np.sqrt(a), size=(h, a))
        self.hidden_bias = rng.normal(0.0, 0.015, size=h)
        self.w_actor = rng.normal(0.0, 0.18 / np.sqrt(h), size=(a, h))
        self.actor_bias = np.zeros(a, dtype=np.float64)
        self.w_predictor = rng.normal(0.0, 0.10 / np.sqrt(h + a), size=(s, h + a))
        self.predictor_bias = np.zeros(s, dtype=np.float64)

        # Evolvable scalar tendencies, intentionally unnamed inside the agent's
        # observation. They govern exploration and learning-progress reward.
        self.exploration_std = float(config.exploration_std)
        self.curiosity_scale = float(config.curiosity_scale)

        self.error_average = 0.5
        self.reward_average = 0.0
        self.stats = TransitionStats()
        self.reward_trace: deque[float] = deque(maxlen=128)
        self.action_trace: deque[list[float]] = deque(maxlen=128)

        self._has_transition = False
        self._last_observation = np.zeros(s, dtype=np.float64)
        self._last_hidden_before = np.zeros(h, dtype=np.float64)
        self._last_action_before = np.zeros(a, dtype=np.float64)
        self._last_hidden = np.zeros(h, dtype=np.float64)
        self._last_actor_mean = np.zeros(a, dtype=np.float64)
        self._last_actor_noise = np.zeros(a, dtype=np.float64)
        self._last_prediction = np.zeros(s, dtype=np.float64)

    def _learn_from_transition(
        self,
        observation: np.ndarray,
        external_reward: float,
        config: SimulationConfig,
    ) -> None:
        prediction_residual = observation - self._last_prediction
        squared_error = float(np.mean(np.square(prediction_residual)))
        old_average = self.error_average
        self.error_average = 0.985 * old_average + 0.015 * squared_error
        progress = float(np.clip(old_average - squared_error, -1.0, 1.0))
        reward = float(external_reward + self.curiosity_scale * progress)

        self.stats.prediction_error = squared_error
        self.stats.learning_progress = progress
        self.stats.reward = reward
        self.reward_trace.append(reward)

        if not config.learning_enabled:
            return

        # One-step predictive learning. The recurrent representation receives a
        # bounded local credit signal; no semantic target is supplied.
        pred_delta = np.clip(
            prediction_residual * (1.0 - np.square(self._last_prediction)),
            -1.0,
            1.0,
        )
        features = np.concatenate((self._last_hidden, self.previous_action))
        old_predictor = self.w_predictor.copy()
        self.w_predictor += config.prediction_learning_rate * np.outer(pred_delta, features)
        self.predictor_bias += config.prediction_learning_rate * pred_delta

        hidden_credit = old_predictor[:, : config.hidden_dim].T @ pred_delta
        hidden_credit *= 1.0 - np.square(self._last_hidden)
        hidden_credit = np.clip(hidden_credit, -0.5, 0.5)
        rep_rate = config.representation_learning_rate
        self.w_input += rep_rate * np.outer(hidden_credit, self._last_observation)
        self.w_recurrent += rep_rate * np.outer(hidden_credit, self._last_hidden_before)
        self.w_feedback += rep_rate * np.outer(hidden_credit, self._last_action_before)

        # Continuous REINFORCE update using only scalar experienced value.
        advantage = float(np.clip(reward - self.reward_average, -1.0, 1.0))
        self.reward_average = 0.98 * self.reward_average + 0.02 * reward
        score = self._last_actor_noise / max(self.exploration_std**2, 1e-6)
        score *= 1.0 - np.square(self._last_actor_mean)
        actor_delta = config.actor_learning_rate * advantage * np.clip(score, -3.0, 3.0)
        self.w_actor += np.outer(actor_delta, self._last_hidden)
        self.actor_bias += actor_delta

        clip = config.weight_clip
        for weights in (
            self.w_input,
            self.w_recurrent,
            self.w_feedback,
            self.w_actor,
            self.w_predictor,
        ):
            np.clip(weights, -clip, clip, out=weights)

    def decide(
        self,
        observation: np.ndarray,
        external_reward: float,
        config: SimulationConfig,
        rng: np.random.Generator,
    ) -> np.ndarray:
        observation = np.clip(_array(observation), -1.0, 1.0)
        if observation.shape != (config.sensor_dim,):
            raise ValueError(f"expected observation shape {(config.sensor_dim,)}, got {observation.shape}")

        if self._has_transition:
            self._learn_from_transition(observation, external_reward, config)

        hidden_before = self.hidden.copy() if config.recurrent_memory else np.zeros_like(self.hidden)
        net = (
            self.w_input @ observation
            + self.w_recurrent @ hidden_before
            + self.w_feedback @ self.previous_action
            + self.hidden_bias
        )
        new_hidden = np.tanh(net)
        actor_mean = np.tanh(self.w_actor @ new_hidden + self.actor_bias)
        actor_noise = rng.normal(0.0, self.exploration_std, size=config.actuator_dim)
        action = np.clip(actor_mean + actor_noise, -1.0, 1.0)
        prediction_features = np.concatenate((new_hidden, action))
        prediction = np.tanh(self.w_predictor @ prediction_features + self.predictor_bias)

        self.hidden = new_hidden
        self._last_observation = observation.copy()
        self._last_hidden_before = hidden_before
        self._last_action_before = self.previous_action.copy()
        self._last_hidden = new_hidden.copy()
        self._last_actor_mean = actor_mean
        self._last_actor_noise = action - actor_mean
        self._last_prediction = prediction
        self.previous_action = action.copy()
        self.action_trace.append(action.tolist())
        self._has_transition = True
        return action

    def counterfactual_mean(
        self,
        alternate_observation: np.ndarray,
        config: SimulationConfig,
    ) -> np.ndarray:
        """Policy output for an intervention without mutating agent state."""
        hidden_before = self._last_hidden_before if config.recurrent_memory else np.zeros_like(self.hidden)
        hidden = np.tanh(
            self.w_input @ alternate_observation
            + self.w_recurrent @ hidden_before
            + self.w_feedback @ self._last_action_before
            + self.hidden_bias
        )
        return np.tanh(self.w_actor @ hidden + self.actor_bias)

    def memory_dependence(self) -> float:
        if not self._has_transition:
            return 0.0
        without_history = np.tanh(
            self.w_input @ self._last_observation
            + self.w_feedback @ self._last_action_before
            + self.hidden_bias
        )
        mean_without = np.tanh(self.w_actor @ without_history + self.actor_bias)
        return float(np.linalg.norm(self._last_actor_mean - mean_without) / np.sqrt(mean_without.size))

    def offspring(
        self,
        identifier: int,
        position: np.ndarray,
        config: SimulationConfig,
        rng: np.random.Generator,
    ) -> "Agent":
        child = Agent(
            identifier=identifier,
            root_identifier=self.root_identifier,
            parent_identifier=self.identifier,
            generation=self.generation + 1,
            position=position,
            config=config,
            rng=rng,
        )
        scale = config.mutation_scale
        for field in (
            "w_input",
            "w_recurrent",
            "w_feedback",
            "hidden_bias",
            "w_actor",
            "actor_bias",
            "w_predictor",
            "predictor_bias",
        ):
            parent_value = getattr(self, field)
            mutation = rng.normal(0.0, scale, size=parent_value.shape)
            setattr(child, field, np.clip(parent_value + mutation, -config.weight_clip, config.weight_clip))
        child.exploration_std = float(np.clip(self.exploration_std * np.exp(rng.normal(0, scale)), 0.03, 0.5))
        child.curiosity_scale = float(np.clip(self.curiosity_scale + rng.normal(0, scale * 0.1), 0.0, 0.15))
        return child

    def to_state(self) -> dict[str, Any]:
        state: dict[str, Any] = {
            "identifier": self.identifier,
            "root_identifier": self.root_identifier,
            "parent_identifier": self.parent_identifier,
            "generation": self.generation,
            "energy": self.energy,
            "age": self.age,
            "pending_reward": self.pending_reward,
            "exploration_std": self.exploration_std,
            "curiosity_scale": self.curiosity_scale,
            "error_average": self.error_average,
            "reward_average": self.reward_average,
            "stats": {
                "prediction_error": self.stats.prediction_error,
                "learning_progress": self.stats.learning_progress,
                "reward": self.stats.reward,
                "signal_influence": self.stats.signal_influence,
            },
            "reward_trace": list(self.reward_trace),
            "action_trace": list(self.action_trace),
            "_has_transition": self._has_transition,
        }
        for field in self.ARRAY_FIELDS:
            state[field] = getattr(self, field).tolist()
        for field in (
            "_last_observation",
            "_last_hidden_before",
            "_last_action_before",
            "_last_hidden",
            "_last_actor_mean",
            "_last_actor_noise",
            "_last_prediction",
        ):
            state[field] = getattr(self, field).tolist()
        return state

    @classmethod
    def from_state(cls, state: dict[str, Any], config: SimulationConfig) -> "Agent":
        agent = cls.__new__(cls)
        for field in (
            "identifier",
            "root_identifier",
            "parent_identifier",
            "generation",
            "energy",
            "age",
            "pending_reward",
            "exploration_std",
            "curiosity_scale",
            "error_average",
            "reward_average",
            "_has_transition",
        ):
            setattr(agent, field, state[field])
        for field in cls.ARRAY_FIELDS:
            setattr(agent, field, _array(state[field]))
        for field in (
            "_last_observation",
            "_last_hidden_before",
            "_last_action_before",
            "_last_hidden",
            "_last_actor_mean",
            "_last_actor_noise",
            "_last_prediction",
        ):
            setattr(agent, field, _array(state[field]))
        agent.stats = TransitionStats(**state.get("stats", {}))
        agent.reward_trace = deque(state.get("reward_trace", []), maxlen=128)
        agent.action_trace = deque(state.get("action_trace", []), maxlen=128)
        return agent

