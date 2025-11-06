# Project Emergence  
**Emergence of Emotion-Driven Symbol Compression in a Multi-Agent Simulation**  
Author: Henry Barrientos  
Language: Python

---

## Abstract
In this project, I built a multi-agent simulation in Python to explore whether meaning,
language, or self-modeling could emerge in a system that was not explicitly programmed
for any of those outcomes. Each agent operates using minimal rules: exist, survive, and
interact. No goals relating to language, intention, or emotional understanding were coded.

Unexpectedly, symbolic language *did* emerge — and not randomly.  
When I adjusted the emotional valence of the system (using a VAD emotional model),
the agents reacted by **compressing their vocabulary**.

**Result:**  
As valence increased, agents consistently reduced the size of their symbolic vocabulary.

> On average, vocabulary size compressed by **~34 symbols per +1.0 valence increase.**

This suggests that emotional state can directly influence communication efficiency, even
in a system without semantic understanding or explicit language design. Meaning emerged
from constraints — not from instruction.

---

## 1. Introduction

Emergence is when complex behavior arises from simple rules.

The purpose of *Project Emergence* was to test one question:

> “Can meaning or communication patterns emerge without being programmed?”

The agents were not given:
- goals relating to optimization,
- language templates,
- emotional rules,
- or any notion of self.

They were only given the ability to interact and store symbols.

---

## 2. Method

**Programming language:** Python  
**Number of agents:** variable  
**Emotional model:** VAD (Valence–Arousal–Dominance)

At each timestep:
1. Agents observe neighbors and environment.
2. They generate and transmit symbols.
3. Symbols are stored and weighted based on context.

The simulation logged:
- every message (`sentience_stream.jsonl`)
- long-form behaviors/materialized patterns (`history.json`)
- emotional and vocabulary metrics (`metrics_summary.csv`)

### Measurement
Vocabulary size was defined as the count of unique symbols used over a rolling time window.
Valence was normalized to range \[-1.0, +1.0\].

---

## 3. Results

| Metric | Observation |
|--------|-------------|
| Avg vocabulary drop per +1.0 valence | **~34 symbols** |
| Communication pattern | Language becomes tighter and more efficient |
| Emotional effect | Higher valence → reduced entropy |
ΔVocab ≈ –34 symbols / +1.0 valenc
**Figure 1. Emotional valence vs. vocabulary compression**  
*(Screenshot: `analytics/screenshots/vad_symbol_usage.png`)*

The relationship was consistent across repeated runs.

---

## 4. Interpretation

Higher emotional valence produced **tighter, more efficient communication**.

In other words:
> Emotion → compression → meaning

This parallels Shannon information theory:
systems naturally reduce noise when the “energy state” is higher.

The agents optimized communication without being told to optimize anything.

They weren’t simplifying their language because of a goal.
They simplified because of **pressure**.

Meaning emerged from constraint, not code.

---

## 5. Limitations & Future Work

| Limitation | Planned improvement |
|------------|---------------------|
| No explicit reward model | Add resource economy + survival incentives |
| No embodiment of agents | Add spatial world + tool usage |
| Emotional model external | Shift emotions to agent-internal state |

Future milestone:
> Introduce Theory-of-Mind triggers to see whether agents model **each other**, not just the world.

---

## 6. Conclusion

A simple system of agents, given only the rule to exist, produced:
- symbolic language,
- compression under emotional pressure,
- evidence of self-directed adaptation.

Meaning wasn’t coded.

**It emerged.**
