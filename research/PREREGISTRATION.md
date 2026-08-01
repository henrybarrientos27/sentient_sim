# Prospective confirmatory protocol v1

**Status:** frozen locally before analysis of confirmatory seeds; not externally
registered. This document must not be described as an OSF preregistration unless
an immutable OSF registration was created before the confirmatory runs.

**Freeze date:** 2026-07-29  
**Protocol identifier:** `confirmatory-ablation-v1`  
**Author:** Henry Barrientos

## Scope and claim boundary

The study asks whether four designed mechanisms—online learning, recurrent
state, continuous local signals, and a writable environmental field—causally
change specified observable outcomes in a resource-limited numerical world.

The study does not test consciousness, sentience, subjective experience,
self-awareness, emotion, understanding, or semantic language. No result from
this protocol will be presented as evidence for those properties.

## Separation of exploration and confirmation

Seeds 1000–1002 were used to tune ecological parameters and verify that the
population safety cap was not the dominant constraint. They are permanently
excluded from confirmatory inference. Confirmatory runs use 30 previously
unexamined seeds, 2000–2029. Parameters are fixed in
`research/confirmatory_config_v1.json` and will not be changed after inspecting
confirmatory outcomes.

## Design

- Independent unit: one random seed.
- Replicates: 30 paired seeds.
- Duration: 3,000 ticks per condition.
- Initial agents: 48; population safety cap: 128.
- Conditions are initialized identically within each seed.
- `adaptive`: all mechanisms active.
- `frozen`: online weight updates blocked.
- `memoryless`: recurrent carryover reset before each decision.
- `signal_blocked`: signals are emitted and cost energy, but are not delivered.
- `trace_blocked`: trace commands cost energy, but cannot modify or reveal the
  trace field.

Cost-matching in the last two controls is required. It prevents a control from
receiving free energy merely because an output channel was disabled.

## Fixed endpoint rule

The simulator targets 100 evenly spaced measurements per run. State endpoints
are the arithmetic mean over the latter half of those measurements. Cumulative
rate endpoints are evaluated at the final completed tick. The confirmatory
ecological endpoint is cumulative harvested energy minus action and basal costs,
divided by cumulative agent-ticks (`net_energy_input_per_agent_step`).

Agents and within-run time samples are not treated as independent replicates.

## Hypotheses and contrasts

All tests are paired by seed. A positive favorable difference supports the
fully adaptive condition.

1. `learning_prediction` (manipulation check): adaptive prediction error is
   lower than frozen prediction error.
2. `learning_ecology` (primary): adaptive net energy input per agent-step is
   higher than frozen.
3. `memory_ecology` (primary): adaptive net energy input per agent-step is
   higher than memoryless.
4. `signal_ecology` (primary): adaptive net energy input per agent-step is
   higher than signal-blocked.
5. `trace_ecology` (primary): adaptive net energy input per agent-step is
   higher than trace-blocked.

## Statistical analysis

- Report paired means, favorable mean differences, paired standardized effect
  size (`dz`), win rate, and a deterministic 20,000-resample paired bootstrap
  95% confidence interval.
- Use a two-sided paired random-sign randomization test with 50,000 draws.
- Control the false discovery rate across the five fixed contrasts using the
  Benjamini–Hochberg procedure.
- Call a preregistered direction supported only if the adjusted `q < 0.05`, the
  favorable mean difference is positive, and its bootstrap interval is wholly
  above zero.
- With 30 paired seeds, the approximate 80% power threshold is `dz ≈ 0.51` for
  a two-sided 5% test. Smaller effects should be treated as underpowered or
  exploratory rather than absent.

## Stopping, failures, and exclusions

- Run all 150 seed-condition combinations. Do not stop early for significance.
- Exclude no completed run based on its outcome, including extinction.
- A crashed or interrupted run may be resumed or rerun only with the same seed,
  code, configuration, and protocol hash.
- If any condition spends more than a mean 5% of ticks at the population safety
  cap, ecological and evolutionary conclusions are declared capacity-limited;
  parameters are not retuned on these confirmatory seeds.
- Any departure from this document is listed as a protocol deviation and its
  affected analysis is labeled exploratory.

## Required provenance

The runner records the protocol hash, source hash, Git revision when available,
Python, NumPy, operating system, timestamps, per-run samples, run-level
endpoints, and all statistical contrasts. Generated results are immutable inputs
to the manuscript and are archived with the tagged software release.
