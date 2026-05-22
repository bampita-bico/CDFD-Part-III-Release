"""
Supplementary — AFL Part III Paper 13
Adaptive Flux Limitation in Evolutionary Dynamics: Selection, Trade-Offs, and Memory Accumulation

Toy model of evolutionary AFL: populations vary in (alpha, beta) — constraint
growth and relaxation rates. Selection favours lineages near Psi_s ≈ 1.
Aging is modelled as M_s accumulation and repair-reserve decline.

All outputs are candidate framings, not validated evolutionary measurements.
Validation: longitudinal cohorts, comparative biology, allometric studies.

Outputs: outputs/paper_13/
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from partiii_runtime import ensure_output, euler_step, operating_ratio, regime_label, safe_plot, write_csv, write_json

DT = 0.05
STEPS = 600
N_LINEAGES = 12
KAPPA_S = 0.04
D_M = 0.008

rng = np.random.default_rng(7)

# Each lineage: (alpha, beta, phi0, label)
LINEAGES = [
    (0.04, 0.03, 1.5, "low-alpha (slow constraint growth)"),
    (0.06, 0.03, 1.5, "moderate-alpha"),
    (0.10, 0.03, 1.5, "high-alpha (rapid constraint)"),
    (0.06, 0.01, 1.5, "low-beta (slow relaxation)"),
    (0.06, 0.05, 1.5, "high-beta (fast relaxation)"),
    (0.06, 0.03, 0.8, "low-phi (resource-poor)"),
    (0.06, 0.03, 2.5, "high-phi (resource-rich)"),
    (0.06, 0.03, 1.5, "baseline"),
    (0.04, 0.04, 1.2, "balanced (near Psi~1 attractor)"),
    (0.10, 0.01, 2.0, "trade-off: high load, slow repair"),
    (0.03, 0.06, 0.9, "trade-off: low load, fast repair"),
    (0.07, 0.02, 1.8, "aging proxy (M_s accumulator)"),
]


def _aging_sim(steps: int = 800) -> list[dict]:
    """Aging: progressive beta decline (repair reserve falls), M_s accumulates."""
    phi, c, s, ms = 1.5, 0.8, 1.0, 0.2
    rows = []
    for i in range(steps):
        beta_t = max(0.03 - i * 0.00002, 0.005)  # repair reserve declines
        c, s, ms = euler_step(phi, c, s, ms, 0.06, beta_t, KAPPA_S, D_M, DT)
        psi = operating_ratio(phi, c, s, ms)
        rows.append({
            "step": i, "t": round(i * DT, 3), "beta": round(beta_t, 5),
            "C": round(c, 4), "Ms": round(ms, 4), "psi": round(psi, 4),
            "regime": regime_label(psi),
        })
    return rows


def main() -> None:
    out = ensure_output("paper_13")

    # Lineage trajectories
    traj_rows = []
    summary_rows = []
    histories = {}
    for (alpha, beta, phi0, label) in LINEAGES:
        phi, c, s, ms = phi0, 0.8, 1.0, 0.2
        psi_h = []
        for _ in range(STEPS):
            c, s, ms = euler_step(phi, c, s, ms, alpha, beta, KAPPA_S, D_M, DT)
            psi = operating_ratio(phi, c, s, ms)
            psi_h.append(psi)
        final_psi = psi_h[-1]
        histories[label] = psi_h
        fitness = 1.0 / (1.0 + abs(final_psi - 1.0))  # fitness peaks at Psi ~ 1
        summary_rows.append({
            "lineage": label, "alpha": alpha, "beta": beta, "phi0": phi0,
            "final_psi": round(final_psi, 4), "fitness_proxy": round(fitness, 4),
            "regime": regime_label(final_psi),
            "claim_status": "candidate fitness proxy — not validated",
        })
        for i, p in enumerate(psi_h):
            traj_rows.append({"step": i, "lineage": label, "psi": round(p, 4)})

    aging = _aging_sim()

    write_csv(out / "evolutionary_scenarios.csv", summary_rows)
    write_csv(out / "evolutionary_trajectory.csv", traj_rows)
    write_csv(out / "aging_memory_accumulation.csv", aging)

    write_json(out / "summary.json", {
        "paper": "13",
        "title": "Adaptive Flux Limitation in Evolutionary Dynamics",
        "lineages": len(LINEAGES),
        "claim_status": "candidate evolutionary AFL framing — not validated",
        "validation_targets": [
            "Longitudinal cohort aging studies: M_s proxy vs biomarker accumulation",
            "Comparative biology: alpha/beta analogs across species lifespans",
            "Allometric scaling: constraint dynamics vs body mass",
            "Evolutionary rescue experiments: constraint relaxation under stress",
        ],
        "falsification": (
            "If lineage fitness is uncorrelated with proximity to Psi_s ~ 1 in "
            "empirical evolutionary datasets, the selection-on-Psi framing fails."
        ),
    })

    plt = safe_plot()
    if plt is not None:
        t = np.arange(STEPS) * DT
        fig, axes = plt.subplots(1, 3, figsize=(17, 4.5), constrained_layout=True)

        ax = axes[0]
        colors = plt.cm.tab20(np.linspace(0, 1, len(LINEAGES)))
        for (_, _, _, label), col in zip(LINEAGES, colors):
            ax.plot(t, histories[label], lw=0.9, label=label, color=col)
        ax.axhline(0.8, color="grey", lw=0.7, ls=":")
        ax.axhline(1.2, color="grey", lw=0.7, ls=":")
        ax.set_xlabel("Time (toy)"); ax.set_ylabel("Psi_s (toy)")
        ax.set_title("Lineage Psi_s Trajectories")
        ax.legend(frameon=False, fontsize=5)

        ax = axes[1]
        labels = [r["lineage"][:20] for r in summary_rows]
        fitness = [r["fitness_proxy"] for r in summary_rows]
        x = np.arange(len(labels))
        ax.bar(x, fitness, color=colors, alpha=0.85)
        ax.set_xticks(x); ax.set_xticklabels(labels, rotation=35, ha="right", fontsize=5)
        ax.set_ylabel("Fitness proxy (1/(1+|Psi-1|))")
        ax.set_title("Selection Analogy: Fitness near Psi_s ~ 1")

        ax = axes[2]
        t_age = [r["t"] for r in aging]
        ax.plot(t_age, [r["Ms"] for r in aging], color="#ff7f0e", lw=1.4, label="M_s (memory)")
        ax.plot(t_age, [r["psi"] for r in aging], color="#1f77b4", lw=1.3, ls="--", label="Psi_s")
        ax.set_xlabel("Time (toy)"); ax.set_ylabel("M_s / Psi_s (toy)")
        ax.set_title("Aging: M_s Accumulation as Repair Reserve Falls")
        ax.legend(frameon=False, fontsize=7)

        fig.suptitle("Adaptive Flux Limitation Paper 13 - Toy Diagnostics: Evolutionary Dynamics (not validated)", fontweight="bold")
        fig.savefig(out / "evolutionary_dynamics.png", dpi=220)
        plt.close(fig)

    print(f"Paper 13 outputs → {out}/")


if __name__ == "__main__":
    main()
