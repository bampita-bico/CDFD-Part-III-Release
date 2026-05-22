"""
Supplementary — AFL Part III Paper 14
Adaptive Flux Limitation in Ecology and Networked Biology: Trophic Systems and Host-Environment Bridge

Toy trophic network: three levels (producers, primary consumers, apex consumers).
Each level has Phi (biomass flux) and C (trophic constraint). Perturbations simulate
ecological stress, microbiome disruption, and One Health spillover scenarios.

All outputs are candidate framings; no real ecological data is used.
Validation: outbreak data, wastewater surveillance, microbiome perturbation studies.

Outputs: outputs/paper_14/
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from partiii_runtime import ensure_output, euler_step, operating_ratio, regime_label, safe_plot, write_csv, write_json

DT = 0.05
STEPS = 700
KAPPA_S = 0.04
D_M = 0.008
ALPHA = 0.06
BETA = 0.025

# Trophic scenarios: (label, phi_prod, phi_prim, phi_apex, c_prod, c_prim, c_apex, note)
TROPHIC_SCENARIOS = [
    ("Pristine",      2.5, 1.8, 1.2, 0.5, 0.6, 0.7, "undisturbed ecosystem"),
    ("Overexploited", 1.0, 1.8, 1.2, 0.5, 0.6, 0.7, "producer flux halved"),
    ("Apex removed",  2.5, 1.8, 0.0, 0.5, 0.6, 0.5, "apex consumer absent"),
    ("Invasion",      2.5, 1.8, 1.2, 1.5, 0.6, 0.7, "invasive competitor raises C_prod"),
    ("Recovery",      2.0, 1.5, 1.0, 0.6, 0.7, 0.8, "post-perturbation partial recovery"),
    ("Microbiome OK", 2.0, 1.5, 1.0, 0.5, 0.5, 0.6, "host microbiome in balance"),
    ("Dysbiosis",     2.0, 1.5, 1.0, 1.5, 1.2, 0.8, "dysbiosis raises host C"),
]


def _sim(phi0: float, c0: float, ms0: float = 0.2) -> list[float]:
    phi, c, s, ms = phi0, c0, 1.0, ms0
    psi_h = []
    for _ in range(STEPS):
        c, s, ms = euler_step(phi, c, s, ms, ALPHA, BETA, KAPPA_S, D_M, DT)
        psi_h.append(operating_ratio(phi, c, s, ms))
    return psi_h


def _one_health_sim(steps: int = 600) -> list[dict]:
    """Zoonotic spillover: wildlife stress raises host constraint."""
    phi_host = 2.0
    c_host = 0.5
    c_wildlife = 0.5
    s, ms = 1.0, 0.2
    rows = []
    for i in range(steps):
        # Wildlife constraint rises from step 150 (habitat loss / climate stress)
        if i >= 150:
            c_wildlife += DT * 0.004
        # Spillover: when wildlife constraint is high, host C rises
        spillover = max(0.0, c_wildlife - 1.0) * 0.05
        c_host += DT * (spillover - 0.02 * (c_host - 0.5))
        c_host = max(c_host, 1e-9)
        psi = operating_ratio(phi_host, c_host, s, ms)
        c_ms = ms
        ms = max(ms + DT * np.clip(phi_host * s - D_M * ms, -10.0, 10.0), 0.0)
        s = max(s + DT * np.clip(KAPPA_S * (psi - s), -10.0, 10.0), 0.01)
        rows.append({
            "step": i, "t": round(i * DT, 3),
            "c_wildlife": round(c_wildlife, 4),
            "c_host": round(c_host, 4),
            "psi_host": round(psi, 4),
            "regime": regime_label(psi),
            "phase": "spillover risk" if c_wildlife > 1.0 else "stable",
        })
    return rows


def main() -> None:
    out = ensure_output("paper_14")

    rows = []
    histories = {}
    for (label, phi_p, phi_prim, phi_apex, c_p, c_prim, c_apex, note) in TROPHIC_SCENARIOS:
        psi_prod  = _sim(phi_p, c_p)
        psi_prim  = _sim(max(phi_prim, 0.01), c_prim)
        psi_apex  = _sim(max(phi_apex, 0.01), c_apex) if phi_apex > 0 else [0.0] * STEPS
        combined_psi = [0.333 * (a + b + c) for a, b, c in zip(psi_prod, psi_prim, psi_apex)]
        histories[label] = combined_psi
        rows.append({
            "scenario": label,
            "phi_producer": phi_p, "phi_primary": phi_prim, "phi_apex": phi_apex,
            "c_producer": c_p, "c_primary": c_prim, "c_apex": c_apex,
            "final_psi_combined": round(combined_psi[-1], 4),
            "regime": regime_label(combined_psi[-1]),
            "note": note,
            "claim_status": "candidate ecological AFL mapping — not validated",
        })

    one_health = _one_health_sim()

    write_csv(out / "trophic_network.csv", rows)
    write_csv(out / "one_health_spillover.csv", one_health)

    write_json(out / "summary.json", {
        "paper": "14",
        "title": "Adaptive Flux Limitation in Ecology and Networked Biology",
        "scenarios": len(rows),
        "claim_status": "toy diagnostic — candidate ecological framework",
        "validation_targets": [
            "Outbreak surveillance: wildlife stress indicator before spillover event",
            "Wastewater surveillance: community-level C proxy from pathogen load",
            "Microbiome perturbation studies: dysbiosis as C elevation in host",
            "Ecological network data: trophic cascade Phi/C signatures",
        ],
        "falsification": (
            "If wildlife constraint elevation has no predictive correlation with "
            "zoonotic spillover risk after controlling for habitat overlap, the "
            "One Health AFL bridge does not hold."
        ),
    })

    plt = safe_plot()
    if plt is not None:
        t = np.arange(STEPS) * DT
        fig, axes = plt.subplots(1, 2, figsize=(14, 5), constrained_layout=True)

        ax = axes[0]
        colors = plt.cm.tab10(np.linspace(0, 1, len(TROPHIC_SCENARIOS)))
        for (label, *_), col in zip(TROPHIC_SCENARIOS, colors):
            ax.plot(t, histories[label], lw=1.2, label=label, color=col)
        ax.axhline(0.8, color="grey", lw=0.8, ls=":")
        ax.axhline(1.2, color="grey", lw=0.8, ls=":")
        ax.set_xlabel("Time (toy)"); ax.set_ylabel("Combined Psi_s (toy)")
        ax.set_title("Trophic Network: Ecosystem Psi_s Trajectories")
        ax.legend(frameon=False, fontsize=6)

        ax = axes[1]
        t_oh = [r["t"] for r in one_health]
        ax.plot(t_oh, [r["c_wildlife"] for r in one_health], color="#d62728", lw=1.4, label="C_wildlife")
        ax.plot(t_oh, [r["c_host"] for r in one_health], color="#1f77b4", lw=1.4, ls="--", label="C_host")
        ax.plot(t_oh, [r["psi_host"] for r in one_health], color="#2ca02c", lw=1.2, ls=":", label="Psi_host")
        ax.axvline(150 * DT, color="grey", lw=0.9, ls=":", label="Habitat stress onset")
        ax.set_xlabel("Time (toy)"); ax.set_ylabel("Toy units")
        ax.set_title("One Health: Wildlife→Host Constraint Transfer")
        ax.legend(frameon=False, fontsize=7)

        fig.suptitle("AFL Paper 14 — Toy Diagnostics: Ecological AFL (not validated predictions)", fontweight="bold")
        fig.savefig(out / "ecological_afl.png", dpi=220)
        plt.close(fig)

    print(f"Paper 14 outputs → {out}/")


if __name__ == "__main__":
    main()
