"""Create a dependency-free SVG summary from a completed experiment.json."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path


COLORS = {
    "adaptive": "#007C83",
    "frozen": "#D95F02",
    "memoryless": "#6A51A3",
    "signal_blocked": "#4D6A7A",
    "trace_blocked": "#7A7A7A",
}
LABELS = {
    "adaptive": "Adaptive",
    "frozen": "Frozen",
    "memoryless": "Memoryless",
    "signal_blocked": "Signal blocked",
    "trace_blocked": "Trace blocked",
}


def _scale(value: float, low: float, high: float, top: float, bottom: float) -> float:
    if high <= low:
        return (top + bottom) / 2
    return bottom - (value - low) * (bottom - top) / (high - low)


def _panel(
    results: dict,
    metric: str,
    conditions: list[str],
    left: float,
    right: float,
    top: float,
    bottom: float,
    title: str,
    ylabel: str,
) -> list[str]:
    values = {
        condition: [
            float(results["runs"][str(seed)][condition]["endpoints"][metric])
            for seed in results["seeds"]
        ]
        for condition in conditions
    }
    flat = [value for group in values.values() for value in group]
    span = max(flat) - min(flat)
    padding = max(span * 0.08, max(abs(value) for value in flat) * 0.02, 1e-9)
    low, high = min(flat) - padding, max(flat) + padding
    width = right - left
    x_positions = {
        condition: left + width * (index + 0.5) / len(conditions)
        for index, condition in enumerate(conditions)
    }
    svg = [
        f'<text x="{left:.1f}" y="{top - 28:.1f}" class="panel-title">{html.escape(title)}</text>',
        f'<line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" class="axis"/>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{bottom}" class="axis"/>',
    ]
    for tick in range(5):
        value = low + (high - low) * tick / 4
        y = _scale(value, low, high, top, bottom)
        svg.extend(
            [
                f'<line x1="{left}" y1="{y:.1f}" x2="{right}" y2="{y:.1f}" class="grid"/>',
                f'<text x="{left - 10:.1f}" y="{y + 4:.1f}" class="tick" text-anchor="end">{value:.4f}</text>',
            ]
        )
    svg.append(
        f'<text x="{left - 58:.1f}" y="{(top + bottom) / 2:.1f}" class="axis-label" '
        f'text-anchor="middle" transform="rotate(-90 {left - 58:.1f} {(top + bottom) / 2:.1f})">'
        f'{html.escape(ylabel)}</text>'
    )
    for condition in conditions:
        x = x_positions[condition]
        group = values[condition]
        for index, value in enumerate(group):
            jitter = ((index * 37) % 19 - 9) * 0.8
            y = _scale(value, low, high, top, bottom)
            svg.append(
                f'<circle cx="{x + jitter:.1f}" cy="{y:.1f}" r="3.3" '
                f'fill="{COLORS[condition]}" fill-opacity="0.48"/>'
            )
        mean = sum(group) / len(group)
        mean_y = _scale(mean, low, high, top, bottom)
        svg.append(
            f'<line x1="{x - 24:.1f}" y1="{mean_y:.1f}" x2="{x + 24:.1f}" '
            f'y2="{mean_y:.1f}" stroke="{COLORS[condition]}" stroke-width="4"/>'
        )
        label = LABELS[condition]
        svg.append(
            f'<text x="{x:.1f}" y="{bottom + 25:.1f}" class="condition" '
            f'text-anchor="middle">{html.escape(label)}</text>'
        )
    return svg


def make_figure(input_path: Path, output_path: Path) -> None:
    results = json.loads(input_path.read_text())
    width, height = 1400, 720
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>",
        ".title{font:700 25px -apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;fill:#15252d}",
        ".subtitle{font:15px -apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;fill:#53636b}",
        ".panel-title{font:700 18px -apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;fill:#15252d}",
        ".axis-label,.condition{font:13px -apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;fill:#263940}",
        ".tick{font:12px ui-monospace,SFMono-Regular,Menlo,monospace;fill:#53636b}",
        ".axis{stroke:#263940;stroke-width:1.2}.grid{stroke:#dce4e7;stroke-width:1}",
        "</style>",
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff"/>',
        '<text x="55" y="45" class="title">Held-out paired causal-ablation study</text>',
        f'<text x="55" y="72" class="subtitle">n={len(results["seeds"])} independent seeds; points are seed-level endpoints; bars are means</text>',
    ]
    svg.extend(
        _panel(
            results,
            "net_energy_input_per_agent_step",
            list(COLORS),
            105,
            825,
            135,
            610,
            "A. Ecological performance",
            "Net energy input per agent-step",
        )
    )
    svg.extend(
        _panel(
            results,
            "prediction_error",
            ["adaptive", "frozen"],
            965,
            1335,
            135,
            610,
            "B. Prediction manipulation check",
            "One-step prediction error",
        )
    )
    svg.extend(
        [
            '<text x="55" y="690" class="subtitle">Interpretation: mechanism effects within this model only; no consciousness or sentience inference.</text>',
            "</svg>",
        ]
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(svg) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    make_figure(args.input, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
