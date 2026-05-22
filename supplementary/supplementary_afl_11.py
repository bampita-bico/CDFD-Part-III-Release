"""
Supplementary — AFL Part III Paper 11
Adaptive Flux Limitation in Bioelectric Regulation: Membrane Potential as Constraint Controller

C_mem = C0 * exp(-kappa_v * (V_m - V_rest))

Simulations: (A) voltage-dependent constraint table across physiological V_m range;
(B) pacemaker oscillation (cardiac/neural analogy); (C) 1-D spatial bioelectric
field propagation via gap junction coupling; (D) therapeutic reset toy scenario.

kappa_v is a voltage-sensitivity parameter (mV^-1) — unrelated to CDFD vacuum kappa.
All outputs are toy diagnostics. Bioelectric therapies require clinical trials.

Outputs: outputs/paper_11/
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from partiii_runtime import ensure_output, laplacian_1d, operating_ratio, regime_label, safe_plot, write_csv, write_json

DT = 0.04
STEPS = 600
KAPPA_S = 0.05
D_M = 0.01
N_CELLS = 80
V_REST = -70.0  # mV
C0 = 1.5
KAPPA_V = 0.05  # mV^-1


def membrane_constraint(V_m: float | np.ndarray) -> float | np.ndarray:
    return C0 * np.exp(-KAPPA_V * (V_m - V_REST))


def _voltage_table() -> list[dict]:
    Vm_values = [-90, -80, -70, -60, -50, -40, -30, -20, -10, 0, 10]
    Phi_ion = 1.0
    rows = []
    for Vm in Vm_values:
        Cm = float(membrane_constraint(Vm))
        psi = operating_ratio(Phi_ion, Cm, 1.0, 1.0)
        if Vm < V_REST - 5:
            label = "hyperpolarised"
        elif abs(Vm - V_REST) <= 5:
            label = "resting"
        elif Vm < -30:
            label = "partially depolarised"
        else:
            label = "depolarised (tumour-like)"
        rows.append({
            "V_m_mV": Vm, "C_mem": round(Cm, 4),
            "Psi_s": round(psi, 4), "state": label,
            "regime": regime_label(psi),
        })
    return rows


def _pacemaker_sim() -> list[dict]:
    V_m = np.full(N_CELLS, V_REST)
    Phi = np.ones(N_CELLS) * 1.0
    S = np.ones(N_CELLS)
    M_s = np.ones(N_CELLS) * 0.2
    D_gap = 0.3  # gap junction coupling

    rows = []
    for step in range(STEPS):
        # pacemaker cells (indices 0-5) receive periodic drive
        drive = 20.0 * (1.0 if (step % 80) < 20 else 0.0)
        V_m[:6] += DT * drive

        # gap junction diffusion
        V_m += DT * D_gap * laplacian_1d(V_m)
        V_m = np.clip(V_m, -100.0, 50.0)

        C_mem = membrane_constraint(V_m)
        psi = (Phi / np.maximum(C_mem, 1e-9)) * S * M_s
        M_s = np.maximum(M_s + DT * np.clip(Phi * S - D_M * M_s, -10.0, 10.0), 0.0)
        S = np.maximum(S + DT * np.clip(KAPPA_S * (psi - S), -10.0, 10.0), 0.01)

        rows.append({
            "step": step, "t": round(step * DT, 3),
            "mean_Vm": round(float(np.mean(V_m)), 4),
            "mean_C_mem": round(float(np.mean(C_mem)), 4),
            "mean_psi": round(float(np.mean(psi)), 4),
            "pacemaker_Vm": round(float(V_m[0]), 4),
        })
    return rows


def _spatial_snapshot(step_idx: int = 400) -> list[dict]:
    """1-D spatial bioelectric field at a given step."""
    V_m = np.full(N_CELLS, V_REST)
    D_gap = 0.3
    for step in range(step_idx + 1):
        drive = 20.0 * (1.0 if (step % 80) < 20 else 0.0)
        V_m[:6] += DT * drive
        V_m += DT * D_gap * laplacian_1d(V_m)
        V_m = np.clip(V_m, -100.0, 50.0)
    C_mem = membrane_constraint(V_m)
    psi = Phi_ion = operating_ratio(1.0, 1.0, 1.0, 1.0)  # placeholder to show spatial C
    return [
        {"cell": i, "V_m": round(float(V_m[i]), 3), "C_mem": round(float(C_mem[i]), 4)}
        for i in range(N_CELLS)
    ]


def _reset_scenario() -> list[dict]:
    """Therapeutic reset: external field briefly hyperpolarises depolarised tissue."""
    V_m = -30.0  # starting depolarised (tumour-like)
    rows = []
    for step in range(500):
        # therapeutic pulse applied between steps 100-150
        if 100 <= step < 150:
            V_m -= DT * 5.0  # hyperpolarising push
        else:
            V_m += DT * 0.5 * (V_REST - V_m)  # passive drift toward rest
        Cm = float(membrane_constraint(V_m))
        psi = operating_ratio(1.0, Cm, 1.0, 1.0)
        rows.append({
            "step": step, "V_m": round(V_m, 3), "C_mem": round(Cm, 4),
            "psi": round(psi, 4), "regime": regime_label(psi),
            "phase": "therapeutic" if 100 <= step < 150 else "free",
        })
    return rows


def main() -> None:
    out = ensure_output("paper_11")

    table = _voltage_table()
    pacemaker = _pacemaker_sim()
    spatial = _spatial_snapshot()
    reset = _reset_scenario()

    write_csv(out / "membrane_constraint_profiles.csv", table)
    write_csv(out / "pacemaker_dynamics.csv", pacemaker)
    write_csv(out / "spatial_bioelectric.csv", spatial)
    write_csv(out / "reset_scenario.csv", reset)

    write_json(out / "summary.json", {
        "paper": "11",
        "title": "Adaptive Flux Limitation in Bioelectric Regulation",
        "simulations": ["voltage_table", "pacemaker", "spatial_field", "therapeutic_reset"],
        "claim_status": "toy diagnostic — experimental framework only",
        "validation_targets": [
            "Patch clamp: C_mem proxy across hyperpolarised vs depolarised cells",
            "Voltage-sensitive dyes / optogenetics: spatial bioelectric field mapping",
            "ECG/EEG: rhythm vs AFL pacemaker coupling analogy",
            "Organoid bioelectric assays: gap junction manipulation and Psi change",
        ],
        "safety_note": (
            "Bioelectric therapeutic claims require clinical trial evidence. "
            "This model is a research framing tool, not a treatment guide."
        ),
        "falsification": (
            "If membrane potential change does not correlate with metabolic flux "
            "rate after controlling for direct ion current effects, C_mem as AFL "
            "constraint provides no additional explanatory power."
        ),
    })

    plt = safe_plot()
    if plt is not None:
        fig, axes = plt.subplots(1, 3, figsize=(17, 4.5), constrained_layout=True)

        ax = axes[0]
        Vm_v = [r["V_m_mV"] for r in table]
        psi_v = [r["Psi_s"] for r in table]
        cm_v = [r["C_mem"] for r in table]
        ax.plot(Vm_v, psi_v, color="#1f77b4", marker="o", lw=1.5, label="Psi_s")
        ax2 = ax.twinx()
        ax2.plot(Vm_v, cm_v, color="#d62728", marker="s", lw=1.3, ls="--", label="C_mem")
        ax.axhline(1.2, color="grey", lw=0.8, ls=":")
        ax.set_xlabel("V_m (mV)"); ax.set_ylabel("Psi_s", color="#1f77b4")
        ax2.set_ylabel("C_mem (toy)", color="#d62728")
        ax.set_title("Membrane Potential → Constraint → Psi_s")

        ax = axes[1]
        t = [r["t"] for r in pacemaker]
        ax.plot(t, [r["pacemaker_Vm"] for r in pacemaker], color="#2ca02c", lw=1.2, label="V_m (pacemaker)")
        ax.plot(t, [r["mean_psi"] * 10 for r in pacemaker], color="#ff7f0e", lw=1.2, ls="--", label="Psi_s ×10")
        ax.set_xlabel("Time (toy)"); ax.set_ylabel("V_m / Psi_s (toy)")
        ax.set_title("Pacemaker Oscillation: V_m and Psi_s")
        ax.legend(frameon=False, fontsize=7)

        ax = axes[2]
        t_r = [r["step"] for r in reset]
        ax.plot(t_r, [r["V_m"] for r in reset], color="#9467bd", lw=1.4, label="V_m (mV)")
        ax.axvspan(100, 150, alpha=0.15, color="red", label="Therapeutic pulse")
        ax.axhline(V_REST, color="grey", lw=0.8, ls=":", label="V_rest")
        ax.set_xlabel("Step"); ax.set_ylabel("V_m (mV)")
        ax.set_title("Therapeutic Reset: Membrane Potential")
        ax.legend(frameon=False, fontsize=7)

        fig.suptitle("Adaptive Flux Limitation Paper 11 - Toy Diagnostics: Bioelectric Regulation (not clinical predictions)", fontweight="bold")
        fig.savefig(out / "bioelectric_regulation.png", dpi=220)
        plt.close(fig)

    print(f"Paper 11 outputs → {out}/")


if __name__ == "__main__":
    main()
