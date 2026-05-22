"""Release-local biological AFL tests for Part III.

The runs here are model diagnostics for the manuscript archive. They test
qualitative CDFD/AFL behavior and deliberately avoid clinical validation language.
"""
from __future__ import annotations

import numpy as np

from partiii_runtime import (
    State,
    apply_biology,
    apply_medicine,
    centered_mask,
    ensure_output,
    safe_plot,
    state_summary,
    write_csv,
    write_json,
)


def run_parasitic_drain(steps: int = 300, dt: float = 0.02) -> tuple[list[dict[str, float]], dict[str, object]]:
    state = State(28, 28)
    lesion = centered_mask(state, radius=3)
    state.S[lesion] = 0.08
    rows: list[dict[str, float]] = []

    for step in range(steps):
        t = step * dt
        state.phi[lesion] += 0.035
        state.C[lesion] += 0.003
        apply_biology(state, dt=dt)
        state.update_psi()
        state.t = t
        if step % 6 == 0:
            rows.append(
                {
                    "t": float(t),
                    "lesion_phi": float(np.mean(state.phi[lesion])),
                    "lesion_S": float(np.mean(state.S[lesion])),
                    "lesion_psi_s": float(np.mean(state.psi_s[lesion])),
                    "system_C": float(np.mean(state.C)),
                    "system_psi_s": float(np.mean(state.psi_s)),
                }
            )

    summary = {
        "diagnostic": "parasitic_drain",
        "interpretation": "A high-flow, low-responsiveness node perturbs the surrounding operating ratio.",
        "clinical_status": "toy model; candidate analogy for oncology, viral foci, or biofilm systems only",
        "final_state": state_summary(state),
    }
    return rows, summary


def run_boundary_covariance(steps: int = 240, dt: float = 0.02) -> tuple[list[dict[str, float]], dict[str, object]]:
    responsive = State(20, 20)
    failing = State(20, 20)
    rows: list[dict[str, float]] = []

    for step in range(steps):
        t = step * dt
        load = 0.012 if t < 3.0 else 0.004
        responsive.phi += load
        failing.phi += load
        responsive.S = np.minimum(responsive.S + 0.0015, 1.2)
        failing.S = np.maximum(failing.S - 0.0025, 0.35)
        apply_biology(responsive, dt=dt)
        apply_biology(failing, dt=dt)
        responsive.update_psi()
        failing.update_psi()
        responsive.t = failing.t = t
        if step % 6 == 0:
            rows.append(
                {
                    "t": float(t),
                    "responsive_S": float(np.mean(responsive.S)),
                    "responsive_psi_s": float(np.mean(responsive.psi_s)),
                    "failing_S": float(np.mean(failing.S)),
                    "failing_psi_s": float(np.mean(failing.psi_s)),
                    "psi_gap": float(np.mean(failing.psi_s) - np.mean(responsive.psi_s)),
                }
            )

    summary = {
        "diagnostic": "boundary_covariance",
        "interpretation": "Matched flow produces different operating ratios when surface responsiveness diverges.",
        "clinical_status": "toy model; not a validated endothelial, epithelial, or gut-barrier test",
        "responsive_final": state_summary(responsive),
        "failing_final": state_summary(failing),
    }
    return rows, summary


def run_cycling_retention(steps: int = 360, dt: float = 0.02) -> tuple[list[dict[str, float]], dict[str, object]]:
    cyclic = State(20, 20)
    chronic = State(20, 20)
    rows: list[dict[str, float]] = []

    for step in range(steps):
        t = step * dt
        cycle_on = (step // 45) % 2 == 0
        cyclic.phi += 0.018 if cycle_on else -0.014
        chronic.phi += 0.006
        cyclic.phi = np.maximum(cyclic.phi, 0.7)
        chronic.phi = np.maximum(chronic.phi, 0.7)
        cyclic.Ms += 0.0006 if cycle_on else -0.0010
        chronic.Ms += 0.00035
        cyclic.Ms = np.maximum(cyclic.Ms, 1.0)
        chronic.Ms = np.maximum(chronic.Ms, 1.0)
        apply_biology(cyclic, dt=dt)
        apply_biology(chronic, dt=dt)
        cyclic.update_psi()
        chronic.update_psi()
        cyclic.t = chronic.t = t
        if step % 6 == 0:
            rows.append(
                {
                    "t": float(t),
                    "cyclic_phi": float(np.mean(cyclic.phi)),
                    "cyclic_Ms": float(np.mean(cyclic.Ms)),
                    "cyclic_psi_s": float(np.mean(cyclic.psi_s)),
                    "chronic_phi": float(np.mean(chronic.phi)),
                    "chronic_Ms": float(np.mean(chronic.Ms)),
                    "chronic_psi_s": float(np.mean(chronic.psi_s)),
                }
            )

    summary = {
        "diagnostic": "cycling_retention",
        "interpretation": "Equal qualitative stress can diverge depending on recovery windows and memory retention.",
        "clinical_status": "toy model; not a fasting, exercise, or therapy recommendation",
        "cyclic_final": state_summary(cyclic),
        "chronic_final": state_summary(chronic),
    }
    return rows, summary


def run_autoimmune_boundary(steps: int = 240, dt: float = 0.02) -> tuple[list[dict[str, float]], dict[str, object]]:
    global_rx = State(20, 20)
    targeted_rx = State(20, 20)
    for state, treatment in [(global_rx, "global_immunosuppression"), (targeted_rx, "afl_targeted_clearance")]:
        state.meta["autoimmune_state_active"] = True
        state.meta["treatment_type"] = treatment
        state.Ms += 0.12
    rows: list[dict[str, float]] = []

    for step in range(steps):
        t = step * dt
        apply_medicine(global_rx, dt=dt)
        apply_medicine(targeted_rx, dt=dt)
        global_rx.update_psi()
        targeted_rx.update_psi()
        global_rx.t = targeted_rx.t = t
        if step % 6 == 0:
            rows.append(
                {
                    "t": float(t),
                    "global_S": float(np.mean(global_rx.S)),
                    "global_Ms": float(np.mean(global_rx.Ms)),
                    "global_psi_s": float(np.mean(global_rx.psi_s)),
                    "targeted_S": float(np.mean(targeted_rx.S)),
                    "targeted_Ms": float(np.mean(targeted_rx.Ms)),
                    "targeted_psi_s": float(np.mean(targeted_rx.psi_s)),
                }
            )

    summary = {
        "diagnostic": "autoimmune_boundary",
        "interpretation": "The model contrasts global responsiveness suppression with a memory-targeted toy intervention.",
        "clinical_status": "toy model; not an autoimmune treatment protocol",
        "global_final": state_summary(global_rx),
        "targeted_final": state_summary(targeted_rx),
    }
    return rows, summary


def write_lines(rows: list[dict[str, float]], path, y_keys: list[str], title: str) -> None:
    plt = safe_plot()
    if plt is None:
        return
    fig, ax = plt.subplots(figsize=(8, 4.5))
    t = [r["t"] for r in rows]
    for key in y_keys:
        ax.plot(t, [r[key] for r in rows], label=key)
    ax.set_xlabel("model time")
    ax.set_ylabel("normalized value")
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def main() -> dict[str, object]:
    paper_07 = ensure_output("paper_07")
    paper_08 = ensure_output("paper_08")
    paper_10 = ensure_output("paper_10")
    paper_17 = ensure_output("paper_17")

    drain_rows, drain_summary = run_parasitic_drain()
    boundary_rows, boundary_summary = run_boundary_covariance()
    cycle_rows, cycle_summary = run_cycling_retention()
    immune_rows, immune_summary = run_autoimmune_boundary()

    write_csv(paper_07 / "parasitic_drain_timeseries.csv", drain_rows)
    write_json(paper_07 / "summary.json", drain_summary)
    write_lines(drain_rows, paper_07 / "parasitic_drain.png", ["lesion_phi", "system_C", "system_psi_s"], "Parasitic-drain toy diagnostic")

    write_csv(paper_10 / "boundary_covariance_timeseries.csv", boundary_rows)
    write_json(paper_10 / "summary.json", boundary_summary)
    write_lines(boundary_rows, paper_10 / "boundary_covariance.png", ["responsive_psi_s", "failing_psi_s"], "Boundary-covariance toy diagnostic")

    write_csv(paper_17 / "cycling_retention_timeseries.csv", cycle_rows)
    write_json(paper_17 / "summary.json", cycle_summary)
    write_lines(cycle_rows, paper_17 / "cycling_retention.png", ["cyclic_psi_s", "chronic_psi_s"], "Cycling-retention toy diagnostic")

    write_csv(paper_08 / "autoimmune_boundary_timeseries.csv", immune_rows)
    write_json(paper_08 / "summary.json", immune_summary)
    write_lines(immune_rows, paper_08 / "autoimmune_boundary.png", ["global_psi_s", "targeted_psi_s"], "Autoimmune-boundary toy diagnostic")

    return {
        "paper_07": drain_summary,
        "paper_08": immune_summary,
        "paper_10": boundary_summary,
        "paper_17": cycle_summary,
    }


if __name__ == "__main__":
    main()
    print("Wrote Part III biological test diagnostics to outputs/paper_07, paper_08, paper_10, and paper_17")
