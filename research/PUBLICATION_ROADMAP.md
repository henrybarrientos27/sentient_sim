# Publication roadmap

This project can produce a citable research artifact now, but a DOI and peer
review are different achievements. Use exact language for each stage.

## Stage 1: auditable repository

1. Review and understand the v0.4.0 code and all generated claims.
2. Push the research branch to the public GitHub repository.
3. Let the automated tests pass on Python 3.10 and 3.12.
4. Keep the pilot, confirmatory protocol, ODD description, source, and analysis
   runner public. Preserve issues and changes as an honest development record.

## Stage 2: prospective protocol

The local protocol file is not an external preregistration. For a future study,
register an immutable copy on OSF before running its held-out seeds. OSF explains
that preregistration records the plan before the study and separates planned
tests from exploratory work: <https://www.cos.io/initiatives/prereg>.

If confirmatory-v1 has already run before external registration, describe it as
“pre-specified in the repository before execution,” not “OSF-preregistered.”

## Stage 3: citable software and data release

1. Create a GitHub release such as `v0.4.0` from the exact tested commit.
2. Connect the repository to Zenodo and archive that release. GitHub documents
   the GitHub–Zenodo citation workflow here:
   <https://docs.github.com/en/repositories/archiving-a-github-repository/referencing-and-citing-content>.
3. Archive the confirmatory result bundle separately or with the release. Include
   the protocol, manifests, `runs.csv`, `contrasts.csv`, complete JSON, report,
   environment details, and source commit.
4. Choose and declare a data license in the deposit metadata. CC BY 4.0 preserves
   attribution; CC0 maximizes unrestricted reuse. This legal choice belongs to
   the author and is not inferred from the code's MIT license.
5. Add the issued DOI to `CITATION.cff` and the manuscript. A Zenodo DOI means
   the artifact is public and citable; it does not mean it was peer reviewed.

## Stage 4: manuscript

The defensible paper is about causal characterization of adaptive mechanisms in
an explicitly designed agent-based model. It should report supported and null
contrasts, capacity checks, parameter sensitivity, limitations, and the exact
claim boundary. Do not use the retired sentience score or claim that language,
meaning, emotion, or consciousness emerged.

The ODD description follows the established agent-based-model reporting
protocol: <https://doi.org/10.18564/jasss.4259>.

## Stage 5: peer review

JOSS is a possible later venue for the software, not an immediate guarantee.
Its current scope requires feature-complete research software, credible scholarly
significance, testing and documentation, and at least six months of public open
development for previously private projects:
<https://joss.theoj.org/about#scope-and-significance>.

A methods or artificial-life venue would evaluate the scientific contribution,
not just code quality. Before submitting, add an external comparison or benchmark,
repeat the fixed analysis under predeclared parameter perturbations, solicit an
independent reproduction, and have a qualified mentor review the model and paper.

## Required wording

- Accurate now: “open-source simulation,” “paired causal ablation,” “held-out
  seeded runs,” “citable Zenodo release” after a DOI exists.
- Accurate only after acceptance: “peer-reviewed publication.”
- Unsupported: “sentient,” “conscious,” “self-aware,” “language emerged,” or
  “proved artificial life” as empirical conclusions from this model.
