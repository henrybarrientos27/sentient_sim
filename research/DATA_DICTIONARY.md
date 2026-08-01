# Result data dictionary

## `runs.csv`

Each row is one independent seed-condition run. Statistical replication occurs
at the seed level; within-run agents and time samples are not extra rows.

- `seed`: pseudorandom seed paired across all conditions.
- `condition`: `adaptive`, `frozen`, `memoryless`, `signal_blocked`, or
  `trace_blocked`.
- `ticks_completed`: ticks reached before the fixed horizon or extinction.
- `extinct`: whether no agents remained.
- `population`: latter-half mean living population.
- `population_exposure`: cumulative agent-ticks divided by completed ticks.
- `capacity_fraction`: latter-half mean population divided by safety cap.
- `capacity_tick_fraction`: fraction of ticks beginning at the safety cap.
- `mean_energy`: latter-half mean energy over living agents.
- `mean_reward`: latter-half mean realized one-tick energy change.
- `prediction_error`: latter-half mean one-step squared prediction error.
- `memory_dependence`: policy-output difference under a zero-recurrent-state
  counterfactual; this is not a psychological memory measurement.
- `signal_influence`: policy-output difference when received signals are set to
  zero while holding the controller fixed.
- `signal_outcome_correlation`: absolute correlation between incoming-signal
  magnitude and subsequent energy change over the bounded diagnostic window.
- `environmental_trace_power`: latter-half mean absolute writable-field value.
- `environmental_trace_structure`: latter-half spatial standard deviation of
  the writable field.
- `local_coordination`: latter-half mean rescaled velocity cosine similarity
  among nearby moving pairs.
- `behavioral_diversity`: latter-half mean across-channel action dispersion.
- `lineage_entropy`: normalized entropy of represented root lineages.
- `root_lineage_survival`: final fraction of initial root lineages represented.
- `max_generation`: latter-half mean of the maximum living generation.
- `harvest_energy_per_agent_step`: cumulative resource-derived energy divided
  by cumulative agent-ticks.
- `energy_cost_per_agent_step`: cumulative basal and action costs divided by
  cumulative agent-ticks.
- `net_energy_input_per_agent_step`: cumulative harvested energy minus costs,
  divided by cumulative agent-ticks; the primary ecological endpoint.
- `instant_harvest_energy_per_agent`: latter-half mean current-tick harvested
  energy per acting agent.
- `instant_energy_cost_per_agent`: latter-half mean current-tick cost per acting
  agent.
- `birth_rate_per_1000_agent_steps`: cumulative births per 1,000 agent-ticks.
- `death_rate_per_1000_agent_steps`: cumulative deaths per 1,000 agent-ticks.

Unless marked cumulative or final, endpoints are arithmetic means over the
latter half of the target 100 evenly spaced measurements.

## `contrasts.csv`

Each row is one fixed adaptive-versus-control paired contrast.

- `id`, `control`, `metric`, `role`: preregistered contrast specification.
- `higher_is_better`: direction before conversion to favorable differences.
- `n`: number of paired seeds.
- `adaptive_mean`, `control_mean`: unpaired descriptive condition means over the
  same paired seeds.
- `mean_favorable_difference`: paired difference oriented so positive favors
  adaptive.
- `ci95_low`, `ci95_high`: deterministic paired-bootstrap percentile interval.
- `paired_effect_size_dz`: favorable mean difference divided by the standard
  deviation of paired differences.
- `win_rate`: fraction of seeds with a strictly positive favorable difference.
- `two_sided_randomization_p`: paired random-sign Monte Carlo p-value.
- `bh_q`: Benjamini–Hochberg adjusted value across the five fixed contrasts.
- `supports_preregistered_direction`: true only when `bh_q < 0.05`, the mean is
  positive, and the confidence interval is wholly above zero.

The word `preregistered` in the machine-generated column name refers to the
fixed local protocol. The campaign was not registered externally before
execution; publication text must use “pre-specified.”
