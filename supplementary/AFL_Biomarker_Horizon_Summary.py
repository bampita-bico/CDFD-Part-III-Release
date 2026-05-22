"""Part III biomarker trajectory toy diagnostic.

This script generates normalized biomarker trajectories for Paper 16. It is a
release-local consistency check for the claim that constraint proxies can rise
before flux proxies fall in some modeled disease-progressor scenarios. It is
not a diagnostic, prognostic, or treatment tool.
"""
from __future__ import annotations

import numpy as np

from partiii_runtime import ensure_output, safe_plot, write_csv, write_json


SCENARIOS = {
    "healthy": {"load": 0.72, "alpha": 0.018, "beta": 0.32, "flux_sensitivity": 0.18, "memory_rate": 0.010},
    "early_disease": {"load": 1.18, "alpha": 0.055, "beta": 0.14, "flux_sensitivity": 0.36, "memory_rate": 0.024},
    "decompensated": {"load": 1.58, "alpha": 0.090, "beta": 0.055, "flux_sensitivity": 0.55, "memory_rate": 0.044},
}


def simulate_scenario(name: str, params: dict[str, float], steps: int = 240, dt: float = 0.05) -> tuple[list[dict[str, float | str | int]], dict[str, object]]:
    rng = np.random.default_rng(1600 + len(name))
    phi = 1.0
    constraint = 1.0
    responsiveness = 1.0
    memory = 1.0
    rows: list[dict[str, float | str | int]] = []

    first_constraint_signal: float | None = None
    first_flux_decline: float | None = None

    for step in range(steps):
        t = step * dt
        load = params["load"] * (1.0 + 0.04 * np.sin(t / 1.7))
        load += float(rng.normal(0.0, 0.003))
        constraint += dt * (params["alpha"] * load - params["beta"] * max(constraint - 1.0, 0.0))
        constraint = max(constraint, 0.65)

        stress = max(constraint - 1.10, 0.0)
        phi_target = max(0.45, 1.0 - params["flux_sensitivity"] * stress)
        phi += 0.12 * (phi_target - phi)
        responsiveness = max(0.45, 1.0 - 0.20 * max(constraint - 1.0, 0.0))
        memory += dt * (params["memory_rate"] * max(constraint - 1.0, 0.0) - 0.030 * max(memory - 1.0, 0.0))
        psi_s_proxy = (phi / constraint) * responsiveness * memory

        if first_constraint_signal is None and constraint >= 1.10:
            first_constraint_signal = t
        if first_flux_decline is None and phi <= 0.94:
            first_flux_decline = t

        if step % 4 == 0:
            rows.append(
                {
                    "scenario": name,
                    "t": float(t),
                    "flux_proxy_phi": float(phi),
                    "constraint_proxy_C": float(constraint),
                    "responsiveness_S": float(responsiveness),
                    "memory_Ms": float(memory),
                    "psi_s_proxy": float(psi_s_proxy),
                    "constraint_signal": int(constraint >= 1.10),
                    "flux_decline_signal": int(phi <= 0.94),
                }
            )

    lead_time = None
    if first_constraint_signal is not None and first_flux_decline is not None:
        lead_time = first_flux_decline - first_constraint_signal

    summary = {
        "diagnostic": "biomarker_horizon_summary",
        "scenario": name,
        "interpretation": "Normalized toy trajectory for constraint-before-flux biomarker behavior.",
        "clinical_status": "toy model; not a diagnostic, prognostic, or treatment tool",
        "thresholds": {"constraint_proxy_C": 1.10, "flux_proxy_phi": 0.94},
        "first_constraint_signal_t": first_constraint_signal if first_constraint_signal is not None else "not_reached",
        "first_flux_decline_t": first_flux_decline if first_flux_decline is not None else "not_reached",
        "constraint_lead_time": lead_time if lead_time is not None else "not_reached",
        "final_state": {
            "flux_proxy_phi": float(phi),
            "constraint_proxy_C": float(constraint),
            "responsiveness_S": float(responsiveness),
            "memory_Ms": float(memory),
            "psi_s_proxy": float(psi_s_proxy),
        },
    }
    return rows, summary


def write_plot(series: dict[str, list[dict[str, float | str | int]]], path) -> None:
    plt = safe_plot()
    if plt is None:
        return
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for name, rows in series.items():
        t = [float(r["t"]) for r in rows]
        ax.plot(t, [float(r["constraint_proxy_C"]) for r in rows], label=f"{name} C")
        ax.plot(t, [float(r["flux_proxy_phi"]) for r in rows], linestyle="--", label=f"{name} Phi")
    ax.axhline(1.10, color="black", linewidth=0.8, linestyle=":", label="C signal threshold")
    ax.axhline(0.94, color="gray", linewidth=0.8, linestyle=":", label="Phi decline threshold")
    ax.set_xlabel("model time")
    ax.set_ylabel("normalized proxy")
    ax.set_title("AFL biomarker constraint-before-flux toy diagnostic")
    ax.legend(ncol=2, fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def main() -> dict[str, object]:
    out = ensure_output("paper_16")
    all_rows: list[dict[str, float | str | int]] = []
    series: dict[str, list[dict[str, float | str | int]]] = {}
    summaries: dict[str, object] = {}

    for name, params in SCENARIOS.items():
        rows, summary = simulate_scenario(name, params)
        series[name] = rows
        all_rows.extend(rows)
        summaries[name] = summary

    write_csv(out / "biomarker_horizon_timeseries.csv", all_rows)
    write_json(out / "summary.json", summaries)
    write_plot(series, out / "biomarker_horizon.png")
    return {"paper_16": summaries}


if __name__ == "__main__":
    main()
    print("Wrote Part III biomarker horizon diagnostic to outputs/paper_16")
