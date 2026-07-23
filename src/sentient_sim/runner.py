from __future__ import annotations

import gzip
import json
from pathlib import Path
from typing import Any

import numpy as np

from .config import SimulationConfig
from .metrics import measure
from .world import World


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    return value


def _write_json_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(_jsonable(value), indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def save_checkpoint(world: World, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with gzip.open(temporary, "wt", encoding="utf-8") as handle:
        json.dump(_jsonable(world.to_state()), handle, separators=(",", ":"))
    temporary.replace(path)


def load_checkpoint(path: Path) -> World:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        state = json.load(handle)
    return World.from_state(state)


def run_world(
    config: SimulationConfig,
    ticks: int,
    output_directory: Path,
    metrics_every: int = 10,
    checkpoint_every: int = 500,
    resume: Path | None = None,
    quiet: bool = False,
) -> dict[str, Any]:
    if ticks <= 0:
        raise ValueError("ticks must be positive")
    if metrics_every <= 0:
        raise ValueError("metrics_every must be positive")
    output_directory.mkdir(parents=True, exist_ok=True)
    world = load_checkpoint(resume) if resume else World(config)
    start_tick = world.tick
    manifest = {
        "format_version": 2,
        "start_tick": start_tick,
        "requested_additional_ticks": ticks,
        "config": world.config.to_dict(),
        "interpretation": (
            "This run measures adaptation and emergence. It cannot establish or refute consciousness."
        ),
    }
    _write_json_atomic(output_directory / "manifest.json", manifest)
    metrics_path = output_directory / "metrics.jsonl"
    records: list[dict[str, Any]] = []

    with metrics_path.open("a", encoding="utf-8") as metrics_file:
        for _ in range(ticks):
            world.step()
            if world.tick % metrics_every == 0 or not world.agents:
                record = measure(world)
                records.append(record)
                metrics_file.write(json.dumps(record, sort_keys=True) + "\n")
                metrics_file.flush()
                if not quiet:
                    print(
                        f"tick={world.tick} population={record['population']} "
                        f"error={record['prediction_error']:.4f} generation={record['max_generation']}"
                    )
            if checkpoint_every and world.tick % checkpoint_every == 0:
                save_checkpoint(world, output_directory / f"checkpoint-{world.tick:08d}.json.gz")
            if not world.agents:
                break

    final_metrics = measure(world)
    summary = {
        "start_tick": start_tick,
        "end_tick": world.tick,
        "completed_ticks": world.tick - start_tick,
        "extinct": not bool(world.agents),
        "final": final_metrics,
        "interpretation": manifest["interpretation"],
    }
    _write_json_atomic(output_directory / "summary.json", summary)
    save_checkpoint(world, output_directory / "checkpoint-final.json.gz")
    return summary
