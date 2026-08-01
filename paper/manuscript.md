---
title: "Causal characterization of adaptive mechanisms in a resource-limited multi-agent simulation"
author: "Henry Barrientos"
date: "Public research release — 2026-08-01 (not peer reviewed)"
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

Across 30 held-out paired seeds and 150 planned runs with a 3,000-tick horizon,
online learning lowered one-step prediction error and improved net energy input
per agent-step relative to frozen learning. Recurrent carryover produced a
smaller supported ecological benefit. Neither signal delivery nor writable
trace coupling produced a supported ecological benefit after multiplicity
correction. Nine runs became extinct, all in the frozen condition, and no
condition spent time at the population safety cap. These findings establish
mechanism effects only within the specified model and parameter regime.

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

## 1.1 Related work

The ODD protocol provides a standard structure for making agent-based models
understandable and reproducible (Grimm et al., 2020). Artificial-life research
also cautions that long duration or an increasing designer-chosen metric is not
sufficient to establish open-ended evolution (Hintze, 2019). MODES separates
change, novelty, complexity, and ecological potential rather than collapsing
them into a single label (Dolson et al., 2019). Consistent with those cautions,
this study does not claim open-ended evolution and reports separate observables.

Learning-progress rewards are one operational family of computational intrinsic
motivation (Oudeyer & Kaplan, 2007); here that term denotes a numeric algorithm,
not a psychological state. Work on grounded emergent communication evaluates
signals through their functional role in accomplishing environmental goals
(Mordatch & Abbeel, 2018). The present study applies the same general demand for
causal utility, but its continuous signal vectors are not words and no semantic
or compositional language test is performed.

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

All 150 planned seed-condition runs completed. Table 1 reports the five pre-
specified paired contrasts. Positive differences favor the adaptive condition.

| Contrast | Favorable mean difference | 95% bootstrap CI | Paired dz | BH q | Supported |
|---|---:|---:|---:|---:|:---:|
| Prediction vs frozen | 0.181829 | [0.166414, 0.196341] | 4.235 | <0.0001 | yes |
| Ecological performance vs frozen | 0.002286 | [0.001948, 0.002589] | 2.484 | <0.0001 | yes |
| Ecological performance vs memoryless | 0.000033 | [0.000019, 0.000048] | 0.801 | 0.00047 | yes |
| Ecological performance vs signal blocked | 0.000008 | [-0.000004, 0.000021] | 0.230 | 0.216 | no |
| Ecological performance vs trace blocked | 0.000010 | [-0.000003, 0.000023] | 0.276 | 0.179 | no |

Adaptive one-step prediction error was 0.01359, compared with 0.19542 under
frozen learning. This confirms that the online predictor changed its directly
optimized target; it is a manipulation check rather than independent evidence of
intelligence. Adaptive net energy input per agent-step was 0.0000787, compared
with -0.0022074 under frozen learning. The favorable paired ecological
difference was positive in 28 of 30 seeds. The adaptive-versus-memoryless
ecological difference was positive in 23 of 30 seeds.

The signaling and trace intervals both crossed zero, their adjusted q-values
were 0.216 and 0.179, and each favorable difference occurred in 17 of 30 seeds.
The data therefore do not demonstrate useful communication or useful external
memory under this protocol.

Nine of 30 frozen runs became extinct before tick 3,000. No adaptive,
memoryless, signal-blocked, or trace-blocked run became extinct. Adaptive
populations averaged 57.05 agents over the latter-half window, but population
was not a primary endpoint. No run began a tick at the population safety cap, so
the pre-specified capacity-interference threshold was not exceeded.

# 4. Discussion

The supported contrasts identify mechanism effects under this model and
parameter regime, while the unsupported contrasts remain compatible with either
small effects or insufficient power. The agents' energy objective, learning
rules, sensor and action bandwidth, reproductive process, and ecological physics
are all designed priors. Channel permutation hides host semantics from the
controllers but does not remove those priors. Interfaces are seed-specific
rather than agent-specific, the study uses no empirical environmental input,
and only one calibrated ecological regime was tested. Behavioral observations
from this setting cannot establish subjective or private experience.

The `memoryless` label refers specifically to recurrent hidden-state carryover;
agents still observe age, velocity, current energy change, and their previous
action, so the intervention is not removal of every temporally informative
variable. Pairing matches initialization within a seed, but random streams can
diverge after interventions alter behavior or population size. The ecological
endpoint measures gross harvested energy minus costs and can include harvest
that is lost at the storage cap. Runs are finite, use one calibrated parameter
regime, and do not establish unbounded novelty or complexity. These limitations
bound all generalization.

The strongest non-circular result is that online adaptation changed an
ecological endpoint in addition to its directly trained prediction loss. The
recurrent-state contrast supports a more modest claim: retaining hidden state
improved ecological performance under the model's partially observed dynamics.
The unsupported signal and trace contrasts are equally important. Continuous
outputs, nonzero signal power, or visible trace structure are not sufficient to
claim communication, language, artifact use, or external memory without a
causal performance benefit and semantic tests.

# 5. Reproducibility and availability

The authoritative simulation used commit
`b18257e149f0fc72f5c072520a29c97c004a11ad`, package-source SHA-256
`3c9873da4d7d2031ae6d5e7d8c477742228567dbd15d8bb37d44d5af1914ab77`,
and protocol SHA-256
`64c634e12075c66cad1609381ef324a58bb700df8d4bbd7db30b569de9feb844`.
It ran under Python 3.10.12 and NumPy 2.2.6 on Linux. The complete campaign is
reproduced with:

```bash
sentient-sim experiment \
  --config research/confirmatory_config_v1.json \
  --ticks 3000 \
  --replicates 30 \
  --workers 3 \
  --output experiments/confirmatory-v1
```

The public repository is
<https://github.com/henrybarrientos27/sentient_sim>, and the software release is
<https://github.com/henrybarrientos27/sentient_sim/releases/tag/v0.4.0>. The
complete confirmatory bundle is attached to that release as
`sentient-sim-confirmatory-v1.tar.gz`; its size and SHA-256 identity are recorded
in the accompanying metadata JSON. An archival DOI will be added to the
repository metadata when its permanent record is issued. This public manuscript
is a research release, not a peer-reviewed publication.

# AI-assistance disclosure

OpenAI Codex was used to critique the experimental design, implement and test
cost-matched ablations, build the resumable statistical runner, inspect the
confirmatory outputs, and draft and edit documentation. Codex also performed the
final release consistency checks. Henry Barrientos initiated the project,
directed its goals, and authorized this public release. He did not represent that
he personally inspected every AI-assisted line before v0.4.0. Responsibility for
future journal claims and submission remains with the human author, who must
understand and approve the submitted version. Full details are in `AI_USAGE.md`.

# References

Grimm, V., et al. (2020). The ODD protocol for describing agent-based and other
simulation models: A second update to improve clarity, replication, and
structural realism. *Journal of Artificial Societies and Social Simulation*,
23(2), 7. <https://doi.org/10.18564/jasss.4259>

Dolson, E. L., Vostinar, A. E., Wiser, M. J., & Ofria, C. (2019). The MODES
Toolbox: Measurements of open-ended dynamics in evolving systems. *Artificial
Life*, 25(1), 50–73. <https://doi.org/10.1162/artl_a_00280>

Hintze, A. (2019). Open-endedness for the sake of open-endedness. *Artificial
Life*, 25(2), 198–206. <https://doi.org/10.1162/artl_a_00289>

Mordatch, I., & Abbeel, P. (2018). Emergence of grounded compositional language
in multi-agent populations. *Proceedings of the AAAI Conference on Artificial
Intelligence*, 32(1). <https://doi.org/10.1609/aaai.v32i1.11492>

Oudeyer, P.-Y., & Kaplan, F. (2007). What is intrinsic motivation? A typology of
computational approaches. *Frontiers in Neurorobotics*, 1, 6.
<https://doi.org/10.3389/neuro.12.006.2007>
