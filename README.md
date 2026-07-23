# Sentient Sim

Sentient Sim is a reproducible experiment in open-ended adaptive behavior. It
does **not** claim to create, detect, or score consciousness. No accepted
behavioral test can currently establish subjective experience in software.

The simulator removes the earlier project's predefined emotions, English
thoughts, named personality traits, scripted reflections, hand-authored
symbols, and circular “sentience score.” Agents receive only permuted numerical
channels and produce permuted continuous outputs. They are never told which
channel represents motion, resources, their own condition, or another agent.

## What is minimally predefined

A literally assumption-free simulation is impossible. Computation always
requires state, transition rules, and some source of selection or value. This
version keeps its priors explicit and small:

- a local two-dimensional world with a regenerating scalar field;
- finite agent energy and storage, creating persistence pressure without
  unbounded accumulation at the population limit;
- anonymous sensory and actuator bandwidth;
- a slowly changing writable scalar field for external memory, with no supplied
  interpretation or artifact types;
- recurrent state, one-step prediction, and continuous policy learning;
- variation and inheritance when agents accumulate enough energy.

There are no semantic tasks such as “speak,” “build,” “feel,” or “reflect.” The
world privately maps anonymous outputs to movement, field coupling, and local
signals. That mapping is randomized for every seed.

## Architecture

Each agent has a small recurrent numerical workspace. It learns to predict the
next observation and adjusts its policy from experienced energy change plus a
small learning-progress signal. Reproduction mutates the learned controller,
allowing within-lifetime learning and across-generation selection to interact.

Signals are continuous vectors with no dictionary or supplied meaning. They
matter only if populations discover a causal use for them. The simulator
measures their power, counterfactual influence on receiver policies, and
correlation with later outcomes.

Agents can also add to or subtract from a decaying local scalar field. This is a
neutral route to trails, external memory, or environmental coordination; none
of those uses is scripted. The `no_trace` ablation checks whether the capability
causally changes the population.

## Install and run

Python 3.10+ and NumPy are required.

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .

sentient-sim run \
  --ticks 5000 \
  --seed 7 \
  --agents 48 \
  --output runs/seed-7
```

The compatibility entry point also works:

```bash
PYTHONPATH=src python src/main.py run --ticks 5000 --output runs/seed-7
```

Runs write a manifest, append-only metrics, periodic compressed checkpoints,
a final checkpoint, and a summary. Resume a saved world with:

```bash
sentient-sim run \
  --ticks 5000 \
  --output runs/seed-7-resumed \
  --resume runs/seed-7/checkpoint-final.json.gz
```

`--ticks` means additional ticks when resuming.

## Run causal controls

Visual complexity is weak evidence because random systems can look purposeful.
The experiment command instead runs matched conditions with learning frozen,
recurrent memory removed, signaling disabled, or the writable field removed:

```bash
sentient-sim experiment \
  --ticks 3000 \
  --seed 7 \
  --replicates 5 \
  --agents 48 \
  --output experiments/seed-7
```

It produces `experiment.json` and `REPORT.md`. Replicates use consecutive seeds
starting at `--seed`; multiple seeds are essential before treating a difference
as robust.

## Interpreting the output

The measurements cover persistence, predictive error, learning progress,
lineage diversity, behavioral diversity, memory dependence, signaling effects,
and local coordination. They can demonstrate adaptive or emergent mechanisms.
They cannot answer whether an agent has subjective experience.

The files in `analytics/` and `logs/` came from the legacy hardcoded simulator
and are retained only as historical artifacts. They are not results from this
implementation.

## Tests

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```
