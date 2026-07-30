from __future__ import annotations

import json
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

    def test_v2_checkpoint_state_migrates(self):
        original = World(small_config())
        for _ in range(4):
            original.step()
        state = original.to_state()
        state["format_version"] = 2
        for field in (
            "agent_steps",
            "capacity_ticks",
            "resource_extracted",
            "harvest_energy",
            "energy_cost",
            "last_resource_extracted",
            "last_harvest_energy",
            "last_energy_cost",
            "last_agent_steps",
        ):
            state.pop(field)
        migrated = World.from_state(state)
        self.assertEqual(migrated.agent_steps, 0)
        migrated.step()
        self.assertGreater(migrated.agent_steps, 0)
        self.assertTrue(np.isfinite(migrated.energy_cost))

    def test_ablation_worlds_have_matched_initialization(self):
        adaptive = World(small_config())
        signal_blocked = World(small_config(signaling_enabled=False))
        trace_blocked = World(small_config(environmental_memory_enabled=False))
        for control in (signal_blocked, trace_blocked):
            np.testing.assert_allclose(adaptive.resource, control.resource, rtol=0, atol=0)
            np.testing.assert_allclose(
                adaptive.sensor_permutation, control.sensor_permutation, rtol=0, atol=0
            )
            for left, right in zip(adaptive.agents, control.agents):
                np.testing.assert_allclose(left.position, right.position, rtol=0, atol=0)
                np.testing.assert_allclose(left.w_actor, right.w_actor, rtol=0, atol=0)

    def test_signal_and_trace_controls_retain_output_costs(self):
        adaptive = World(small_config())
        signal_blocked = World(small_config(signaling_enabled=False))
        trace_blocked = World(small_config(environmental_memory_enabled=False))
        adaptive.step()
        signal_blocked.step()
        trace_blocked.step()
        self.assertAlmostEqual(adaptive.energy_cost, signal_blocked.energy_cost)
        self.assertAlmostEqual(adaptive.energy_cost, trace_blocked.energy_cost)
        self.assertGreater(
            sum(float(np.linalg.norm(agent.emitted_signal)) for agent in signal_blocked.agents),
            0.0,
        )
        self.assertEqual(float(np.max(np.abs(trace_blocked.trace))), 0.0)

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
                "adaptive", "frozen", "memoryless", "signal_blocked", "trace_blocked"
            })
            self.assertEqual(results["conditions"]["adaptive"]["replicates"], 2)
            self.assertEqual(len(results["contrasts"]), 5)
            self.assertEqual(results["contrasts"][0]["n"], 2)
            self.assertTrue((Path(directory) / "runs.csv").exists())
            self.assertTrue((Path(directory) / "contrasts.csv").exists())
            self.assertTrue((Path(directory) / "manifest.json").exists())

    def test_replicated_ablation_resumes_cached_runs(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            with redirect_stdout(StringIO()):
                first = run_ablation_experiment(
                    small_config(initial_agents=4, max_agents=8),
                    ticks=3,
                    output_directory=output,
                    replicates=2,
                )
                second = run_ablation_experiment(
                    small_config(initial_agents=4, max_agents=8),
                    ticks=3,
                    output_directory=output,
                    replicates=2,
                )
        self.assertEqual(first, second)

    def test_experiment_refuses_protocol_or_source_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            config = small_config(initial_agents=4, max_agents=8)
            with redirect_stdout(StringIO()):
                run_ablation_experiment(config, 2, output, replicates=1)
            with self.assertRaisesRegex(ValueError, "different protocol"):
                run_ablation_experiment(config, 3, output, replicates=1)

            run_path = output / "runs" / "seed-00000019" / "adaptive.json"
            record = json.loads(run_path.read_text())
            record["source_sha256"] = "not-the-source"
            run_path.write_text(json.dumps(record))
            with self.assertRaisesRegex(ValueError, "source mismatch"):
                run_ablation_experiment(config, 2, output, replicates=1)


if __name__ == "__main__":
    unittest.main()
