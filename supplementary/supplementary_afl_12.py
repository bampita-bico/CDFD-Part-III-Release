"""
Supplementary — AFL Part III Paper 12
Adaptive Flux Limitation in Developmental Biology: Morphogen Gradients as Constraint Fields

Toy demonstration: a 1-D morphogen gradient drives a spatially varying constraint
field. Scenarios: (A) normal patterning; (B) constraint perturbation — gradient
disruption; (C) developmental memory lock — M_s accumulation after transient insult.

Validation surfaces: organoids, embryoid bodies, HuBMAP/Human Cell Atlas spatial data.
All outputs are candidate mappings, not causation claims.

Outputs: outputs/paper_12/
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from partiii_runtime import ensure_output, laplacian_1d, operating_ratio, regime_label, safe_plot, write_csv, write_json

DT = 0.04
STEPS = 600
N = 80  # 1-D tissue axis
D_MORPH = 0.15   # morphogen diffusion
DECAY_M = 0.01   # morphogen decay
KAPPA_S = 0.04
D_M = 0.008
ALPHA = 0.07
BETA = 0.02


def _normal_patterning() -> dict:
    """Morphogen gradient from left boundary; constraint field forms in response."""
    morphogen = np.zeros(N)
    morphogen[0] = 5.0  # source
    C = np.ones(N)
    S = np.ones(N)
    M_s = np.ones(N) * 0.1

    snap_steps = [100, 300, 599]
    snapshots = {}
    rows = []
    for step in range(STEPS):
        morphogen[0] = 5.0
        morphogen += DT * (D_MORPH * laplacian_1d(morphogen) - DECAY_M * morphogen)
        morphogen = np.clip(morphogen, 0.0, 10.0)

        C += DT * (ALPHA * morphogen - BETA * C)
        C = np.maximum(C, 1e-9)

        psi = (morphogen / np.maximum(C, 1e-12)) * S * M_s
        M_s = np.maximum(M_s + DT * np.clip(morphogen * S - D_M * M_s, -10.0, 10.0), 0.0)
        S = np.maximum(S + DT * np.clip(KAPPA_S * (psi - S), -10.0, 10.0), 0.01)

        rows.append({
            "step": step, "mean_morphogen": round(float(np.mean(morphogen)), 4),
            "mean_C": round(float(np.mean(C)), 4), "mean_psi": round(float(np.mean(psi)), 4),
        })
        if step in snap_steps:
            snapshots[step] = {
                "morphogen": morphogen.tolist(), "C": C.tolist(), "psi": psi.tolist()
            }
    return {"rows": rows, "snapshots": snapshots, "final_C": C.copy(), "final_morph": morphogen.copy()}


def _disrupted_patterning() -> dict:
    """Constraint perturbation at midpoint simulates developmental insult."""
    morphogen = np.zeros(N)
    morphogen[0] = 5.0
    C = np.ones(N)
    S = np.ones(N)
    M_s = np.ones(N) * 0.1

    rows = []
    for step in range(STEPS):
        morphogen[0] = 5.0
        morphogen += DT * (D_MORPH * laplacian_1d(morphogen) - DECAY_M * morphogen)
        morphogen = np.clip(morphogen, 0.0, 10.0)

        # Insult: elevated constraint at midpoint between steps 100-200
        if 100 <= step < 200:
            C[N // 2 - 3: N // 2 + 3] += DT * 1.5

        C += DT * (ALPHA * morphogen - BETA * C)
        C = np.maximum(C, 1e-9)

        psi = (morphogen / np.maximum(C, 1e-12)) * S * M_s
        M_s = np.maximum(M_s + DT * np.clip(morphogen * S - D_M * M_s, -10.0, 10.0), 0.0)
        S = np.maximum(S + DT * np.clip(KAPPA_S * (psi - S), -10.0, 10.0), 0.01)

        rows.append({
            "step": step, "mean_psi": round(float(np.mean(psi)), 4),
            "mean_C": round(float(np.mean(C)), 4),
            "phase": "insult" if 100 <= step < 200 else "free",
        })
    return {"rows": rows, "final_C": C.copy()}


def main() -> None:
    out = ensure_output("paper_12")

    normal = _normal_patterning()
    disrupted = _disrupted_patterning()

    snap_rows = []
    for step_key, snap in normal["snapshots"].items():
        for i in range(N):
            snap_rows.append({
                "snapshot_step": step_key, "cell_index": i,
                "morphogen": round(snap["morphogen"][i], 4),
                "C": round(snap["C"][i], 4),
                "psi": round(snap["psi"][i], 4),
            })
    write_csv(out / "morphogen_field_snapshots.csv", snap_rows)
    write_csv(out / "developmental_scenarios.csv", normal["rows"])

    write_json(out / "summary.json", {
        "paper": "12",
        "title": "Adaptive Flux Limitation in Developmental Biology",
        "simulations": ["normal_patterning", "disrupted_patterning"],
        "claim_status": "toy diagnostic — candidate framework for spatial constraint mapping",
        "validation_targets": [
            "Organoids: morphogen gradient perturbation and tissue patterning readout",
            "Embryoid body models: transient insult and recovery of spatial C field",
            "HuBMAP / Human Cell Atlas: spatial single-cell Phi/C proxy measurement",
            "Congenital anomaly registries: patterning failure classes as C disruption events",
        ],
        "falsification": (
            "If spatial patterning outcomes are fully determined by morphogen concentration "
            "alone without constraint memory (M_s), the spatial AFL scaffold adds no value."
        ),
    })

    plt = safe_plot()
    if plt is not None:
        x = np.arange(N)
        fig, axes = plt.subplots(1, 3, figsize=(17, 4.5), constrained_layout=True)

        ax = axes[0]
        ax.plot(x, normal["final_morph"], color="#1f77b4", lw=1.4, label="Morphogen")
        ax.plot(x, normal["final_C"], color="#d62728", lw=1.4, ls="--", label="Constraint C")
        ax.set_xlabel("Cell index"); ax.set_ylabel("Toy units")
        ax.set_title("Normal Patterning: Spatial Gradient (final)")
        ax.legend(frameon=False, fontsize=7)

        ax = axes[1]
        ax.plot(x, disrupted["final_C"], color="#9467bd", lw=1.4, label="C (disrupted)")
        ax.plot(x, normal["final_C"], color="#2ca02c", lw=1.2, ls="--", label="C (normal)")
        ax.axvspan(N // 2 - 3, N // 2 + 3, alpha=0.15, color="red", label="Insult zone")
        ax.set_xlabel("Cell index"); ax.set_ylabel("Constraint C (toy)")
        ax.set_title("Disrupted Patterning: Constraint Scar")
        ax.legend(frameon=False, fontsize=7)

        ax = axes[2]
        t_n = [r["step"] * DT for r in normal["rows"]]
        t_d = [r["step"] * DT for r in disrupted["rows"]]
        ax.plot(t_n, [r["mean_psi"] for r in normal["rows"]], color="#1f77b4", lw=1.4, label="Normal Psi_s")
        ax.plot(t_d, [r["mean_psi"] for r in disrupted["rows"]], color="#d62728", lw=1.3, ls="--", label="Disrupted Psi_s")
        ax.axvspan(100 * DT, 200 * DT, alpha=0.1, color="red")
        ax.set_xlabel("Time (toy)"); ax.set_ylabel("Mean Psi_s (toy)")
        ax.set_title("Psi_s Trajectory: Normal vs Disrupted")
        ax.legend(frameon=False, fontsize=7)

        fig.suptitle("AFL Paper 12 — Toy Diagnostics: Developmental Constraint Fields (not clinical predictions)", fontweight="bold")
        fig.savefig(out / "morphogen_field_snapshots.png", dpi=220)
        plt.close(fig)

    print(f"Paper 12 outputs → {out}/")


if __name__ == "__main__":
    main()
