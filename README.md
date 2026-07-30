# Sentient Sim

Sentient Sim is a reproducible agent-based research test bed for causal studies
of adaptive behavior. The historical name is retained for project continuity;
the software does **not** create, detect, or score consciousness. No accepted
behavior-only test currently establishes subjective experience in software.

The current model replaces an earlier rule-based prototype that contained
English thoughts, named emotions, scripted reflections, and a circular
“sentience score.” Agents now receive only permuted numerical channels and emit
permuted continuous outputs. The host does not tell them which channel maps to
motion, resources, internal state, environmental traces, or other agents.

## Research question

The defensible question is:

> Do online learning, recurrent state, unstructured local signaling, or a
> writable environmental field causally change prediction and ecological
> performance in this explicitly defined numerical world?

Five seed-paired conditions address that question:

- `adaptive`: all tested mechanisms active;
- `frozen`: no within-lifetime weight updates;
- `memoryless`: no recurrent carryover between decisions;
- `signal_blocked`: signal outputs and their costs remain, but delivery is
  blocked;
- `trace_blocked`: trace outputs and their costs remain, but field coupling is
  blocked.

The cost-matched controls are important. Removing a signal or trace cost would
give the control population free energy and confound the causal comparison.

## What is predefined

An assumption-free simulation is impossible. This model explicitly supplies:

- a local toroidal 2-D world and renewable scalar resource;
- finite energy and storage;
- anonymous sensory and actuator bandwidth;
- recurrent state and one-step predictive learning;
- scalar reinforcement from experienced energy change;
- inheritance, mutation, and probabilistic reproduction;
- local continuous signals and a decaying writable scalar field.

There are no supplied words, meanings, emotions, social roles, reflection
routines, tool categories, or target coordination patterns. That removes several
circular claims, but it does not make the architecture neutral.

## Install

Python 3.10 or newer and NumPy are required.

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
```

## Run one world

```bash
sentient-sim run \
  --config research/confirmatory_config_v1.json \
  --ticks 3000 \
  --seed 2000 \
  --output runs/seed-2000
```

A run writes a manifest, append-only metrics, compressed checkpoints, a summary,
and the final checkpoint. `--ticks` means additional ticks when resuming:

```bash
sentient-sim run \
  --ticks 3000 \
  --output runs/seed-2000-continued \
  --resume runs/seed-2000/checkpoint-final.json.gz
```

Checkpoint v3 stores cumulative ecological counters. Older v2 checkpoints still
load, although new cumulative-rate counters begin at zero after migration.

## Run the paired study

The frozen local protocol is in `research/PREREGISTRATION.md`. Pilot seeds
1000–1002 were used for configuration and must not enter confirmatory inference.
The fixed confirmatory seeds are 2000–2029.

```bash
sentient-sim experiment \
  --config research/confirmatory_config_v1.json \
  --ticks 3000 \
  --replicates 30 \
  --workers 3 \
  --output experiments/confirmatory-v1
```

Every seed-condition result is saved immediately. Re-running the same command
reuses completed records after verifying the protocol hash, so an interrupted
campaign can restart safely. A different protocol cannot silently reuse the
directory.

Generated artifacts include:

- `manifest.json`: protocol, source hash, Git revision, runtime, and timestamps;
- `runs/`: per-seed samples and endpoints;
- `runs.csv`: analysis-ready run-level data;
- `contrasts.csv`: paired effect estimates, intervals, p-values, and adjusted
  q-values;
- `experiment.json`: complete machine-readable result;
- `REPORT.md`: concise human-readable findings and validity checks.

The seed—not an agent or time sample—is the independent unit. The report uses
paired bootstrap intervals, paired random-sign tests, and Benjamini–Hochberg
correction across five fixed contrasts.

## Documentation and interpretation

- `research/ODD.md` gives the standard Overview, Design concepts, and Details
  model specification.
- `research/PREREGISTRATION.md` fixes hypotheses, outcomes, analysis, stopping,
  exclusions, and the separation between pilot and confirmatory seeds.
- `src/ARCHITECTURE.md` gives a shorter implementation map.
- `AI_USAGE.md` records the disclosure that must be completed and personally
  reviewed before submission.

A supported contrast means that a designed mechanism changed a named observable
under this model and parameterization. It does not establish consciousness,
self-awareness, intention, semantic language, or human-like experience. Null
signal or trace results must be reported as null or underpowered—not converted
into an emergence claim.

## Historical artifacts

Files under `analytics/`, `logs/`, and `research/research_paper.md` belong to the
retired scripted prototype. They are retained for provenance only and are not
evidence from the current model.

## License and citation

The code is MIT licensed. Citation metadata is in `CITATION.cff`. Archive a tagged
release and its exact result bundle with Zenodo before citing a DOI.
