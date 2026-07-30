# Core Python API

The command line is the supported path for complete recorded studies. The Python
API is useful for new diagnostics, controlled extensions, and tests.

## `SimulationConfig`

```python
from sentient_sim import SimulationConfig

config = SimulationConfig(seed=7, initial_agents=48, max_agents=128)
config.validate()
```

`SimulationConfig` contains every world, energy, reproduction, controller, and
mechanism parameter. `to_dict()` returns a JSON-compatible mapping and
`from_dict(mapping)` ignores unknown keys but validates recognized values.

Changing a mechanism flag changes the causal condition:

- `learning_enabled=False` blocks all online weight updates;
- `recurrent_memory=False` zeros hidden carryover before decisions;
- `signaling_enabled=False` blocks delivery but retains signal outputs and costs;
- `environmental_memory_enabled=False` blocks trace read/write coupling but
  retains trace-command costs.

## `World`

```python
from sentient_sim import SimulationConfig, World
from sentient_sim.metrics import measure

world = World(SimulationConfig(seed=7))
for _ in range(100):
    world.step()
print(measure(world))
```

`World(config)` initializes a deterministic seeded model. `step()` advances one
complete scheduled tick. `to_state()` returns checkpoint state;
`World.from_state(state)` restores v2 or v3 state. Attributes such as `agents`,
`resource`, and `trace` are public for analysis but mutations can invalidate
model assumptions and should be documented as protocol changes.

## Measurements

```python
from sentient_sim.metrics import measure

record = measure(world)
```

`measure(world)` returns separate descriptive values for demographics, energy,
resource state, prediction, recurrent dependence, signal response, traces,
coordination, behavior, and lineages. It deliberately returns no composite
sentience or emergence score.

## Checkpoints and recorded runs

```python
from pathlib import Path
from sentient_sim.runner import load_checkpoint, run_world, save_checkpoint

save_checkpoint(world, Path("checkpoint.json.gz"))
restored = load_checkpoint(Path("checkpoint.json.gz"))

summary = run_world(
    config=SimulationConfig(seed=7),
    ticks=1000,
    output_directory=Path("runs/seed-7"),
    metrics_every=10,
    checkpoint_every=500,
)
```

`run_world` writes a manifest before simulation, append-only metrics during the
run, periodic checkpoints, a final checkpoint, and a summary. A `resume` path
continues the exact saved world; the `ticks` argument always means additional
ticks.

## Paired ablation study

```python
from pathlib import Path
from sentient_sim.experiment import run_ablation_experiment

results = run_ablation_experiment(
    config=SimulationConfig(seed=2000, initial_agents=48, max_agents=128),
    ticks=3000,
    output_directory=Path("experiments/example"),
    replicates=30,
    workers=3,
)
```

The function runs the five fixed v1 conditions over consecutive seeds. It caches
each finished unit, binds cache reuse to protocol and package-source hashes, and
returns the same structure written to `experiment.json`. A seed is the unit of
replication.

For a publication campaign, use the command line with a committed JSON
configuration so the invocation, configuration, and output directory are
auditable together.
