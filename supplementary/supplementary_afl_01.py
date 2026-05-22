"""
Supplementary — AFL Part III Paper 01
Adaptive Flux Limitation in Living Systems (AFL-1)

Toy demonstration: adaptive constraint formation produces metabolic channeling
and a stable Psi_s band. Non-adaptive control homogenises with no regulatory
structure. All outputs are synthetic toy diagnostics; no clinical claims are made.

Outputs: outputs/paper_01/
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from partiii_runtime import ensure_output, laplacian_2d, regime_label, safe_plot, write_csv, write_json

N = 60
STEPS = 500
DT = 0.05
ALPHA = 0.08
BETA = 0.02
GAMMA = 0.005
KAPPA_S = 0.05
D_M = 0.01
SEED = 42


def _run(alpha: float) -> dict:
    rng = np.random.default_rng(SEED)
    Phi = rng.random((N, N)) * 0.5
    C = np.ones((N, N))
    S = np.ones((N, N))
    M_s = np.ones((N, N)) * 0.1
    Phi[0, :] = 5.0

    psi_h, phi_h, c_h, s_h, ms_h = [], [], [], [], []
    for _ in range(STEPS):
        Phi[0, :] = 5.0
        safe_C = np.maximum(C, 1e-12)
        diff = laplacian_2d((Phi / safe_C) * S)
        Phi = np.clip(Phi + DT * diff, 0.0, 100.0)
        C = np.clip(C + DT * (alpha * np.abs(diff) - BETA * C + GAMMA * laplacian_2d(C)), 1e-12, None)
        psi = (Phi / np.maximum(C, 1e-12)) * S * M_s
        M_s = np.maximum(M_s + DT * np.clip(Phi * S - D_M * M_s, -10.0, 10.0), 0.0)
        S = np.maximum(S + DT * np.clip(KAPPA_S * (psi - S), -10.0, 10.0), 0.01)
        psi_h.append(float(np.mean(psi)))
        phi_h.append(float(np.mean(Phi)))
        c_h.append(float(np.mean(C)))
        s_h.append(float(np.mean(S)))
        ms_h.append(float(np.mean(M_s)))

    return dict(psi=psi_h, phi=phi_h, c=c_h, s=s_h, ms=ms_h, C_field=C.copy())


def main() -> None:
    out = ensure_output("paper_01")

    adaptive = _run(alpha=ALPHA)
    control = _run(alpha=0.0)

    std_on = float(np.std(adaptive["C_field"]))
    std_off = float(np.std(control["C_field"]))

    rows = [
        {
            "condition": "adaptive (alpha=0.08)",
            "final_psi": round(adaptive["psi"][-1], 4),
            "final_phi": round(adaptive["phi"][-1], 4),
            "final_C": round(adaptive["c"][-1], 4),
            "std_C": round(std_on, 4),
            "regime": regime_label(adaptive["psi"][-1]),
            "note": "toy diagnostic only",
        },
        {
            "condition": "control (alpha=0.0)",
            "final_psi": round(control["psi"][-1], 4),
            "final_phi": round(control["phi"][-1], 4),
            "final_C": round(control["c"][-1], 4),
            "std_C": round(std_off, 4),
            "regime": regime_label(control["psi"][-1]),
            "note": "toy diagnostic only",
        },
    ]
    write_csv(out / "afl_scenarios.csv", rows)

    surface_rows = [
        {"step": i * DT, "psi_adaptive": round(p, 4), "psi_control": round(q, 4),
         "S_adaptive": round(s, 4), "Ms_adaptive": round(ms, 4)}
        for i, (p, q, s, ms) in enumerate(
            zip(adaptive["psi"], control["psi"], adaptive["s"], adaptive["ms"])
        )
    ]
    write_csv(out / "surface_response.csv", surface_rows)

    write_json(out / "summary.json", {
        "paper": "01",
        "title": "Adaptive Flux Limitation in Living Systems",
        "adaptive_final_psi": round(adaptive["psi"][-1], 4),
        "control_final_psi": round(control["psi"][-1], 4),
        "adaptive_std_C": round(std_on, 4),
        "control_std_C": round(std_off, 4),
        "regime_adaptive": regime_label(adaptive["psi"][-1]),
        "regime_control": regime_label(control["psi"][-1]),
        "claim_status": "toy diagnostic — not a clinical claim",
        "falsification_target": (
            "If Psi_s evolution is fully explained by a static concentration "
            "without adaptive constraint dynamics, AFL adds no mechanistic value."
        ),
    })

    plt = safe_plot()
    if plt is not None:
        t = np.arange(STEPS) * DT
        fig, axes = plt.subplots(1, 3, figsize=(16, 4.5), constrained_layout=True)

        ax = axes[0]
        ax.plot(t, adaptive["psi"], color="#1f77b4", lw=1.5, label="Adaptive (α=0.08)")
        ax.plot(t, control["psi"], color="#d62728", lw=1.5, ls="--", label="Control (α=0)")
        ax.axhline(0.8, color="grey", lw=0.8, ls=":")
        ax.axhline(1.2, color="grey", lw=0.8, ls=":")
        ax.set_xlabel("Time")
        ax.set_ylabel("Mean Ψ_s")
        ax.set_title("Adaptive vs Control: Mean Operating Ratio")
        ax.legend(frameon=False)

        ax = axes[1]
        im = ax.imshow(adaptive["C_field"], cmap="viridis", origin="lower", aspect="auto")
        plt.colorbar(im, ax=ax, label="Constraint C (toy)")
        ax.set_title("Adaptive: Final Constraint Field")

        ax = axes[2]
        ax.plot(t, adaptive["ms"], color="#ff7f0e", lw=1.5, label="M_s (memory)")
        ax.plot(t, adaptive["s"], color="#2ca02c", lw=1.5, label="S (responsiveness)")
        ax.set_xlabel("Time")
        ax.set_ylabel("S & M_s (toy units)")
        ax.set_title("Adaptive Surface Dynamics")
        ax.legend(frameon=False)

        fig.suptitle("AFL Paper 01 — Toy Diagnostic (not a clinical prediction)", fontweight="bold")
        fig.savefig(out / "adaptive_vs_control.png", dpi=220)
        plt.close(fig)

    print(f"Paper 01 outputs → {out}/")


if __name__ == "__main__":
    main()
