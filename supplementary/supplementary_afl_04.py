"""
Supplementary — AFL Part III Paper 04
Adaptive Flux Limitation in Mainstream Systems Medicine: Metabolic Comorbidity Matrix

Toy scenarios across metabolic comorbidity clusters aligned with ADA 2026 and
cardiovascular-kidney-metabolic syndrome framing. Each scenario varies Phi, C,
and M_s to represent different clinical burden states.

All entries are candidate AFL translations, not validated clinical measurements.
Standard care guidelines take precedence over any AFL interpretation.

Outputs: outputs/paper_04/
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from partiii_runtime import ensure_output, euler_step, operating_ratio, regime_label, safe_plot, write_csv, write_json

DT = 0.05
STEPS = 500
ALPHA = 0.07
BETA = 0.025
KAPPA_S = 0.05
D_M = 0.01

# Comorbidity scenarios: (label, Phi0, C0, M_s0, note)
SCENARIOS = [
    ("Healthy",             2.0, 0.6, 0.2, "baseline — no significant burden"),
    ("Obesity",             2.5, 1.2, 0.5, "increased metabolic flux, adipose constraint"),
    ("T2DM",                2.0, 1.8, 0.7, "insulin resistance; ADA 2026 category"),
    ("CKD-Metabolic",       1.5, 2.5, 1.0, "CKD-MBD + metabolic burden"),
    ("Heart failure",       1.2, 2.8, 1.2, "reduced cardiac Phi, high vascular C"),
    ("MASLD",               2.2, 2.0, 0.9, "metabolic liver disease; hepatic C load"),
    ("CKM Syndrome",        1.2, 3.5, 1.5, "cardiovascular-kidney-metabolic overlap"),
    ("Frailty (elderly)",   0.8, 3.0, 1.8, "reduced Phi, high accumulated C and M_s"),
    ("Pregnancy (complex)", 3.0, 1.8, 0.6, "elevated Phi demand, gestational constraints"),
]

# CKD-MBD cascade: FGF23/PTH/phosphate as early constraint signals
CKD_MBD_STAGES = [
    {"stage": "G1", "gfr_frac": 0.95, "FGF23": 1.0, "PTH": 1.0, "phos_proxy": 1.00},
    {"stage": "G2", "gfr_frac": 0.70, "FGF23": 1.5, "PTH": 1.1, "phos_proxy": 1.02},
    {"stage": "G3a","gfr_frac": 0.45, "FGF23": 2.5, "PTH": 1.5, "phos_proxy": 1.05},
    {"stage": "G3b","gfr_frac": 0.35, "FGF23": 4.0, "PTH": 2.0, "phos_proxy": 1.10},
    {"stage": "G4", "gfr_frac": 0.20, "FGF23": 6.0, "PTH": 3.5, "phos_proxy": 1.30},
    {"stage": "G5", "gfr_frac": 0.08, "FGF23": 10.0,"PTH": 6.0, "phos_proxy": 1.70},
]


def _sim(phi0: float, c0: float, ms0: float) -> dict:
    phi, c, s, ms = phi0, c0, 1.0, ms0
    psi_h = []
    for _ in range(STEPS):
        c, s, ms = euler_step(phi, c, s, ms, ALPHA, BETA, KAPPA_S, D_M, DT)
        psi_h.append(operating_ratio(phi, c, s, ms))
    return {"final_psi": psi_h[-1], "psi_history": psi_h}


def main() -> None:
    out = ensure_output("paper_04")

    rows = []
    histories = {}
    for (label, phi0, c0, ms0, note) in SCENARIOS:
        res = _sim(phi0, c0, ms0)
        rows.append({
            "scenario": label,
            "Phi0": phi0, "C0": c0, "Ms0": ms0,
            "final_psi": round(res["final_psi"], 4),
            "regime": regime_label(res["final_psi"]),
            "note": note,
            "claim_status": "candidate AFL translation — not validated",
        })
        histories[label] = res["psi_history"]

    write_csv(out / "metabolic_tissues.csv", rows)

    # CKD-MBD bridge table
    ckd_rows = []
    for stage in CKD_MBD_STAGES:
        c_renal = 1.0 / max(stage["gfr_frac"], 0.01)
        psi_phos = operating_ratio(1.0, c_renal / max(stage["FGF23"], 0.1), 1.0, 0.5)
        ckd_rows.append({
            **stage,
            "C_renal_proxy": round(c_renal, 3),
            "psi_phosphate": round(psi_phos, 3),
            "constraint_state": "compensated" if stage["FGF23"] > 1.2 and stage["phos_proxy"] < 1.15 else "decompensated",
        })
    write_csv(out / "ckd_mbd_cascade.csv", ckd_rows)

    write_json(out / "summary.json", {
        "paper": "04",
        "title": "Adaptive Flux Limitation in Mainstream Systems Medicine",
        "scenarios": len(rows),
        "claim_status": "candidate AFL translations — not validated measurements",
        "guideline_note": "ADA Standards of Care 2026; KDIGO 2024 CKD. When AFL disagrees with standard care, standard care takes precedence.",
        "falsification": (
            "If comorbidity burden is fully explained by additive risk scores without "
            "interactive constraint dynamics, AFL cross-domain coupling adds no value."
        ),
    })

    plt = safe_plot()
    if plt is not None:
        t = np.arange(STEPS) * DT
        fig, axes = plt.subplots(1, 2, figsize=(15, 5), constrained_layout=True)

        ax = axes[0]
        colors = plt.cm.tab10(np.linspace(0, 1, len(SCENARIOS)))
        for (label, *_), col in zip(SCENARIOS, colors):
            ax.plot(t, histories[label], lw=1.2, label=label, color=col)
        ax.axhline(0.8, color="grey", lw=0.8, ls=":")
        ax.axhline(1.2, color="grey", lw=0.8, ls=":")
        ax.set_xlabel("Time (toy)"); ax.set_ylabel("Ψ_s (toy)")
        ax.set_title("Metabolic Comorbidity Matrix: Psi_s Trajectories")
        ax.legend(frameon=False, fontsize=6)

        ax = axes[1]
        stages = [r["stage"] for r in ckd_rows]
        psi_vals = [r["psi_phosphate"] for r in ckd_rows]
        fgf_vals = [r["FGF23"] for r in ckd_rows]
        x = np.arange(len(stages))
        ax.bar(x, psi_vals, color="#1f77b4", alpha=0.8, label="Psi_phosphate (toy)")
        ax2 = ax.twinx()
        ax2.plot(x, fgf_vals, color="#d62728", marker="o", lw=1.4, label="FGF23 (toy proxy)")
        ax.set_xticks(x); ax.set_xticklabels(stages)
        ax.set_ylabel("Psi_phosphate", color="#1f77b4")
        ax2.set_ylabel("FGF23 proxy", color="#d62728")
        ax.set_title("CKD-MBD: FGF23 as Early Constraint Signal")

        fig.suptitle("AFL Paper 04 — Toy Diagnostics: Metabolic Comorbidity (not clinical predictions)", fontweight="bold")
        fig.savefig(out / "insulin_resistance_afl.png", dpi=220)
        plt.close(fig)

    print(f"Paper 04 outputs → {out}/")


if __name__ == "__main__":
    main()
