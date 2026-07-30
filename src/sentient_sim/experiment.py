from __future__ import annotations

import csv
import hashlib
import json
import platform
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from .config import SimulationConfig
from .metrics import measure
from .world import World


PROTOCOL_VERSION = "confirmatory-ablation-v1"
CONDITIONS = {
    "adaptive": {},
    "frozen": {"learning_enabled": False},
    "memoryless": {"recurrent_memory": False},
    # These interventions block reception/coupling but retain the anonymous
    # output dimensions and energy costs, avoiding the confound in v0.3.
    "signal_blocked": {"signaling_enabled": False},
    "trace_blocked": {"environmental_memory_enabled": False},
}

MEASURE_KEYS = (
    "population",
    "population_exposure",
    "capacity_fraction",
    "capacity_tick_fraction",
    "mean_energy",
    "mean_reward",
    "prediction_error",
    "memory_dependence",
    "signal_influence",
    "signal_outcome_correlation",
    "environmental_trace_power",
    "environmental_trace_structure",
    "local_coordination",
    "behavioral_diversity",
    "lineage_entropy",
    "root_lineage_survival",
    "max_generation",
    "harvest_energy_per_agent_step",
    "energy_cost_per_agent_step",
    "net_energy_input_per_agent_step",
    "instant_harvest_energy_per_agent",
    "instant_energy_cost_per_agent",
    "birth_rate_per_1000_agent_steps",
    "death_rate_per_1000_agent_steps",
)

# Each seed is one independent unit. Positive favorable differences always
# favor the fully adaptive condition, regardless of the metric's direction.
PRIMARY_CONTRASTS = (
    {
        "id": "learning_prediction",
        "control": "frozen",
        "metric": "prediction_error",
        "higher_is_better": False,
        "role": "manipulation check",
    },
    {
        "id": "learning_ecology",
        "control": "frozen",
        "metric": "net_energy_input_per_agent_step",
        "higher_is_better": True,
        "role": "primary ecological outcome",
    },
    {
        "id": "memory_ecology",
        "control": "memoryless",
        "metric": "net_energy_input_per_agent_step",
        "higher_is_better": True,
        "role": "primary ecological outcome",
    },
    {
        "id": "signal_ecology",
        "control": "signal_blocked",
        "metric": "net_energy_input_per_agent_step",
        "higher_is_better": True,
        "role": "primary ecological outcome",
    },
    {
        "id": "trace_ecology",
        "control": "trace_blocked",
        "metric": "net_energy_input_per_agent_step",
        "higher_is_better": True,
        "role": "primary ecological outcome",
    },
)

# Cumulative rates are evaluated once at the final tick. Other outcomes are the
# mean of the latter half of sampled states, defined before confirmatory runs.
FINAL_ENDPOINTS = {
    "population_exposure",
    "capacity_tick_fraction",
    "root_lineage_survival",
    "harvest_energy_per_agent_step",
    "energy_cost_per_agent_step",
    "net_energy_input_per_agent_step",
    "birth_rate_per_1000_agent_steps",
    "death_rate_per_1000_agent_steps",
}


def _atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _source_digest() -> str:
    digest = hashlib.sha256()
    source_directory = Path(__file__).resolve().parent
    for path in sorted(source_directory.glob("*.py")):
        digest.update(path.name.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _git_revision() -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=Path(__file__).resolve().parents[3],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return completed.stdout.strip() or None


def _protocol(config: SimulationConfig, ticks: int, seeds: list[int]) -> dict[str, Any]:
    return {
        "protocol_version": PROTOCOL_VERSION,
        "base_config": config.to_dict(),
        "ticks": ticks,
        "seeds": seeds,
        "conditions": CONDITIONS,
        "primary_contrasts": list(PRIMARY_CONTRASTS),
        "sampling": {
            "samples_per_run_target": 100,
            "state_endpoint": "mean of latter half of sampled states",
            "cumulative_rate_endpoint": "final value",
            "independent_unit": "seed",
        },
        "analysis": {
            "confidence_level": 0.95,
            "bootstrap_resamples": 20000,
            "random_sign_permutations": 50000,
            "multiplicity": "Benjamini-Hochberg across five preregistered contrasts",
            "test_sidedness": "two-sided",
        },
    }


def _protocol_hash(protocol: dict[str, Any]) -> str:
    encoded = json.dumps(protocol, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _condition(
    config: SimulationConfig,
    ticks: int,
    overrides: dict[str, Any],
) -> dict[str, Any]:
    world = World(replace(config, **overrides))
    samples: list[dict[str, float | int]] = []
    sample_every = max(1, ticks // 100)
    for _ in range(ticks):
        world.step()
        if world.tick % sample_every == 0:
            samples.append(measure(world))
        if not world.agents:
            break
    if not samples or samples[-1]["tick"] != world.tick:
        samples.append(measure(world))
    tail = samples[len(samples) // 2 :]
    tail_mean = {
        key: float(np.mean([float(sample[key]) for sample in tail])) for key in MEASURE_KEYS
    }
    final = measure(world)
    endpoints = {
        key: float(final[key]) if key in FINAL_ENDPOINTS else tail_mean[key]
        for key in MEASURE_KEYS
    }
    return {
        "ticks_completed": world.tick,
        "extinct": not bool(world.agents),
        "sample_every": sample_every,
        "tail_mean": tail_mean,
        "endpoints": endpoints,
        "final": final,
        "samples": samples,
    }


def _run_task(
    seed: int,
    name: str,
    base_config: dict[str, Any],
    ticks: int,
    protocol_sha256: str,
) -> tuple[int, str, dict[str, Any]]:
    config = SimulationConfig.from_dict({**base_config, "seed": seed})
    run = _condition(config, ticks, CONDITIONS[name])
    run.update(
        {
            "seed": seed,
            "condition": name,
            "overrides": CONDITIONS[name],
            "protocol_sha256": protocol_sha256,
        }
    )
    return seed, name, run


def _paired_statistics(
    adaptive: list[float],
    control: list[float],
    higher_is_better: bool,
    rng: np.random.Generator,
) -> dict[str, Any]:
    adaptive_array = np.asarray(adaptive, dtype=np.float64)
    control_array = np.asarray(control, dtype=np.float64)
    raw = adaptive_array - control_array
    favorable = raw if higher_is_better else -raw
    n = favorable.size
    observed = float(np.mean(favorable))

    bootstrap_indices = rng.integers(0, n, size=(20000, n))
    bootstrap = np.mean(favorable[bootstrap_indices], axis=1)
    ci_low, ci_high = np.quantile(bootstrap, [0.025, 0.975])

    signs = rng.choice(np.array([-1.0, 1.0]), size=(50000, n))
    null_means = np.mean(signs * favorable, axis=1)
    p_value = float(
        (1 + np.count_nonzero(np.abs(null_means) >= abs(observed))) / (len(null_means) + 1)
    )
    standard_deviation = float(np.std(favorable, ddof=1)) if n > 1 else 0.0
    effect_size = observed / standard_deviation if standard_deviation > 0 else None
    return {
        "n": int(n),
        "adaptive_mean": float(np.mean(adaptive_array)),
        "control_mean": float(np.mean(control_array)),
        "mean_favorable_difference": observed,
        "ci95_low": float(ci_low),
        "ci95_high": float(ci_high),
        "paired_effect_size_dz": None if effect_size is None else float(effect_size),
        "win_rate": float(np.mean(favorable > 0)),
        "two_sided_randomization_p": p_value,
    }


def _benjamini_hochberg(p_values: list[float]) -> list[float]:
    count = len(p_values)
    order = np.argsort(p_values)
    adjusted = np.ones(count, dtype=np.float64)
    running = 1.0
    for reverse_rank in range(count - 1, -1, -1):
        index = int(order[reverse_rank])
        rank = reverse_rank + 1
        running = min(running, p_values[index] * count / rank)
        adjusted[index] = min(1.0, running)
    return adjusted.tolist()


def _analyze(results: dict[str, Any]) -> list[dict[str, Any]]:
    rng = np.random.default_rng(20260729)
    contrasts: list[dict[str, Any]] = []
    for specification in PRIMARY_CONTRASTS:
        metric = str(specification["metric"])
        control_name = str(specification["control"])
        adaptive = [
            float(results["runs"][str(seed)]["adaptive"]["endpoints"][metric])
            for seed in results["seeds"]
        ]
        control = [
            float(results["runs"][str(seed)][control_name]["endpoints"][metric])
            for seed in results["seeds"]
        ]
        statistics = _paired_statistics(
            adaptive,
            control,
            bool(specification["higher_is_better"]),
            rng,
        )
        contrasts.append({**specification, **statistics})

    adjusted = _benjamini_hochberg(
        [float(item["two_sided_randomization_p"]) for item in contrasts]
    )
    for item, q_value in zip(contrasts, adjusted):
        item["bh_q"] = float(q_value)
        item["supports_preregistered_direction"] = bool(
            q_value < 0.05
            and float(item["ci95_low"]) > 0.0
            and float(item["mean_favorable_difference"]) > 0.0
        )
    return contrasts


def _condition_summaries(results: dict[str, Any]) -> dict[str, Any]:
    summaries: dict[str, Any] = {}
    for name in CONDITIONS:
        runs = [results["runs"][str(seed)][name] for seed in results["seeds"]]
        endpoint_mean = {
            key: float(np.mean([run["endpoints"][key] for run in runs])) for key in MEASURE_KEYS
        }
        endpoint_sd = {
            key: float(np.std([run["endpoints"][key] for run in runs], ddof=1))
            if len(runs) > 1
            else 0.0
            for key in MEASURE_KEYS
        }
        summaries[name] = {
            "replicates": len(runs),
            "extinction_count": sum(bool(run["extinct"]) for run in runs),
            "mean_ticks_completed": float(np.mean([run["ticks_completed"] for run in runs])),
            "endpoint_mean": endpoint_mean,
            "endpoint_sd": endpoint_sd,
            # Retained for callers of the v0.3 API. New work should use endpoints.
            "tail_mean": endpoint_mean,
        }
    return summaries


def _write_csv_files(results: dict[str, Any], output_directory: Path) -> None:
    run_fields = ["seed", "condition", "ticks_completed", "extinct", *MEASURE_KEYS]
    with (output_directory / "runs.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=run_fields)
        writer.writeheader()
        for seed in results["seeds"]:
            for condition in CONDITIONS:
                run = results["runs"][str(seed)][condition]
                writer.writerow(
                    {
                        "seed": seed,
                        "condition": condition,
                        "ticks_completed": run["ticks_completed"],
                        "extinct": run["extinct"],
                        **run["endpoints"],
                    }
                )
    contrast_fields = list(results["contrasts"][0]) if results["contrasts"] else []
    with (output_directory / "contrasts.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=contrast_fields)
        writer.writeheader()
        writer.writerows(results["contrasts"])


def _report(results: dict[str, Any]) -> str:
    lines = [
        "# Confirmatory causal-ablation report",
        "",
        f"Protocol: `{results['protocol']['protocol_version']}`  ",
        f"Protocol SHA-256: `{results['protocol_sha256']}`  ",
        f"Independent seeds: `{len(results['seeds'])}`  ",
        f"Ticks per condition: `{results['ticks']}`",
        "",
        "This is a paired mechanism-ablation study. It is **not a test of consciousness**.",
        "A seed is the unit of replication; time samples and individual agents are not",
        "treated as independent replicates. Positive differences favor the adaptive condition.",
        "",
        "## Preregistered contrasts",
        "",
        "| Contrast | Metric | n | Favorable difference | 95% CI | p | BH q | Supported? |",
        "|---|---|---:|---:|---:|---:|---:|:---:|",
    ]
    for item in results["contrasts"]:
        supported = "yes" if item["supports_preregistered_direction"] else "no"
        lines.append(
            f"| {item['id']} | {item['metric']} | {item['n']} | "
            f"{item['mean_favorable_difference']:.6f} | "
            f"[{item['ci95_low']:.6f}, {item['ci95_high']:.6f}] | "
            f"{item['two_sided_randomization_p']:.4f} | {item['bh_q']:.4f} | {supported} |"
        )

    capacity = max(
        summary["endpoint_mean"]["capacity_tick_fraction"]
        for summary in results["conditions"].values()
    )
    lines.extend(
        [
            "",
            "## Validity checks",
            "",
            f"- Maximum mean fraction of ticks at the population safety cap: `{capacity:.4f}`.",
            f"- Extinctions across all runs: `{sum(summary['extinction_count'] for summary in results['conditions'].values())}`.",
        ]
    )
    if capacity > 0.05:
        lines.append(
            "- **Caution:** the safety cap was active for more than 5% of ticks; ecological and evolutionary conclusions are capacity-limited."
        )
    else:
        lines.append("- The preregistered 5% capacity-interference threshold was not exceeded.")
    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            "A supported contrast is evidence that the intervened mechanism changed the named",
            "observable under this model and parameterization. A null contrast is inconclusive",
            "between absence of a useful mechanism and insufficient power. Neither outcome",
            "establishes subjective experience, self-awareness, meaning, or sentience.",
            "",
        ]
    )
    return "\n".join(lines)


def run_ablation_experiment(
    config: SimulationConfig,
    ticks: int,
    output_directory: Path,
    replicates: int = 1,
    workers: int = 1,
) -> dict[str, Any]:
    if ticks <= 0:
        raise ValueError("ticks must be positive")
    if replicates <= 0:
        raise ValueError("replicates must be positive")
    if workers <= 0:
        raise ValueError("workers must be positive")
    config.validate()
    output_directory.mkdir(parents=True, exist_ok=True)
    seeds = [config.seed + offset for offset in range(replicates)]
    protocol = _protocol(config, ticks, seeds)
    protocol_sha256 = _protocol_hash(protocol)
    manifest_path = output_directory / "manifest.json"
    if manifest_path.exists():
        existing = json.loads(manifest_path.read_text())
        if existing.get("protocol_sha256") != protocol_sha256:
            raise ValueError(
                "output directory contains a different protocol; choose a new directory"
            )
        started_at = existing["started_at"]
    else:
        started_at = _utc_now()

    manifest = {
        "protocol": protocol,
        "protocol_sha256": protocol_sha256,
        "source_sha256": _source_digest(),
        "git_revision": _git_revision(),
        "python": sys.version,
        "numpy": np.__version__,
        "platform": platform.platform(),
        "started_at": started_at,
        "completed_at": None,
        "status": "running",
    }
    _atomic_json(manifest_path, manifest)

    results: dict[str, Any] = {
        "protocol": protocol,
        "protocol_sha256": protocol_sha256,
        "seeds": seeds,
        "ticks": ticks,
        "runs": {str(seed): {} for seed in seeds},
        "conditions": {},
        "contrasts": [],
        "interpretation": "Mechanism ablation only; not a test for consciousness.",
    }
    pending: list[tuple[int, str]] = []
    for seed in seeds:
        for name in CONDITIONS:
            path = output_directory / "runs" / f"seed-{seed:08d}" / f"{name}.json"
            if path.exists():
                run = json.loads(path.read_text())
                if run.get("protocol_sha256") != protocol_sha256:
                    raise ValueError(f"protocol mismatch in cached run {path}")
                results["runs"][str(seed)][name] = run
                print(f"seed={seed} condition={name} cached")
            else:
                pending.append((seed, name))

    def save_completed(seed: int, name: str, run: dict[str, Any]) -> None:
        results["runs"][str(seed)][name] = run
        path = output_directory / "runs" / f"seed-{seed:08d}" / f"{name}.json"
        _atomic_json(path, run)
        print(f"seed={seed} condition={name} complete")

    if workers == 1:
        for seed, name in pending:
            save_completed(
                *_run_task(seed, name, config.to_dict(), ticks, protocol_sha256)
            )
    else:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(
                    _run_task, seed, name, config.to_dict(), ticks, protocol_sha256
                ): (seed, name)
                for seed, name in pending
            }
            for future in as_completed(futures):
                save_completed(*future.result())

    results["conditions"] = _condition_summaries(results)
    results["contrasts"] = _analyze(results)
    _atomic_json(output_directory / "experiment.json", results)
    _write_csv_files(results, output_directory)
    (output_directory / "REPORT.md").write_text(_report(results))
    manifest["completed_at"] = _utc_now()
    manifest["status"] = "complete"
    _atomic_json(manifest_path, manifest)
    return results
