# Confirmatory-v1 protocol deviations and execution audit

## Outcome-affecting deviations

None recorded.

## Pre-execution provenance correction

The frozen research design was committed as `384fc0c`. The first campaign
launch revealed that `git_revision` was null because the provenance helper
looked one directory above the repository. Exactly one seed-condition record had
finished when the issue was identified. Only the manifest, completed-file count,
and process state were inspected; its numerical outcome was not used.

That attempt was stopped and preserved on the server as
`experiments/confirmatory-v1-invalid-provenance`. The helper was corrected and
cached records were additionally bound to the exact package-source hash in
commit `b18257e`. No model dynamics, parameters, endpoints, hypotheses, or
statistical rules changed in that correction.

The authoritative `experiments/confirmatory-v1` campaign began from an empty
directory after `b18257e`. All 150 records in that campaign must share its
protocol and source hashes. The invalid attempt is excluded from every analysis
and archive.

## Interim monitoring

At 15 of 150 authoritative records, an operational monitoring command printed
incomplete per-condition means for net energy and population in addition to the
planned cap and extinction diagnostics. It did not calculate formal paired
contrasts or p-values, and no code, parameter, endpoint, sample size, exclusion,
or stopping decision was changed. All 150 fixed records remained required. This
descriptive look is disclosed so the execution history is complete.

## Registration wording

The protocol was frozen in the local repository before the authoritative held-
out campaign, but it was not placed in an external immutable registry first.
Public descriptions must say “pre-specified before execution” and must not say
“OSF-preregistered.”
