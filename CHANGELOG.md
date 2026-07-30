# Changelog

## 0.4.0 — 2026-07-29

### Research design

- Replace energy-confounded signal and trace controls with cost-matched causal
  interventions.
- Separate pilot seeds from 30 held-out confirmatory seeds.
- Add a prospective protocol with fixed hypotheses, endpoints, stopping rule,
  failure handling, multiplicity correction, and claim boundary.
- Add an ODD model specification and calibrated resource-limited configuration.

### Analysis and provenance

- Treat the random seed as the independent unit and preserve seed pairing.
- Add paired bootstrap intervals, random-sign tests, paired effect sizes, win
  rates, and Benjamini–Hochberg correction.
- Add ecological exposure, resource, cost, demographic, lineage, and population-
  cap diagnostics.
- Save every seed-condition result immediately and reject resume attempts with a
  different protocol or source hash.
- Record source hash, Git revision, runtime versions, operating system, and UTC
  timestamps.
- Add analysis-ready CSV exports, an SVG figure generator, and a validated
  archival result packager.

### Software quality

- Expand deterministic, migration, control-matching, and cache-safety tests.
- Add Python 3.10/3.12 continuous integration, package metadata, citation
  metadata, an AI-assistance disclosure draft, and a publication roadmap.
- Read legacy v2 checkpoints while writing v3 checkpoints with cumulative
  ecological counters.

## 0.3.0 — 2026-07-22

- Replace the retired rule-based prototype with anonymous numerical agents,
  recurrent state, predictive and policy learning, mutation, local signaling,
  writable traces, checkpoints, and initial mechanism ablations.
