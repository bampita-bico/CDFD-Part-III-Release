# Reproducibility

Run commands from the release root:

```bash
cd /home/bampita/Projects/CDFD/CDFD-Part-III-Release
```

## Python Environment

Use the workspace virtual environment when available:

```bash
/home/bampita/Projects/CDFD/.venv/bin/python -m pip install -r requirements.txt
```

or create the conda environment:

```bash
conda env create -f environment.yml
conda activate cdfd-part-iii-public
```

## Regenerate Public Diagnostics

```bash
/home/bampita/Projects/CDFD/.venv/bin/python supplementary/run_biology_discovery.py
```

The command writes release-local outputs under `outputs/` for Papers 01-17. It
does not write to the root workspace `experiments/outputs` directory.

The runner calls the complete public diagnostic set:

```bash
/home/bampita/Projects/CDFD/.venv/bin/python supplementary/supplementary_afl_01.py
/home/bampita/Projects/CDFD/.venv/bin/python supplementary/supplementary_afl_02.py
/home/bampita/Projects/CDFD/.venv/bin/python supplementary/supplementary_afl_03.py
/home/bampita/Projects/CDFD/.venv/bin/python supplementary/supplementary_afl_04.py
/home/bampita/Projects/CDFD/.venv/bin/python supplementary/AFL_Metabolism_Verification.py
/home/bampita/Projects/CDFD/.venv/bin/python supplementary/supplementary_afl_06.py
/home/bampita/Projects/CDFD/.venv/bin/python supplementary/AFL_Biological_Mujjabi_Tests.py
/home/bampita/Projects/CDFD/.venv/bin/python supplementary/Pharmacological_Synergy_Engine.py
/home/bampita/Projects/CDFD/.venv/bin/python supplementary/supplementary_afl_11.py
/home/bampita/Projects/CDFD/.venv/bin/python supplementary/supplementary_afl_12.py
/home/bampita/Projects/CDFD/.venv/bin/python supplementary/supplementary_afl_13.py
/home/bampita/Projects/CDFD/.venv/bin/python supplementary/supplementary_afl_14.py
/home/bampita/Projects/CDFD/.venv/bin/python supplementary/supplementary_afl_15.py
/home/bampita/Projects/CDFD/.venv/bin/python supplementary/AFL_Biomarker_Horizon_Summary.py
```

## Build Interactive Panels

```bash
/home/bampita/Projects/CDFD/.venv/bin/python make_interactive_panels.py
```

This creates `outputs/interactive_index.html` plus simple per-paper panels where
generated outputs exist.

## Compile PDFs

If `latexmk` is installed, compile the 17-paper spine into a temporary build
directory:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=/tmp/cdfd_partiii_build_next papers/*.tex
```

The manuscripts use `natbib`; run BibTeX through `latexmk` rather than a single
`pdflatex` pass. The verified upgrade build produced 17 PDFs under
`/tmp/cdfd_partiii_build_next/`.

After a clean build, refresh the release PDF folder:

```bash
cp /tmp/cdfd_partiii_build_next/*.pdf PDFs/
```

## Output Interpretation

The outputs are toy model diagnostics. They are useful for checking internal
consistency of the CDFD/AFL notation and runtime links. They are not clinical
validation, medical advice, diagnostic devices, or clinical guidance.
