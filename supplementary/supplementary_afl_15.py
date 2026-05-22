"""
Supplementary — AFL Part III Paper 15
Adaptive Flux Limitation in Microbial Systems: AMR, Stewardship, and HGT

Three toy simulations: (A) antibiotic resistance cycle — fitness cost of resistance
vs antibiotic pressure; (B) horizontal gene transfer (HGT) — constraint propagation
across species; (C) stewardship scenario — dose-escalation vs de-escalation.

AMR framing aligned with WHO AMR Report 2021 and CDC AMR guidelines.
This model is NOT clinical guidance. Stewardship decisions require
clinical expertise, culture results, and institutional guidelines.

Outputs: outputs/paper_15/
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from partiii_runtime import ensure_output, euler_step, operating_ratio, regime_label, safe_plot, write_csv, write_json

DT = 0.04
STEPS = 700
KAPPA_S = 0.04
D_M = 0.006
ALPHA_BASE = 0.06
BETA_BASE = 0.03


def _resistance_cycle(steps: int = 700) -> list[dict]:
    """
    Sensitive strain (phi_s) competes with resistant strain (phi_r).
    Resistance fitness cost: resistant strain has lower phi when antibiotic absent.
    AFL: antibiotic = constraint on sensitive phi; resistance lowers C_drug.
    """
    phi_s, phi_r = 2.0, 1.5  # sensitive has fitness advantage when drug absent
    c_s, c_r = 0.5, 0.5
    s_s, ms_s = 1.0, 0.2
    s_r, ms_r = 1.0, 0.2
    rows = []
    for i in range(steps):
        # Antibiotic applied from step 150–350
        drug_on = 150 <= i < 350
        c_drug_s = 3.0 if drug_on else 0.0   # drug heavily constrains sensitive
        c_drug_r = 0.3 if drug_on else 0.0   # resistant strain barely constrained

        c_s_eff = c_s + c_drug_s
        c_r_eff = c_r + c_drug_r

        c_s, s_s, ms_s = euler_step(phi_s, c_s_eff, s_s, ms_s, ALPHA_BASE, BETA_BASE, KAPPA_S, D_M, DT)
        c_r, s_r, ms_r = euler_step(phi_r, c_r_eff, s_r, ms_r, ALPHA_BASE, BETA_BASE, KAPPA_S, D_M, DT)
        # Revert to intrinsic C after drug subtracted
        c_s = max(c_s - c_drug_s * DT, 1e-9)
        c_r = max(c_r - c_drug_r * DT, 1e-9)

        psi_s = operating_ratio(phi_s, c_s + c_drug_s, s_s, ms_s)
        psi_r = operating_ratio(phi_r, c_r + c_drug_r, s_r, ms_r)

        rows.append({
            "step": i, "t": round(i * DT, 3),
            "psi_sensitive": round(psi_s, 4),
            "psi_resistant": round(psi_r, 4),
            "drug_on": drug_on,
            "regime_sensitive": regime_label(psi_s),
            "regime_resistant": regime_label(psi_r),
        })
    return rows


def _hgt_sim(n_species: int = 6, steps: int = 500) -> list[dict]:
    """HGT toy: resistance gene transfer raises C_drug_sensitivity in receiving species."""
    phi = np.ones(n_species) * 1.8
    c = np.random.default_rng(9).uniform(0.4, 0.8, n_species)
    s = np.ones(n_species)
    ms = np.ones(n_species) * 0.2
    hgt_rate = 0.003
    rows = []
    for i in range(steps):
        psi = np.array([operating_ratio(phi[j], c[j], s[j], ms[j]) for j in range(n_species)])
        # HGT: species with high Psi_s share resistance (lower effective C_drug)
        donor = np.argmax(psi)
        for j in range(n_species):
            if j != donor:
                c[j] = max(c[j] - DT * hgt_rate * max(0.0, psi[donor] - psi[j]), 1e-9)
        for j in range(n_species):
            dc = ALPHA_BASE * phi[j] - BETA_BASE * c[j]
            c[j] = max(c[j] + DT * dc, 1e-9)
            dpsi = operating_ratio(phi[j], c[j], s[j], ms[j])
            s[j] = max(s[j] + DT * KAPPA_S * (dpsi - s[j]), 0.01)
            ms[j] = max(ms[j] + DT * np.clip(phi[j] * s[j] - D_M * ms[j], -10.0, 10.0), 0.0)
        rows.append({
            "step": i, "t": round(i * DT, 3),
            "mean_psi": round(float(np.mean(psi)), 4),
            "std_psi": round(float(np.std(psi)), 4),
            "donor_species": int(donor),
        })
    return rows


def _stewardship_scenarios() -> list[dict]:
    """De-escalation vs dose-escalation vs combination: AFL axis map."""
    SCENARIOS = [
        ("Dose-escalation", 0.10, 0.02, "increased Phi demand on constraint"),
        ("De-escalation",   0.04, 0.04, "lower alpha; faster beta recovery"),
        ("Combination",     0.06, 0.04, "orthogonal axes; balanced relaxation"),
        ("No treatment",    0.00, 0.02, "no AFL drug axis; unconstrained resistance"),
    ]
    rows = []
    for (label, alpha, beta, note) in SCENARIOS:
        phi, c, s, ms = 2.0, 0.8, 1.0, 0.2
        psi_h = []
        for _ in range(500):
            c, s, ms = euler_step(phi, c, s, ms, alpha, beta, KAPPA_S, D_M, DT)
            psi_h.append(operating_ratio(phi, c, s, ms))
        rows.append({
            "strategy": label, "alpha": alpha, "beta": beta,
            "final_psi": round(psi_h[-1], 4),
            "regime": regime_label(psi_h[-1]),
            "note": note,
            "claim_status": "axis map only — not clinical guidance",
        })
    return rows


def main() -> None:
    out = ensure_output("paper_15")

    resist = _resistance_cycle()
    hgt = _hgt_sim()
    stewardship = _stewardship_scenarios()

    write_csv(out / "resistance_cycle.csv", resist)
    write_csv(out / "hgt_dynamics.csv", hgt)
    write_csv(out / "stewardship_scenarios.csv", stewardship)

    write_json(out / "summary.json", {
        "paper": "15",
        "title": "Adaptive Flux Limitation in Microbial Systems",
        "simulations": ["resistance_cycle", "hgt_dynamics", "stewardship_scenarios"],
        "claim_status": "toy diagnostic — NOT clinical guidance",
        "guideline_anchors": [
            "WHO AMR Report 2021 (IACG): resistance, stewardship, HGT, public health",
            "CDC AMR Guidelines: diagnostics, treatment duration, de-escalation",
        ],
        "validation_targets": [
            "In vitro resistance fitness cost assays: growth rate vs antibiotic pressure",
            "HGT plasmid transfer experiments: resistance spread rate vs Phi/C analogy",
            "Retrospective AMR registry: stewardship strategy vs outcome correlation",
            "Wastewater AMR surveillance: community resistance load as C proxy",
        ],
        "safety_note": (
            "Antibiotic holiday / de-escalation decisions require clinical judgement, "
            "culture and sensitivity data, and institutional guidelines. This model "
            "is a framing tool, not prescriptive."
        ),
        "falsification": (
            "If resistance fitness cost is uncorrelated with AFL constraint relaxation "
            "dynamics after drug withdrawal in controlled in vitro experiments, the "
            "resistance-cycle framing does not hold."
        ),
    })

    plt = safe_plot()
    if plt is not None:
        t_r = [r["t"] for r in resist]
        t_h = [r["t"] for r in hgt]
        fig, axes = plt.subplots(1, 3, figsize=(17, 4.5), constrained_layout=True)

        ax = axes[0]
        ax.plot(t_r, [r["psi_sensitive"] for r in resist], color="#1f77b4", lw=1.4, label="Sensitive")
        ax.plot(t_r, [r["psi_resistant"] for r in resist], color="#d62728", lw=1.4, ls="--", label="Resistant")
        drug_on_t = [r["t"] for r in resist if r["drug_on"]]
        if drug_on_t:
            ax.axvspan(drug_on_t[0], drug_on_t[-1], alpha=0.12, color="orange", label="Antibiotic on")
        ax.axhline(0.8, color="grey", lw=0.7, ls=":")
        ax.axhline(1.2, color="grey", lw=0.7, ls=":")
        ax.set_xlabel("Time (toy)"); ax.set_ylabel("Psi_s (toy)")
        ax.set_title("Resistance Cycle: Sensitive vs Resistant")
        ax.legend(frameon=False, fontsize=7)

        ax = axes[1]
        ax.plot(t_h, [r["mean_psi"] for r in hgt], color="#2ca02c", lw=1.4, label="Mean Psi_s")
        ax.fill_between(t_h,
            [r["mean_psi"] - r["std_psi"] for r in hgt],
            [r["mean_psi"] + r["std_psi"] for r in hgt],
            alpha=0.2, color="#2ca02c")
        ax.set_xlabel("Time (toy)"); ax.set_ylabel("Mean Psi_s (toy)")
        ax.set_title("HGT: Community Psi_s Convergence")
        ax.legend(frameon=False, fontsize=7)

        ax = axes[2]
        labels = [r["strategy"] for r in stewardship]
        psi_v = [r["final_psi"] for r in stewardship]
        colors = ["#1f77b4", "#2ca02c", "#ff7f0e", "#d62728"]
        ax.bar(range(len(labels)), psi_v, color=colors, alpha=0.85)
        ax.set_xticks(range(len(labels))); ax.set_xticklabels(labels, rotation=20, ha="right", fontsize=7)
        ax.axhline(0.8, color="grey", lw=0.8, ls=":")
        ax.axhline(1.2, color="grey", lw=0.8, ls=":")
        ax.set_ylabel("Final Psi_s (toy)")
        ax.set_title("Stewardship Axis Map (not clinical guidance)")

        fig.suptitle("AFL Paper 15 — Toy Diagnostics: AMR Dynamics (not clinical guidance)", fontweight="bold")
        fig.savefig(out / "microbial_resistance_afl.png", dpi=220)
        plt.close(fig)

    print(f"Paper 15 outputs → {out}/")


if __name__ == "__main__":
    main()
