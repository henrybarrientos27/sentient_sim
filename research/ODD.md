# ODD model description

This description follows the Overview, Design concepts, and Details (ODD)
protocol for agent-based models (Grimm et al., 2020,
<https://doi.org/10.18564/jasss.4259>). It describes Sentient Sim v0.4.0.

## 1. Overview

### 1.1 Purpose and patterns

The model is a controlled test bed for asking whether numerical agent capacities
causally affect prediction and ecological performance. Target patterns are
population persistence, resource acquisition, within-lifetime predictive
adaptation, lineage turnover, and any measurable benefit from recurrent state,
local signaling, or writable environmental traces.

The word “sentient” is a historical project name. The model neither implements
nor measures a scientific criterion for consciousness.

### 1.2 Entities, state variables, and scales

The world is a 32 by 32 toroidal continuous plane overlaid by two cell grids: a
bounded renewable resource and a signed writable trace. One tick is an abstract
update interval and has no mapping to physical time.

Each agent has an identifier, parent and root-lineage identifiers, generation,
2-D position and velocity, bounded energy, age, recurrent hidden vector,
previous action, emitted signal, predictor and actor parameters, learning-rate
tendencies, and finite diagnostic traces. Agents have no names, words, emotion
labels, roles, or symbolic instructions.

World state includes the fields, population, random-generator state, interface
permutations, births, deaths, cumulative agent-ticks, resource extraction,
energy income and cost, and population-cap exposure.

### 1.3 Process overview and scheduling

Each tick executes in this order:

1. Regenerate the resource field and decay the writable trace.
2. Build occupancy and local-neighbor caches from pre-movement positions.
3. For every extant agent, form an observation, apply online learning from its
   previous transition, update recurrent state, and sample an action.
4. Apply all actions in a randomly permuted agent order: move, extract resource,
   write trace, emit a signal, pay costs, and record energy change.
5. Allow energy-qualified agents to reproduce probabilistically until the
   computational safety cap is reached.
6. Remove agents whose energy is non-finite or non-positive.

All decisions in a tick see signals emitted during the preceding tick. Actions
are chosen before any current-tick action is applied.

## 2. Design concepts

### Basic principles

The model combines local resource competition, recurrent controllers,
self-supervised one-step prediction, stochastic policy learning, inheritance,
and mutation. These are strong, explicit design priors—not evidence that the
system is assumption-free.

### Emergence

No target coordination pattern, message dictionary, trail type, social role,
or lineage strategy is supplied. A pattern is described as emergent only when it
appears in measured dynamics and survives a matched causal intervention. Visual
complexity alone is not evidence.

### Adaptation and objectives

Within-lifetime parameter updates use experienced energy change plus a small
learning-progress term. Across generations, controllers are inherited with
mutation. Persistence pressure is therefore designed into the model; claims are
limited to adaptation under this objective.

### Learning and prediction

An agent predicts its next anonymous observation from current hidden state and
action. Predictor weights receive a bounded delta update. Predictor residual is
back-projected into input, recurrent, and feedback weights. The actor uses a
continuous REINFORCE-style update with a moving reward baseline.

### Sensing

Raw observations contain 3 by 3 local patches of resource, occupancy, and trace;
five internal or kinetic scalars; and a distance-weighted incoming signal vector.
A seed-specific permutation and sign mask hide host-channel ordering. This does
not remove architectural priors or prevent an agent from learning correlations.

### Interaction and collectives

Agents interact only through resource competition, local continuous signals,
the writable trace, and reproduction. There is no declared group entity.

### Stochasticity

A NumPy pseudorandom generator controls initialization, interface masks, action
noise, update order, reproduction, offspring placement, and mutation. The full
generator state is checkpointed. Identical seeds are paired across conditions.

### Observation

Measurements are descriptive and remain separate. No composite “sentience
score” is calculated. Confirmatory inference uses seed-level endpoints; agents
and repeated time samples are not counted as independent observations.

The `memoryless` intervention removes recurrent hidden-state carryover, not all
temporally informative inputs: age, velocity, energy change, and previous action
remain observable. Paired seeds match initialization, but pseudorandom streams
can diverge after an intervention changes behavior, births, or deaths.

## 3. Details

### 3.1 Initialization

The resource field begins as uniform random noise smoothed by five nearest-
neighbor averaging passes, rescaled to 25–100% of configured capacity. Trace is
zero. Root agents receive uniform random positions, zero velocity and recurrent
state, configured initial energy, random bounded controller matrices, and shared
seed-specific interface transforms.

### 3.2 Input data

The model consumes no empirical input data. A JSON configuration, code version,
and pseudorandom seed fully determine a fresh run.

### 3.3 Submodels

Resource regeneration is
`R <- clip(R + regen * (capacity - R), 0, capacity)`. Trace decay is
`T <- (1 - decay) * T`.

The recurrent update is a hyperbolic tangent of anonymous observation input,
prior hidden state, previous-action feedback, and bias. The actor mean is a
bounded linear projection of hidden state; Gaussian exploration is added and
clipped to [-1, 1]. A hidden permutation maps outputs to two velocity channels,
resource coupling, trace coupling, and continuous signal channels.

Resource extraction is limited by local availability and positive resource
coupling. Energy income is extraction times harvest efficiency. Costs include a
basal term plus movement magnitude, emitted-signal magnitude, and absolute trace
command. Signal-blocked and trace-blocked controls retain these output costs.

An agent above the reproduction threshold reproduces with a fixed probability.
It transfers a fixed fraction of its energy to its child. Controller arrays are
copied with independent Gaussian mutation, and two scalar learning tendencies
mutate within fixed bounds.

Exact parameter values for the confirmatory study are stored in
`research/confirmatory_config_v1.json`; checkpoint serialization stores all
state needed for exact continuation.
