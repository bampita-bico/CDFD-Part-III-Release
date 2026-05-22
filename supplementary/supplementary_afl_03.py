"""
Supplementary — AFL Part III Paper 03
Adaptive Flux Limitation in Clinical Translation: Sepsis, Organ Coupling, and ICU Cascade

Three toy scenarios: (A) sepsis cascade — infection source drives Phi spike,
C rises via endothelial/inflammatory load, multi-organ coupling propagates
constraint; (B) cardiorenal constraint transfer — renal C rises secondary to
cardiac output fall; (C) post-ICU recovery — M_s memory retention after
the acute insult is resolved.

All outputs are synthetic toy diagnostics. No real patient data is used.
Claim status: hypothesis / candidate validation target.

Outputs: outputs/paper_03/
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


# --- A: Sepsis cascade ---
def sepsis_sim(steps: int = 600) -> dict:
    phi = 1.0      # baseline physiological flux
    c_immune = 0.5
    c_endo = 0.5   # endothelial constraint
    c_renal = 0.5
    c_cardiac = 0.5
    s, ms = 1.0, 0.2

    rows = []
    for i in range(steps):
        # infection event at step 50
        phi_infect = phi + (3.0 * np.exp(-0.01 * max(0, i - 50)) if i >= 50 else 0.0)

        # immune and endothelial constraint rise with infection load
        c_immune += DT * (0.08 * phi_infect - 0.03 * c_immune)
        c_endo += DT * (0.06 * c_immune - 0.02 * c_endo)

        # organ coupling: renal and cardiac constraints rise secondary
        c_renal += DT * (0.04 * c_endo - 0.015 * c_renal)
        c_cardiac += DT * (0.03 * c_endo - 0.015 * c_cardiac)

        c_total = max(c_immune + c_endo + c_renal + c_cardiac, 1e-9)
        psi = operating_ratio(phi_infect, c_total, s, ms)

        ms = max(ms + DT * np.clip(phi_infect * s - D_M * ms, -10.0, 10.0), 0.0)
        s = max(s + DT * np.clip(KAPPA_S * (psi - s), -10.0, 10.0), 0.01)

        rows.append({
            "step": i, "t": round(i * DT, 3),
            "phi_infect": round(phi_infect, 4),
            "c_immune": round(c_immune, 4),
            "c_endo": round(c_endo, 4),
            "c_renal": round(c_renal, 4),
            "c_cardiac": round(c_cardiac, 4),
            "c_total": round(c_total, 4),
            "psi": round(psi, 4),
            "Ms": round(ms, 4),
            "regime": regime_label(psi),
        })
    return {"rows": rows}


# --- B: Cardiorenal constraint transfer ---
def cardiorenal_sim(steps: int = 500) -> dict:
    phi_cardiac = 2.0
    c_cardiac = 0.5
    c_renal = 0.5
    s, ms = 1.0, 0.2
    rows = []
    for i in range(steps):
        # cardiac output falls from step 100
        if i >= 100:
            phi_cardiac = max(phi_cardiac - DT * 0.004, 0.5)

        # renal constraint rises secondary to reduced cardiac output
        c_cardiac += DT * (0.02 * abs(phi_cardiac - 1.5) - 0.01 * c_cardiac)
        c_renal += DT * (0.05 * max(0, c_cardiac - 0.6) - 0.015 * c_renal)

        psi = operating_ratio(phi_cardiac, c_renal, s, ms)
        ms = max(ms + DT * np.clip(phi_cardiac * s - D_M * ms, -10.0, 10.0), 0.0)
        s = max(s + DT * np.clip(KAPPA_S * (psi - s), -10.0, 10.0), 0.01)

        rows.append({
            "step": i, "t": round(i * DT, 3),
            "phi_cardiac": round(phi_cardiac, 4),
            "c_cardiac": round(c_cardiac, 4),
            "c_renal": round(c_renal, 4),
            "psi": round(psi, 4),
            "regime": regime_label(psi),
        })
    return {"rows": rows}


# --- C: Post-ICU memory retention ---
def post_icu_sim(steps: int = 800, insult_end: int = 200) -> dict:
    phi, c, s, ms = 1.0, 0.5, 1.0, 0.2
    rows = []
    for i in range(steps):
        phi_eff = 3.0 if i < insult_end else 1.0  # acute insult resolved at insult_end
        c += DT * (0.07 * phi_eff - 0.025 * c)
        psi = operating_ratio(phi_eff, c, s, ms)
        ms = max(ms + DT * np.clip(phi_eff * s - D_M * ms, -10.0, 10.0), 0.0)
        s = max(s + DT * np.clip(KAPPA_S * (psi - s), -10.0, 10.0), 0.01)
        rows.append({
            "step": i, "t": round(i * DT, 3),
            "phi_eff": round(phi_eff, 4), "C": round(c, 4),
            "psi": round(psi, 4), "Ms": round(ms, 4),
            "phase": "acute" if i < insult_end else "recovery",
            "regime": regime_label(psi),
        })
    return {"rows": rows}


def main() -> None:
    out = ensure_output("paper_03")

    sep = sepsis_sim()
    cr = cardiorenal_sim()
    post = post_icu_sim()

    write_csv(out / "sepsis_cascade.csv", sep["rows"])
    write_csv(out / "cardiorenal_transfer.csv", cr["rows"])
    write_csv(out / "post_icu_recovery.csv", post["rows"])

    write_json(out / "summary.json", {
        "paper": "03",
        "title": "Adaptive Flux Limitation in Clinical Translation",
        "scenarios": ["sepsis_cascade", "cardiorenal_transfer", "post_icu_recovery"],
        "claim_status": "toy diagnostic — candidate validation target",
        "validation_targets": [
            "Longitudinal ICU time-series: lactate, vasopressor dose, creatinine, urine output",
            "Post-ICU sequelae cohorts: PICS, persistent Psi elevation as M_s proxy",
            "Cardiorenal registry data: eGFR decline vs cardiac output drop correlation",
        ],
        "falsification": (
            "If organ constraint coupling is statistically absent in ICU time-series "
            "after controlling for shared haemodynamic drivers, the transfer model adds no value."
        ),
    })

    plt = safe_plot()
    if plt is not None:
        fig, axes = plt.subplots(1, 3, figsize=(17, 4.5), constrained_layout=True)
        t_sep = [r["t"] for r in sep["rows"]]
        t_cr = [r["t"] for r in cr["rows"]]
        t_post = [r["t"] for r in post["rows"]]

        ax = axes[0]
        ax.plot(t_sep, [r["psi"] for r in sep["rows"]], color="#1f77b4", lw=1.4, label="Psi_s")
        ax.plot(t_sep, [r["c_total"] for r in sep["rows"]], color="#d62728", lw=1.2, ls="--", label="C_total")
        ax.axhline(1.2, color="grey", lw=0.8, ls=":")
        ax.set_xlabel("Time (toy)"); ax.set_ylabel("Psi_s / C_total")
        ax.set_title("Sepsis: Constraint Cascade"); ax.legend(frameon=False, fontsize=7)

        ax = axes[1]
        ax.plot(t_cr, [r["phi_cardiac"] for r in cr["rows"]], color="#2ca02c", lw=1.3, label="Phi_cardiac")
        ax.plot(t_cr, [r["c_renal"] for r in cr["rows"]], color="#9467bd", lw=1.3, ls="--", label="C_renal")
        ax.set_xlabel("Time (toy)"); ax.set_ylabel("Toy units")
        ax.set_title("Cardiorenal: Constraint Transfer"); ax.legend(frameon=False, fontsize=7)

        ax = axes[2]
        ax.plot(t_post, [r["psi"] for r in post["rows"]], color="#1f77b4", lw=1.3, label="Psi_s")
        ax.plot(t_post, [r["Ms"] for r in post["rows"]], color="#ff7f0e", lw=1.3, ls="--", label="M_s (memory)")
        ax.axvline(200 * DT, color="grey", lw=0.9, ls=":", label="Insult resolved")
        ax.set_xlabel("Time (toy)"); ax.set_ylabel("Psi_s / M_s")
        ax.set_title("Post-ICU: Memory Retention"); ax.legend(frameon=False, fontsize=7)

        fig.suptitle("AFL Paper 03 — Toy Diagnostics: ICU Cascade (not clinical predictions)", fontweight="bold")
        fig.savefig(out / "icu_organ_coupling.png", dpi=220)
        plt.close(fig)

    print(f"Paper 03 outputs → {out}/")


if __name__ == "__main__":
    main()
