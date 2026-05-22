"""Part III pharmacological orthogonality diagnostic.

This toy model compares same-axis and cross-axis drug combinations in CDFD/AFL
terms. It is not a prescribing model and does not recommend drug combinations.
"""
from __future__ import annotations

import numpy as np

from partiii_runtime import State, apply_pharmacology, ensure_output, safe_plot, state_summary, write_csv, write_json


def simulate_combo(name: str, drugs: list[dict[str, float]], steps: int = 160, dt: float = 0.05) -> tuple[list[dict[str, float]], dict[str, object]]:
    state = State(16, 16)
    state.C += 0.45
    rows: list[dict[str, float]] = []
    for step in range(steps):
        t = step * dt
        apply_pharmacology(state, drugs, dt=dt)
        state.update_psi()
        state.t = t
        if step % 4 == 0:
            rows.append(
                {
                    "t": float(t),
                    "mean_phi": float(np.mean(state.phi)),
                    "mean_C": float(np.mean(state.C)),
                    "mean_beta": float(np.mean(state.beta)),
                    "mean_psi_s": float(np.mean(state.psi_s)),
                    "ischemia_warning": int(bool(state.meta.get("ischemia_warning", False))),
                }
            )
    summary = {
        "diagnostic": name,
        "drugs": drugs,
        "status": state.meta.get("synergy_status", "STANDARD"),
        "clinical_status": "toy model; not a drug recommendation or safety model",
        "final_state": state_summary(state),
    }
    return rows, summary


def write_plot(series: dict[str, list[dict[str, float]]], path) -> None:
    plt = safe_plot()
    if plt is None:
        return
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for name, rows in series.items():
        ax.plot([r["t"] for r in rows], [r["mean_psi_s"] for r in rows], label=name)
    ax.axhline(1.0, color="black", linewidth=0.8, linestyle="--", label="Psi_s = 1")
    ax.set_xlabel("model time")
    ax.set_ylabel("mean Psi_s")
    ax.set_title("AFL pharmacological orthogonality toy diagnostic")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def main() -> dict[str, object]:
    out = ensure_output("paper_09")
    redundant_rows, redundant_summary = simulate_combo(
        "same_axis_flux_reduction",
        [{"target": "phi", "effect": -0.12}, {"target": "phi", "effect": -0.10}],
    )
    orthogonal_rows, orthogonal_summary = simulate_combo(
        "cross_axis_flux_relaxation",
        [{"target": "phi", "effect": -0.08}, {"target": "beta", "effect": 0.055}],
    )
    write_csv(out / "same_axis_flux_reduction.csv", redundant_rows)
    write_csv(out / "cross_axis_flux_relaxation.csv", orthogonal_rows)
    write_json(out / "summary.json", {"same_axis": redundant_summary, "cross_axis": orthogonal_summary})
    write_plot({"same_axis": redundant_rows, "cross_axis": orthogonal_rows}, out / "pharmacology_orthogonality.png")
    return {"paper_09": {"same_axis": redundant_summary, "cross_axis": orthogonal_summary}}


if __name__ == "__main__":
    main()
    print("Wrote Part III pharmacology diagnostic to outputs/paper_09")
