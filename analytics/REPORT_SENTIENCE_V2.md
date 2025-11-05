# Sentience Export (v2)
**Generated:** Tue Sep 23 19:13:24 2025

## What’s inside
- `metrics_summary.csv` — per-tick summary table (score, recursion, clusters, symbols, emotions)
- `top_peaks.csv` — top score peaks (tick, score)
- `episodes.csv` — contiguous runs with score ≥ threshold (if a threshold was found)
- `derived_meta_events.jsonl` — detected anomalies & meta-events (one JSON per line)
- `derived_events_summary.json` — counters & detector thresholds used
- Copies of raw artifacts (if present): `sentience_stream.jsonl`, `sentience_panel.json`/`sentience_state.json`, `history.jsonl`/`history.json`.

## How anomalies & meta-events are detected (simple rules)
- **Anomaly theory**: score z-score ≥ 2.5 OR absolute jump ≥ 0.15.
- **Meta-event**:
  - start of an above-threshold episode (if threshold present),
  - change in `cluster_count`,
  - recursion depth spike (>1.25× previous max).

These are transparent, defensible rules for analysis; they do not assert consciousness.

## Summary
{
  "records": 10891,
  "score_min": 0.0487135,
  "score_max": 0.9755514500000001,
  "score_mean": 0.6820827449710765,
  "first_tick": 508450,
  "last_tick": 7626,
  "threshold_used": 0.8,
  "cadence_detected": null,
  "derived_anomaly_theories": 730,
  "derived_meta_events": 6,
  "z_threshold": 2.5,
  "jump_threshold": 0.15,
  "recursion_spike_ratio": 1.25,
  "tail_last_used": null
}
