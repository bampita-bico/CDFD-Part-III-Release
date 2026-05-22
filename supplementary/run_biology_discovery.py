"""Run all active Part III release-local diagnostics."""
from __future__ import annotations

from AFL_Biological_Mujjabi_Tests import main as run_biology_tests
from AFL_Biomarker_Horizon_Summary import main as run_biomarker_horizon
from AFL_Metabolism_Verification import main as run_metabolism
from Pharmacological_Synergy_Engine import main as run_pharmacology
from partiii_runtime import OUTPUTS, write_json
from supplementary_afl_01 import main as run_paper_01
from supplementary_afl_02 import main as run_paper_02
from supplementary_afl_03 import main as run_paper_03
from supplementary_afl_04 import main as run_paper_04
from supplementary_afl_06 import main as run_paper_06
from supplementary_afl_11 import main as run_paper_11
from supplementary_afl_12 import main as run_paper_12
from supplementary_afl_13 import main as run_paper_13
from supplementary_afl_14 import main as run_paper_14
from supplementary_afl_15 import main as run_paper_15


def main() -> dict[str, object]:
    OUTPUTS.mkdir(exist_ok=True)
    payload: dict[str, object] = {}
    run_paper_01()
    run_paper_02()
    run_paper_03()
    run_paper_04()
    payload.update(run_metabolism())
    run_paper_06()
    payload.update(run_biology_tests())
    payload.update(run_pharmacology())
    run_paper_11()
    run_paper_12()
    run_paper_13()
    run_paper_14()
    run_paper_15()
    payload.update(run_biomarker_horizon())
    payload["status"] = {
        "clinical_status": "toy diagnostics only; not clinical validation",
        "generated_paper_folders": [f"paper_{i:02d}" for i in range(1, 18)],
        "output_boundary": "all generated files are release-local under CDFD-Part-III-Release/outputs",
    }
    write_json(OUTPUTS / "biology_discoveries.json", payload)
    return payload


if __name__ == "__main__":
    result = main()
    print("Wrote Part III release diagnostics to outputs/")
    print(", ".join(sorted(k for k in result if k.startswith("paper_"))))
