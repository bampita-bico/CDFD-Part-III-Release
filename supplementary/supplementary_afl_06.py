"""
Supplementary — AFL Part III Paper 06
Adaptive Flux Limitation in Renal Disease: CKD, Erythropoiesis, and Anaemia

Three toy simulations: (A) CKD staging — GFR as 1/C_renal; FGF23/PTH rise
before frank hyperphosphataemia (KDIGO 2024 CKD framing); (B) dialysis
oscillation — episodic C modulation with inter-session rebound; (C) multi-
component erythropoietic constraint across CKD stages with ESA resistance proxy.

All outputs are candidate AFL translations, not validated clinical measurements.
Anchor references: KDIGO 2024 CKD Guideline.

Outputs: outputs/paper_06/
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from partiii_runtime import ensure_output, operating_ratio, regime_label, safe_plot, write_csv, write_json

DT = 0.05
KAPPA_S = 0.05
D_M = 0.01

# Erythropoiesis scenarios: (label, S_EPO, C_Fe, C_inflam, C_uraemia, C_marrow)
ERYTHRO_SCENARIOS = [
    ("G1 healthy",   2.0, 0.5, 0.2, 0.3, 0.5),
    ("G2 CKD",       1.8, 0.8, 0.5, 0.6, 0.6),
    ("G3 CKD",       1.4, 1.2, 1.0, 1.0, 0.8),
    ("G4 CKD",       1.0, 1.8, 1.5, 1.5, 1.0),
    ("G5/dialysis",  0.6, 2.5, 2.0, 2.0, 1.2),
    ("G5 + ESA",     3.0, 2.5, 2.0, 2.0, 1.2),
    ("G5 multi-Rx",  3.0, 1.0, 0.8, 1.8, 0.9),
]


def ckd_progression_sim(steps: int = 600) -> dict:
    """Progressive CKD with FGF23 compensation; KDIGO 2024 stage anchors."""
    J_phos = 1.0
    C_renal = 1.0
    FGF23 = 1.0
    PTH = 1.0
    S = 1.0
    M_s = 0.1
    serum_phos = 1.0
    rows = []
    for i in range(steps):
        C_renal += DT * 0.003
        gfr_est = 1.0 / max(C_renal, 1e-9)
        FGF23 = 1.0 + 2.0 * max(0.0, 1.0 - gfr_est)
        eff_C = C_renal / max(FGF23, 1e-9)
        psi = operating_ratio(J_phos, eff_C, S, M_s)
        M_s = max(M_s + DT * np.clip(J_phos * S - D_M * M_s, -10.0, 10.0), 0.0)
        S = max(S + DT * np.clip(KAPPA_S * (psi - S), -10.0, 10.0), 0.01)
        serum_phos = 1.0 + 0.8 * max(0.0, 1.0 - gfr_est - 0.5)
        if psi > 1.1:
            PTH += DT * 0.3 * (psi - 1.1)
        else:
            PTH = max(PTH - DT * 0.1, 1.0)
        C_renal = max(C_renal + DT * (0.06 * abs(psi - 1.0) - 0.02 * C_renal), 1.0)
        rows.append({
            "step": i, "t": round(i * DT, 3),
            "gfr_proxy": round(gfr_est * 90, 1),
            "FGF23": round(FGF23, 3), "PTH": round(PTH, 3),
            "serum_phos_proxy": round(serum_phos, 3),
            "psi": round(psi, 4),
            "constraint_state": "P-EXCESS" if psi > 1.1 else "BUFFERED",
        })
    return {"rows": rows}


def dialysis_sim(sessions: int = 5, intra_dur: int = 60, inter_dur: int = 120) -> dict:
    C_high, C_post = 5.0, 2.0
    J, S, M_s = 1.0, 1.0, 0.1
    rows = []
    step = 0
    for _ in range(sessions):
        for k in range(inter_dur):
            C_cur = C_post + C_high * (1.0 - np.exp(-0.03 * k))
            psi = operating_ratio(J, C_cur, S, M_s)
            M_s = max(M_s + DT * np.clip(J * S - D_M * M_s, -10.0, 10.0), 0.0)
            S = max(S + DT * np.clip(KAPPA_S * (psi - S), -10.0, 10.0), 0.01)
            rows.append({"step": step, "phase": "inter-session", "C_renal": round(C_cur, 4), "psi": round(psi, 4)})
            step += 1
        for k in range(intra_dur):
            C_cur = max(C_high - (C_high - C_post) * (k / intra_dur), C_post)
            psi = operating_ratio(J, C_cur, S, M_s)
            M_s = max(M_s + DT * np.clip(J * S - D_M * M_s, -10.0, 10.0), 0.0)
            S = max(S + DT * np.clip(KAPPA_S * (psi - S), -10.0, 10.0), 0.01)
            rows.append({"step": step, "phase": "intra-session", "C_renal": round(C_cur, 4), "psi": round(psi, 4)})
            step += 1
    return {"rows": rows}


def erythro_sim(S_EPO: float, C_Fe: float, C_inflam: float, C_uraemia: float, C_marrow: float, steps: int = 400) -> dict:
    Phi = 1.0
    C = max(C_Fe + C_inflam + C_uraemia + C_marrow, 1e-12)
    S, M_s = 1.0, 0.1
    psi_h = []
    for _ in range(steps):
        dPhi = S_EPO * S - Phi * C
        Phi = np.clip(Phi + DT * dPhi, 0.0, 100.0)
        C = max(C + DT * (0.05 * abs(dPhi) - 0.02 * C), 1e-12)
        psi = operating_ratio(Phi, C, S, M_s)
        M_s = max(M_s + DT * np.clip(Phi * S - D_M * M_s, -10.0, 10.0), 0.0)
        S = max(S + DT * np.clip(KAPPA_S * (psi - S), -10.0, 10.0), 0.01)
        psi_h.append(psi)
    eri_proxy = C / max(S_EPO, 1e-9)
    return {"final_psi": psi_h[-1], "eri_proxy": eri_proxy, "final_phi": Phi, "final_C": C}


def main() -> None:
    out = ensure_output("paper_06")

    ckd = ckd_progression_sim()
    dial = dialysis_sim()

    erythro_rows = []
    for (label, epo, cfe, cinfl, cura, cmar) in ERYTHRO_SCENARIOS:
        res = erythro_sim(epo, cfe, cinfl, cura, cmar)
        erythro_rows.append({
            "scenario": label,
            "S_EPO": epo, "C_Fe": cfe, "C_inflam": cinfl,
            "C_uraemia": cura, "C_marrow": cmar,
            "C_total": round(cfe + cinfl + cura + cmar, 2),
            "final_psi": round(res["final_psi"], 4),
            "eri_proxy": round(res["eri_proxy"], 4),
            "regime": regime_label(res["final_psi"]),
            "claim_status": "candidate ESA resistance proxy — not validated",
        })

    write_csv(out / "ckd_cascade.csv", ckd["rows"])
    write_csv(out / "dialysis_oscillation.csv", dial["rows"])
    write_csv(out / "erythropoiesis_constraints.csv", erythro_rows)

    write_json(out / "summary.json", {
        "paper": "06",
        "title": "Adaptive Flux Limitation in Renal Disease",
        "scenarios": {
            "ckd_stages": 6,
            "dialysis_sessions": 5,
            "erythro_scenarios": len(erythro_rows),
        },
        "claim_status": "toy diagnostic — candidate validation target",
        "guideline_anchor": "KDIGO 2024 CKD Guideline (eGFR staging, albuminuria, CKD-MBD, complications)",
        "validation_targets": [
            "Longitudinal eGFR slope vs FGF23/PTH trajectory",
            "Urine albumin-creatinine ratio as C_renal early signal",
            "ESA resistance index vs iron/inflammatory markers",
        ],
        "falsification": (
            "If FGF23 rise does not precede serum phosphate elevation in longitudinal "
            "CKD cohort data, the compensation framing does not hold."
        ),
    })

    plt = safe_plot()
    if plt is not None:
        t_ckd = np.array([r["t"] for r in ckd["rows"]])
        t_dial = np.arange(len(dial["rows"]))
        fig, axes = plt.subplots(1, 3, figsize=(17, 4.5), constrained_layout=True)

        ax = axes[0]
        ax2 = ax.twinx()
        ax.plot(t_ckd, [r["psi"] for r in ckd["rows"]], color="#1f77b4", lw=1.5, label="Psi_s")
        ax2.plot(t_ckd, [r["FGF23"] for r in ckd["rows"]], color="#ff7f0e", lw=1.3, ls="--", label="FGF23")
        ax2.plot(t_ckd, [r["serum_phos_proxy"] for r in ckd["rows"]], color="#2ca02c", lw=1.2, ls=":", label="Serum P~")
        ax.axhline(1.1, color="grey", lw=0.8, ls=":")
        ax.set_xlabel("Time (CKD progression, toy)"); ax.set_ylabel("Psi_s", color="#1f77b4")
        ax2.set_ylabel("FGF23 / Serum P (toy)", color="#ff7f0e")
        ax.set_title("CKD: FGF23 compensates before P rises")
        ax.legend(frameon=False, fontsize=7); ax2.legend(frameon=False, fontsize=7, loc="center right")

        ax = axes[1]
        ax.plot(t_dial, [r["C_renal"] for r in dial["rows"]], color="#9467bd", lw=1.3, label="C_renal")
        ax.set_xlabel("Steps"); ax.set_ylabel("C_renal (toy)")
        ax.set_title("Dialysis: C_renal Oscillation"); ax.legend(frameon=False, fontsize=7)

        ax = axes[2]
        scenarios = [r["scenario"] for r in erythro_rows]
        psi_v = [r["final_psi"] for r in erythro_rows]
        eri_v = [r["eri_proxy"] for r in erythro_rows]
        x = np.arange(len(scenarios))
        ax.bar(x - 0.2, psi_v, 0.35, color="#1f77b4", alpha=0.8, label="Final Psi_s")
        ax3 = ax.twinx()
        ax3.bar(x + 0.2, eri_v, 0.35, color="#d62728", alpha=0.8, label="ERI proxy")
        ax.set_xticks(x); ax.set_xticklabels(scenarios, rotation=25, ha="right", fontsize=6)
        ax.set_ylabel("Final Psi_s", color="#1f77b4"); ax3.set_ylabel("ERI proxy", color="#d62728")
        ax.set_title("Erythropoiesis: Psi_s and ERI proxy")

        fig.suptitle("AFL Paper 06 — Toy Diagnostics: Renal/Erythropoiesis (not clinical predictions)", fontweight="bold")
        fig.savefig(out / "renal_constraint_cascade.png", dpi=220)
        plt.close(fig)

    print(f"Paper 06 outputs → {out}/")


if __name__ == "__main__":
    main()
