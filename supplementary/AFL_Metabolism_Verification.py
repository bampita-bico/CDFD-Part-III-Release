"""Release-local Part III metabolic AFL diagnostics.

These diagnostics use the public CDFD Runtime state object and biology update.
They are toy consistency checks for manuscript figures and tables, not clinical
validation of insulin resistance, diabetes, CKD, or any treatment claim.
"""
from __future__ import annotations

import numpy as np

from partiii_runtime import (
    State,
    apply_biology,
    centered_mask,
    ensure_output,
    safe_plot,
    state_summary,
    write_csv,
    write_json,
)


def run_metabolic_saturation(steps: int = 360, dt: float = 0.02) -> tuple[list[dict[str, float]], dict[str, object]]:
    state = State(24, 24)
    mask = centered_mask(state, radius=4)
    rows: list[dict[str, float]] = []

    for step in range(steps):
        t = step * dt
        drive = 0.018 if t < 4.0 else 0.004
        state.phi[mask] += drive
        state.phi[~mask] += drive * 0.15
        apply_biology(state, dt=dt)
        state.C = np.maximum(state.C, 0.05)
        state.phi = np.maximum(state.phi, 0.01)
        state.update_psi()
        state.t = t
        if step % 6 == 0:
            rows.append(
                {
                    "t": float(t),
                    "mean_phi": float(np.mean(state.phi)),
                    "mean_C": float(np.mean(state.C)),
                    "mean_psi_s": float(np.mean(state.psi_s)),
                    "center_phi": float(np.mean(state.phi[mask])),
                    "center_C": float(np.mean(state.C[mask])),
                    "center_psi_s": float(np.mean(state.psi_s[mask])),
                }
            )

    summary = {
        "diagnostic": "metabolic_saturation",
        "interpretation": "Sustained substrate drive raises local constraint and produces a plateau-like operating ratio.",
        "clinical_status": "toy model; not diabetes clinical guidance",
        "final_state": state_summary(state),
    }
    return rows, summary


def run_constraint_memory(steps: int = 420, dt: float = 0.02) -> tuple[list[dict[str, float]], dict[str, object]]:
    state = State(24, 24)
    mask = centered_mask(state, radius=4)
    state.beta[mask] = 0.002
    state.beta[~mask] = 0.06
    rows: list[dict[str, float]] = []

    for step in range(steps):
        t = step * dt
        if t < 3.0:
            state.phi[mask] += 0.025
            state.Ms[mask] += 0.0008
        else:
            state.phi[mask] = np.maximum(state.phi[mask] - 0.012, 1.0)
            state.Ms[mask] = np.maximum(state.Ms[mask] - 0.00015, 1.0)
        apply_biology(state, dt=dt)
        state.update_psi()
        state.t = t
        if step % 7 == 0:
            rows.append(
                {
                    "t": float(t),
                    "mean_phi": float(np.mean(state.phi)),
                    "mean_C": float(np.mean(state.C)),
                    "mean_Ms": float(np.mean(state.Ms)),
                    "mean_psi_s": float(np.mean(state.psi_s)),
                    "center_C": float(np.mean(state.C[mask])),
                    "center_Ms": float(np.mean(state.Ms[mask])),
                    "center_psi_s": float(np.mean(state.psi_s[mask])),
                }
            )

    summary = {
        "diagnostic": "constraint_memory",
        "interpretation": "A low-relaxation region retains elevated constraint and memory after a transient load.",
        "clinical_status": "toy model; not CKD, fibrosis, or metabolic disease validation",
        "final_state": state_summary(state),
    }
    return rows, summary


def write_figure(rows: list[dict[str, float]], path) -> None:
    plt = safe_plot()
    if plt is None:
        return
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot([r["t"] for r in rows], [r["center_phi"] if "center_phi" in r else r["mean_phi"] for r in rows], label="center Phi")
    ax.plot([r["t"] for r in rows], [r["center_C"] for r in rows], label="center C")
    ax.plot([r["t"] for r in rows], [r["center_psi_s"] for r in rows], label="center Psi_s")
    ax.set_xlabel("model time")
    ax.set_ylabel("normalized value")
    ax.set_title("Part III metabolic AFL toy diagnostic")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def main() -> dict[str, object]:
    out = ensure_output("paper_05")
    saturation_rows, saturation_summary = run_metabolic_saturation()
    memory_rows, memory_summary = run_constraint_memory()

    write_csv(out / "metabolic_saturation_timeseries.csv", saturation_rows)
    write_csv(out / "constraint_memory_timeseries.csv", memory_rows)
    write_json(out / "summary.json", {"metabolic_saturation": saturation_summary, "constraint_memory": memory_summary})
    write_figure(saturation_rows, out / "metabolic_saturation.png")
    write_figure(memory_rows, out / "constraint_memory.png")
    return {"paper_05": {"metabolic_saturation": saturation_summary, "constraint_memory": memory_summary}}


if __name__ == "__main__":
    result = main()
    print("Wrote Part III metabolic diagnostics to outputs/paper_05")
    print(result["paper_05"]["metabolic_saturation"]["interpretation"])
