from __future__ import annotations

import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import numpy as np

from sentient_sim.config import SimulationConfig
from sentient_sim.experiment import run_ablation_experiment
from sentient_sim.metrics import measure
from sentient_sim.runner import load_checkpoint, save_checkpoint
from sentient_sim.world import World


def small_config(**overrides):
    values = {
        "seed": 19,
        "width": 10,
        "height": 10,
        "initial_agents": 8,
        "max_agents": 24,
        "hidden_dim": 8,
        "signal_dim": 3,
    }
    values.update(overrides)
    return SimulationConfig(**values)


class SimulationTests(unittest.TestCase):
    def test_randomized_interfaces_are_valid_permutations(self):
        world = World(small_config())
        self.assertEqual(sorted(world.sensor_permutation.tolist()), list(range(world.config.sensor_dim)))
        self.assertEqual(sorted(world.action_permutation.tolist()), list(range(world.config.actuator_dim)))
        self.assertTrue(set(world.sensor_signs.tolist()) <= {-1.0, 1.0})
        self.assertTrue(set(world.action_signs.tolist()) <= {-1.0, 1.0})

    def test_seeded_runs_are_deterministic(self):
        first, second = World(small_config()), World(small_config())
        for _ in range(40):
            first.step()
            second.step()
        np.testing.assert_allclose(first.resource, second.resource, rtol=0, atol=0)
        self.assertEqual(measure(first), measure(second))
        for left, right in zip(first.agents, second.agents):
            np.testing.assert_allclose(left.position, right.position, rtol=0, atol=0)
            np.testing.assert_allclose(left.w_predictor, right.w_predictor, rtol=0, atol=0)

    def test_learning_updates_weights_and_frozen_control_does_not(self):
        adaptive = World(small_config(learning_enabled=True))
        frozen = World(small_config(learning_enabled=False))
        adaptive_before = adaptive.agents[0].w_predictor.copy()
        frozen_before = frozen.agents[0].w_predictor.copy()
        for _ in range(5):
            adaptive.step()
            frozen.step()
        self.assertGreater(float(np.max(np.abs(adaptive.agents[0].w_predictor - adaptive_before))), 0.0)
        np.testing.assert_allclose(frozen.agents[0].w_predictor, frozen_before, rtol=0, atol=0)

    def test_memoryless_control_has_zero_history_dependence(self):
        world = World(small_config(recurrent_memory=False))
        for _ in range(10):
            world.step()
        self.assertLess(measure(world)["memory_dependence"], 1e-12)

    def test_checkpoint_resumes_exactly(self):
        original = World(small_config())
        for _ in range(25):
            original.step()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "checkpoint.json.gz"
            save_checkpoint(original, path)
            restored = load_checkpoint(path)
        original.step()
        restored.step()
        self.assertEqual(measure(original), measure(restored))
        np.testing.assert_allclose(original.resource, restored.resource, rtol=0, atol=0)
        np.testing.assert_allclose(original.trace, restored.trace, rtol=0, atol=0)
        for left, right in zip(original.agents, restored.agents):
            np.testing.assert_allclose(left.w_actor, right.w_actor, rtol=0, atol=0)

    def test_long_smoke_run_remains_finite(self):
        world = World(small_config())
        for _ in range(300):
            world.step()
            if not world.agents:
                break
        self.assertGreater(len(world.agents), 0)
        self.assertTrue(np.isfinite(world.resource).all())
        self.assertTrue(np.isfinite(world.trace).all())
        for agent in world.agents:
            self.assertTrue(np.isfinite(agent.hidden).all())
            self.assertTrue(np.isfinite(agent.energy))

    def test_replicated_ablation_includes_all_controls(self):
        with tempfile.TemporaryDirectory() as directory:
            with redirect_stdout(StringIO()):
                results = run_ablation_experiment(
                    small_config(initial_agents=4, max_agents=8),
                    ticks=5,
                    output_directory=Path(directory),
                    replicates=2,
                )
        self.assertEqual(results["seeds"], [19, 20])
        self.assertEqual(set(results["conditions"]), {
            "adaptive", "frozen", "memoryless", "silent", "no_trace"
        })
        self.assertEqual(results["conditions"]["adaptive"]["replicates"], 2)


if __name__ == "__main__":
    unittest.main()
