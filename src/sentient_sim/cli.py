from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

from .config import SimulationConfig
from .experiment import run_ablation_experiment
from .runner import run_world


def _common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--ticks", type=int, default=2000)
    parser.add_argument("--config", type=Path, help="JSON file containing simulation parameters")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--agents", type=int)
    parser.add_argument("--max-agents", type=int)
    parser.add_argument("--hidden", type=int)
    parser.add_argument("--signals", type=int)
    parser.add_argument("--output", type=Path, required=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sentient-sim",
        description="Run a minimal-prior adaptive-agent simulation.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run", help="run one simulation")
    _common(run_parser)
    run_parser.add_argument("--metrics-every", type=int, default=10)
    run_parser.add_argument("--checkpoint-every", type=int, default=500)
    run_parser.add_argument("--resume", type=Path)
    run_parser.add_argument("--frozen", action="store_true", help="disable online learning")
    run_parser.add_argument("--memoryless", action="store_true", help="disable recurrent carryover")
    run_parser.add_argument("--silent", action="store_true", help="disable inter-agent signals")
    run_parser.add_argument("--no-trace", action="store_true", help="disable the writable world field")
    run_parser.add_argument("--quiet", action="store_true")

    experiment_parser = subparsers.add_parser(
        "experiment", help="run matched learning, memory, signal, and world-field controls"
    )
    _common(experiment_parser)
    experiment_parser.add_argument(
        "--replicates",
        type=int,
        default=1,
        help="run consecutive seeds starting at --seed",
    )
    experiment_parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="independent worker processes; completed runs are cached for safe restart",
    )
    return parser


def _config(args: argparse.Namespace) -> SimulationConfig:
    if args.config:
        config = SimulationConfig.from_dict(json.loads(args.config.read_text()))
    else:
        config = SimulationConfig()
    overrides = {
        name: value
        for name, value in {
            "seed": args.seed,
            "initial_agents": args.agents,
            "max_agents": args.max_agents,
            "hidden_dim": args.hidden,
            "signal_dim": args.signals,
        }.items()
        if value is not None
    }
    return replace(
        config,
        **overrides,
        learning_enabled=config.learning_enabled and not getattr(args, "frozen", False),
        recurrent_memory=config.recurrent_memory and not getattr(args, "memoryless", False),
        signaling_enabled=config.signaling_enabled and not getattr(args, "silent", False),
        environmental_memory_enabled=(
            config.environmental_memory_enabled and not getattr(args, "no_trace", False)
        ),
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = _config(args)
    config.validate()
    if args.command == "run":
        run_world(
            config=config,
            ticks=args.ticks,
            output_directory=args.output,
            metrics_every=args.metrics_every,
            checkpoint_every=args.checkpoint_every,
            resume=args.resume,
            quiet=args.quiet,
        )
    else:
        run_ablation_experiment(
            config,
            args.ticks,
            args.output,
            args.replicates,
            workers=args.workers,
        )
    return 0
