# Claim Status

This file separates mathematical framing from empirical medical status.

## Established Clinical Background

The papers refer to standard clinical entities such as insulin resistance,
chronic kidney disease, erythropoiesis, inflammation, oncology, pharmacology,
bioelectric regulation, development, microbial resistance, and biomarkers. Those
background concepts should be supported by ordinary biomedical citations.

## Framework Definitions

The following are internal CDFD/AFL definitions:

- `Phi`: flow intensity or driver.
- `C`: constraint or capacity burden.
- `S`: surface responsiveness.
- `M_s`: structural memory or hysteresis.
- `Psi_s`: adaptive operating ratio.

These definitions are release-internal modeling terms, not validated clinical
measurements by themselves.

## Model Diagnostics

The supplementary scripts are toy diagnostics. They check whether the CDFD
runtime can reproduce qualitative behaviors such as saturation, constraint
memory, parasitic drain, boundary-response mismatch, and cross-axis drug
combination logic. They are not clinical trials, diagnostic devices, or
treatment algorithms.

## Candidate Constructs

The Medicine Upgrade adds several named constructs: Constraint Reserve Index
(`CRI`), Constraint Recovery Half-Time (`CRHT`), Multi-Axis Orthogonality Score
(`MAOS`), Boundary Error Score (`BES`), Memory-Locking Index (`MLI`), and
Cross-Organ Constraint Transfer (`COCT`). These are proposed research
constructs only. They require context-of-use definition, analytical validation,
clinical validation, calibration, independent replication, and safety review
before any clinical use.

## Falsification Standard

A Part III claim is stronger when it states:

- the measurable proxy for `Phi`, `C`, `S`, or `M_s`;
- the expected direction of change;
- the clinical or laboratory time scale;
- a condition under which the AFL interpretation would fail;
- how the result differs from standard care or existing physiology.

## Medical Boundary

No manuscript in this archive should be read as medical advice. Any future
clinical use would require ordinary validation: cohort studies, prospective
testing, calibration against accepted biomarkers, safety review, and independent
clinical replication.
