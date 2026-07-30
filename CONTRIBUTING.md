# Contributing

Contributions that improve correctness, reproducibility, performance,
documentation, or controlled experimental design are welcome.

## Development check

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
```

Pull requests should explain the mechanism changed, add or update tests, and
state whether checkpoints or protocol hashes are affected. Do not commit
generated runs to the source tree.

## Scientific integrity

- Preserve the distinction between exploratory pilot seeds and held-out tests.
- Do not tune parameters on confirmatory outcomes and then report those outcomes
  as confirmatory.
- Treat seeds—not agents or time samples—as independent replicates.
- Report null results, extinctions, cap exposure, failed checks, and deviations.
- Do not describe a continuous signal as language without a pre-specified,
  task-grounded semantic test and a causal communication benefit.
- Do not use simulation behavior as evidence of consciousness or subjective
  experience.
- Disclose material AI assistance according to the target venue's policy.

Bug reports should include the Git revision, source and protocol hashes when
available, Python and NumPy versions, exact command, seed, and smallest artifact
needed to reproduce the issue.
