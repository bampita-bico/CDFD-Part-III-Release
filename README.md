# CDFD Part III: Adaptive Flux Limitation Biology and Medicine

This release contains the public Part III biology-and-medicine archive for the
Constraint-Driven Flux Dynamics project.

## Author

Steve Bico Mujjabi, MD  
ORCID: https://orcid.org/0009-0001-0556-5516

## Release Naming

CDFD Part III: Adaptive Flux Limitation Biology and Medicine - Constraint-Driven Flux Dynamics

## Keywords

Constraint-Driven Flux Dynamics; CDFD; CDFL; CDFD Runtime; Adaptive Flux
Limitation; AFL; systems biology; network medicine; clinical systems medicine;
systems medicine; computational medicine; bioenergetics; metabolism; insulin
resistance; chronic kidney disease; CKD-MBD; erythropoiesis; inflammation;
immunology; oncology; pharmacology; bioelectric regulation; developmental
biology; evolution; microbial resistance; biomarkers; diagnostics; model
diagnostics; falsification; therapeutic strategy; reproducible research; open
science; preprint.

## GitHub Topics

`cdfd`, `cdfd-runtime`, `cdfl`, `adaptive-flux-limitation`,
`systems-biology`, `network-medicine`, `clinical-systems-medicine`,
`bioenergetics`, `metabolism`, `insulin-resistance`, `chronic-kidney-disease`,
`immunology`, `oncology`, `pharmacology`, `bioelectric-regulation`,
`developmental-biology`, `microbial-resistance`, `biomarkers`,
`reproducible-research`, `open-science`

## Contents

- `papers/` - the 17-paper Part III manuscript spine.
- `CLAIM_STATUS.md`, `MUJJABI_BIOLOGY_LAWS_AND_TESTS.md`, and
  `REPRODUCIBILITY.md` - claim discipline, laws/tests, and rebuild
  instructions.
- `supplementary/` - the public, script-first diagnostic code used for Part III
  runtime checks. The completed suite covers Papers 01-17 through release-local
  scripts and shared `partiii_runtime.py` helpers.
- `outputs/` - generated JSON, CSV, and figure outputs from the supplementary
  scripts, including per-paper interactive panels and an index.
- `figures/` - manuscript figures retained from the current paper set.
- `PDFs/` - release PDFs for the 17-paper manuscript spine.
- `CITATION.cff` and `.zenodo.json` - citation and deposit metadata.
- `requirements.txt` and `environment.yml` - public science-stack dependencies.
- `LICENSE` and `LICENSE_BOUNDARY.md` - archive license and separation from the
  reusable CDFD Runtime.

## Final Part III Architecture

Part III is organized as an Adaptive Flux Limitation clinical systems sequence.
It starts with the AFL principle, expands it across biological domains, then
moves into clinical translation, metabolic disease, renal disease, oncology, immunology,
pharmacology, systems integration, bioelectric regulation, development,
evolution, ecology, microbial resistance, biomarkers, and therapeutic synthesis.

The release is written for medical and scientific readers. It defines symbols
where they are used, separates derivations from clinical interpretation, and
labels toy runtime outputs as model diagnostics rather than clinical validation.

## Review Status

These manuscripts are archived as research/preprint materials and are not peer
reviewed. They are not medical advice, clinical guidelines, diagnostic devices,
or clinical guidance. The supplementary scripts reproduce toy
diagnostics and consistency checks for the CDFD/AFL notation; they do not
establish empirical validation of disease mechanisms or therapeutic strategies.

## Suggested Reading Order

1. `papers/README.md`
2. `CLAIM_STATUS.md`
3. `MUJJABI_BIOLOGY_LAWS_AND_TESTS.md`
4. `REPRODUCIBILITY.md`
5. `outputs/interactive_index.html` after regeneration
6. `PDFs/` after compiling the manuscripts

## Reproducibility

See `REPRODUCIBILITY.md` for rebuild and verification commands. The
active release is script-first. Outputs are included where a paper cites a
generated diagnostic, table, or figure. The completed diagnostic suite now
covers Papers 01-17.

## Public CDFD Runtime

The CDFD Runtime is the reusable implementation target for CDFL, the
flow-constraint-memory language used across the CDFD series. This Part III
release is a scholarly archive: paper-local scripts use selected runtime
modules to reproduce biology and medicine diagnostics, and the archive remains
cited and licensed separately from the runtime itself.

Runtime software DOI:
https://doi.org/10.5281/zenodo.20343160

## Reference Discipline

The release intentionally avoids claiming that runtime outputs validate clinical
disease mechanisms.

## License

This release is licensed under the Creative Commons Attribution 4.0
International License (CC BY 4.0). See `LICENSE` and `LICENSE_BOUNDARY.md`.

## Citation

Mujjabi, S. B. (2026). CDFD Part III: Adaptive Flux Limitation Biology and Medicine -
Constraint-Driven Flux Dynamics. Public preprint archive.

Runtime software cited by the papers:

Mujjabi, S. B. (2026). CDFD Runtime: Constraint-Driven Flux Dynamics and CDFL
Execution Engine. Zenodo.
https://doi.org/10.5281/zenodo.20343160
