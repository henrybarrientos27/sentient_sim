---
title: "Causal characterization of adaptive mechanisms in a resource-limited multi-agent simulation"
author: "Henry Barrientos"
date: "Draft"
---

# Abstract

Claims of emergence in agent-based simulations can become circular when the
reported behavior is encoded in the model or selected through a designer-defined
composite score. We present an open numerical multi-agent test bed with anonymous
permuted interfaces, recurrent controllers, one-step predictive learning,
energy-based reinforcement, inheritance, mutation, continuous local signals,
and a writable environmental field. We evaluate mechanisms with paired,
cost-matched interventions over independently seeded runs. The study measures
prediction and ecological performance and explicitly excludes consciousness,
sentience, semantic language, and subjective experience from its claims.

**Results placeholder:** Replace this paragraph only from the immutable
confirmatory report. State the number of seeds, all five adjusted tests, effect
sizes and intervals, population-cap diagnostic, extinctions, and null outcomes.

# 1. Introduction

Complex-looking simulation trajectories do not by themselves identify the
mechanism that generated them. A controller can also appear intentional because
its designer supplied semantic states or evaluated it with a score constructed
from those same states. The present work narrows the question to a falsifiable
one: whether removing one designed capacity changes a pre-specified observable
under matched initialization.

The contribution is a reproducible experimental scaffold rather than a theory or
detector of consciousness. It combines explicit architectural priors, exact
checkpoint continuation, cost-matched causal controls, seed-level inference,
interruption-safe results, and machine-readable provenance.

# 2. Methods

## 2.1 Model

The full model follows the ODD protocol in `research/ODD.md`. Briefly, agents
occupy a toroidal resource field and receive local numerical observations whose
channel ordering and signs are randomized by seed. Their recurrent controllers
predict the next observation and update stochastic policies from experienced
energy change plus a small learning-progress term. Energy-rich controllers
reproduce mutated descendants.

## 2.2 Interventions

The adaptive condition is paired by seed with frozen-learning, memoryless,
signal-blocked, and trace-blocked conditions. Signal and trace interventions
retain their anonymous outputs and energy costs while blocking only reception or
field coupling. This removes the principal energy-cost confound in the earlier
implementation.

## 2.3 Protocol and outcomes

The protocol was fixed in `research/PREREGISTRATION.md`. Pilot seeds 1000–1002
were used for ecological calibration and excluded from inference. Confirmatory
seeds are the independent units. The main ecological endpoint is cumulative net
energy input per agent-step; predictor error is a learning manipulation check.

## 2.4 Statistics

For each paired contrast we report the favorable mean difference, paired effect
size, win rate, a paired bootstrap 95% interval, and a two-sided paired random-
sign test. Benjamini–Hochberg correction is applied across the five fixed
contrasts. Agents and time samples within a seed are not treated as independent.

# 3. Results

Insert the generated `REPORT.md` table and a compact figure derived directly
from `runs.csv`. Report all confirmatory and validity outcomes, not only those
passing a significance threshold.

# 4. Discussion

Interpret supported results as mechanism effects under this model and parameter
regime. Treat unsupported results as null or underpowered. Discuss the designed
energy objective, architectural priors, seed-specific rather than agent-specific
interfaces, absence of empirical input data, sensitivity to ecological settings,
and the inability of behavioral observations to establish private experience.

# 5. Reproducibility and availability

Record the public repository URL, release tag, source commit, archived software
DOI, archived result DOI, protocol hash, and one-command reproduction procedure.

# AI-assistance disclosure

Complete this section from `AI_USAGE.md` only after Henry has personally reviewed,
executed, understood, and edited the AI-assisted materials.

# References

Grimm, V., et al. (2020). The ODD protocol for describing agent-based and other
simulation models: A second update to improve clarity, replication, and
structural realism. *Journal of Artificial Societies and Social Simulation*,
23(2), 7. <https://doi.org/10.18564/jasss.4259>
