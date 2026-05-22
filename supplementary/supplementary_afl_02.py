"""
Supplementary — AFL Part III Paper 02
Adaptive Flux Limitation Across Living Domains: Cross-Domain System Dictionary

Demonstrates that the same Phi/C/Psi_s grammar applies across biological domains
by computing steady-state operating ratios for a representative body-system matrix.
All entries are candidate mappings, not validated measurements.

Outputs: outputs/paper_02/
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from partiii_runtime import ensure_output, euler_step, operating_ratio, regime_label, safe_plot, write_csv, write_json

DT = 0.05
STEPS = 400
ALPHA = 0.06
BETA = 0.02
KAPPA_S = 0.05
D_M = 0.01

# Body-system matrix: (domain, Phi_label, C_label, Phi0, C0, S0, M_s0)
SYSTEMS = [
    ("Metabolic",      "glucose flux",          "insulin resistance",    2.0, 1.0, 1.0, 0.5),
    ("Renal",          "filtration flux",        "nephron damage",        1.5, 1.2, 1.0, 0.5),
    ("Immune",         "pathogen clearance",     "inflammatory load",     1.8, 0.8, 1.0, 0.5),
    ("Oncologic",      "proliferative flux",     "apoptosis constraint",  3.0, 0.4, 1.0, 0.5),
    ("Neurologic",     "neural firing rate",     "inhibitory tone",       2.2, 1.0, 1.0, 0.5),
    ("Developmental",  "morphogen flux",         "patterning constraint", 1.0, 1.0, 1.0, 0.5),
    ("Microbial",      "bacterial replication",  "host defence",          1.5, 1.5, 1.0, 0.5),
    ("Cardiovascular", "cardiac output",         "vascular resistance",   2.0, 1.0, 1.0, 0.5),
    ("Hepatic",        "metabolic detox flux",   "fibrotic constraint",   1.8, 0.9, 1.0, 0.5),
    ("Pulmonary",      "gas exchange flux",      "airway resistance",     1.6, 1.1, 1.0, 0.5),
]


def _simulate(phi0: float, c0: float, s0: float, ms0: float) -> dict:
    phi, c, s, ms = phi0, c0, s0, ms0
    psi_h = []
    for _ in range(STEPS):
        c, s, ms = euler_step(phi, c, s, ms, ALPHA, BETA, KAPPA_S, D_M, DT)
        psi_h.append(operating_ratio(phi, c, s, ms))
    return {"final_psi": psi_h[-1], "psi_history": psi_h}


def main() -> None:
    out = ensure_output("paper_02")

    rows = []
    histories = {}
    for (domain, phi_lbl, c_lbl, phi0, c0, s0, ms0) in SYSTEMS:
        res = _simulate(phi0, c0, s0, ms0)
        rows.append({
            "domain": domain,
            "Phi_label": phi_lbl,
            "C_label": c_lbl,
            "Phi0": phi0,
            "C0": c0,
            "final_psi": round(res["final_psi"], 4),
            "regime": regime_label(res["final_psi"]),
            "candidate_mapping": "hypothesis",
        })
        histories[domain] = res["psi_history"]

    write_csv(out / "domain_comparison.csv", rows)

    write_json(out / "summary.json", {
        "paper": "02",
        "title": "Adaptive Flux Limitation Across Living Domains",
        "domains_modelled": len(rows),
        "claim_status": "candidate mappings — not validated measurements",
        "falsification_target": (
            "If domain-specific mechanisms require fundamentally different "
            "constraint dynamics (not captured by dC/dt = alpha*Phi - beta*C), "
            "the universal skeleton breaks down for that domain."
        ),
        "results": [{r["domain"]: r["final_psi"]} for r in rows],
    })

    plt = safe_plot()
    if plt is not None:
        t = np.arange(STEPS) * DT
        fig, axes = plt.subplots(1, 2, figsize=(14, 5), constrained_layout=True)

        ax = axes[0]
        colors = plt.cm.tab10(np.linspace(0, 1, len(SYSTEMS)))
        for (domain, *_), col in zip(SYSTEMS, colors):
            ax.plot(t, histories[domain], lw=1.2, label=domain, color=col)
        ax.axhline(0.8, color="grey", lw=0.8, ls=":")
        ax.axhline(1.2, color="grey", lw=0.8, ls=":")
        ax.set_xlabel("Time (toy units)")
        ax.set_ylabel("Ψ_s (toy)")
        ax.set_title("Cross-Domain AFL: Psi_s Trajectories")
        ax.legend(frameon=False, fontsize=6)

        ax = axes[1]
        domains = [r["domain"] for r in rows]
        psi_vals = [r["final_psi"] for r in rows]
        x = np.arange(len(domains))
        bars = ax.bar(x, psi_vals, color=colors, alpha=0.85)
        ax.axhline(0.8, color="grey", lw=0.8, ls=":")
        ax.axhline(1.2, color="grey", lw=0.8, ls=":")
        ax.set_xticks(x)
        ax.set_xticklabels(domains, rotation=35, ha="right", fontsize=7)
        ax.set_ylabel("Final Ψ_s (toy)")
        ax.set_title("Body-System Matrix: Final Operating Ratios")

        fig.suptitle("AFL Paper 02 — Candidate Cross-Domain Mappings (not validated)", fontweight="bold")
        fig.savefig(out / "cross_domain_afl.png", dpi=220)
        plt.close(fig)

    print(f"Paper 02 outputs → {out}/")


if __name__ == "__main__":
    main()
