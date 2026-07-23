from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np

from .config import SimulationConfig
from .metrics import measure
from .world import World


CONDITIONS = {
    "adaptive": {},
    "frozen": {"learning_enabled": False},
    "memoryless": {"recurrent_memory": False},
    "silent": {"signaling_enabled": False},
    "no_trace": {"environmental_memory_enabled": False},
}

MEASURE_KEYS = (
    "population",
    "mean_energy",
    "prediction_error",
    "memory_dependence",
    "signal_influence",
    "signal_outcome_correlation",
    "environmental_trace_power",
    "environmental_trace_structure",
    "local_coordination",
    "behavioral_diversity",
    "lineage_entropy",
    "max_generation",
)


def _condition(config: SimulationConfig, ticks: int, overrides: dict[str, Any]) -> dict[str, Any]:
    world = World(replace(config, **overrides))
    samples: list[dict[str, float | int]] = []
    sample_every = max(1, ticks // 100)
    for _ in range(ticks):
        world.step()
        if world.tick % sample_every == 0:
            samples.append(measure(world))
        if not world.agents:
            break
    if not samples:
        samples.append(measure(world))
    tail = samples[len(samples) // 2 :]
    aggregate = {
        key: float(np.mean([float(sample[key]) for sample in tail])) for key in MEASURE_KEYS
    }
    return {
        "ticks_completed": world.tick,
        "extinct": not bool(world.agents),
        "tail_mean": aggregate,
        "final": measure(world),
    }


def _report(results: dict[str, Any], ticks: int) -> str:
    adaptive = results["conditions"]["adaptive"]["tail_mean"]
    frozen = results["conditions"]["frozen"]["tail_mean"]
    memoryless = results["conditions"]["memoryless"]["tail_mean"]
    silent = results["conditions"]["silent"]["tail_mean"]
    no_trace = results["conditions"]["no_trace"]["tail_mean"]

    def delta(value: float, baseline: float) -> str:
        return f"{value - baseline:+.4f}"

    return f"""# Causal ablation report

Seeds: `{', '.join(str(seed) for seed in results['seeds'])}`  
Requested ticks per condition: `{ticks}`

This experiment compares matched simulations that differ by one mechanism. It
tests whether learning, recurrent memory, or signaling causally changes measured
behavior. It is **not** a consciousness test.

| Measure | Adaptive | Frozen | Memoryless | Silent | No trace |
|---|---:|---:|---:|---:|---:|
| Population | {adaptive['population']:.2f} | {frozen['population']:.2f} | {memoryless['population']:.2f} | {silent['population']:.2f} | {no_trace['population']:.2f} |
| Prediction error | {adaptive['prediction_error']:.4f} | {frozen['prediction_error']:.4f} | {memoryless['prediction_error']:.4f} | {silent['prediction_error']:.4f} | {no_trace['prediction_error']:.4f} |
| Memory dependence | {adaptive['memory_dependence']:.4f} | {frozen['memory_dependence']:.4f} | {memoryless['memory_dependence']:.4f} | {silent['memory_dependence']:.4f} | {no_trace['memory_dependence']:.4f} |
| Signal influence | {adaptive['signal_influence']:.4f} | {frozen['signal_influence']:.4f} | {memoryless['signal_influence']:.4f} | {silent['signal_influence']:.4f} | {no_trace['signal_influence']:.4f} |
| Trace structure | {adaptive['environmental_trace_structure']:.4f} | {frozen['environmental_trace_structure']:.4f} | {memoryless['environmental_trace_structure']:.4f} | {silent['environmental_trace_structure']:.4f} | {no_trace['environmental_trace_structure']:.4f} |
| Local coordination | {adaptive['local_coordination']:.4f} | {frozen['local_coordination']:.4f} | {memoryless['local_coordination']:.4f} | {silent['local_coordination']:.4f} | {no_trace['local_coordination']:.4f} |
| Lineage entropy | {adaptive['lineage_entropy']:.4f} | {frozen['lineage_entropy']:.4f} | {memoryless['lineage_entropy']:.4f} | {silent['lineage_entropy']:.4f} | {no_trace['lineage_entropy']:.4f} |

Selected causal contrasts (adaptive minus control):

- Prediction error vs frozen: {delta(adaptive['prediction_error'], frozen['prediction_error'])}
- Population vs frozen: {delta(adaptive['population'], frozen['population'])}
- Memory dependence vs memoryless: {delta(adaptive['memory_dependence'], memoryless['memory_dependence'])}
- Coordination vs silent: {delta(adaptive['local_coordination'], silent['local_coordination'])}
- Population vs no trace: {delta(adaptive['population'], no_trace['population'])}

Interpret differences as evidence about mechanisms, not subjective experience.
Replicate across many seeds before treating any contrast as robust.
"""


def run_ablation_experiment(
    config: SimulationConfig,
    ticks: int,
    output_directory: Path,
    replicates: int = 1,
) -> dict[str, Any]:
    if ticks <= 0:
        raise ValueError("ticks must be positive")
    if replicates <= 0:
        raise ValueError("replicates must be positive")
    output_directory.mkdir(parents=True, exist_ok=True)
    seeds = [config.seed + offset for offset in range(replicates)]
    results: dict[str, Any] = {
        "seeds": seeds,
        "ticks": ticks,
        "runs": {},
        "conditions": {},
        "interpretation": "Mechanism ablation only; not a test for consciousness.",
    }
    condition_runs: dict[str, list[dict[str, Any]]] = {name: [] for name in CONDITIONS}
    for seed in seeds:
        seeded_config = replace(config, seed=seed)
        results["runs"][str(seed)] = {}
        for name, overrides in CONDITIONS.items():
            print(f"seed={seed} condition={name}")
            run = _condition(seeded_config, ticks, overrides)
            results["runs"][str(seed)][name] = run
            condition_runs[name].append(run)

    for name, runs in condition_runs.items():
        results["conditions"][name] = {
            "replicates": replicates,
            "extinction_count": sum(bool(run["extinct"]) for run in runs),
            "mean_ticks_completed": float(np.mean([run["ticks_completed"] for run in runs])),
            "tail_mean": {
                key: float(np.mean([run["tail_mean"][key] for run in runs]))
                for key in MEASURE_KEYS
            },
        }
    (output_directory / "experiment.json").write_text(
        json.dumps(results, indent=2, sort_keys=True) + "\n"
    )
    (output_directory / "REPORT.md").write_text(_report(results, ticks))
    return results
