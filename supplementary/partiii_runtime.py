"""Shared helpers for CDFD Part III release diagnostics."""
from __future__ import annotations

import csv
import json
import os
import sys
from pathlib import Path
from typing import Iterable, Mapping

import numpy as np


RELEASE_ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = RELEASE_ROOT / "outputs"
VALUE_FLOOR = 1e-9
VALUE_CAP = 1e4
PSI_CAP = 1e4


def find_runtime_root() -> Path:
    """Locate the checked-out CDFD Runtime without hard-coding a user path."""
    for parent in [RELEASE_ROOT, *RELEASE_ROOT.parents]:
        candidate = parent / "cdfd_runtime"
        if (candidate / "engine" / "state.py").exists():
            return candidate
    raise RuntimeError("Could not locate cdfd_runtime next to this release archive.")


RUNTIME_ROOT = find_runtime_root()
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

from engine.biology import apply_biology  # noqa: E402
from engine.medicine import apply_medicine  # noqa: E402
from engine.pharmacology import apply_pharmacology  # noqa: E402
from engine.state import State  # noqa: E402


def ensure_output(name: str) -> Path:
    path = OUTPUTS / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def finite_stats(values: np.ndarray) -> dict[str, float | bool]:
    arr = np.asarray(values, dtype=float)
    finite = arr[np.isfinite(arr)]
    if finite.size == 0:
        return {"all_finite": False, "min": float("nan"), "max": float("nan"), "mean": float("nan")}
    return {
        "all_finite": bool(finite.size == arr.size),
        "min": float(np.min(finite)),
        "max": float(np.max(finite)),
        "mean": float(np.mean(finite)),
    }


def clean_json(value):
    if isinstance(value, dict):
        return {str(k): clean_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean_json(v) for v in value]
    if isinstance(value, np.ndarray):
        return clean_json(value.tolist())
    if isinstance(value, (np.floating, float)):
        v = float(value)
        return v if np.isfinite(v) else None
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer, int)):
        return int(value)
    return value


def state_summary(state: State) -> dict[str, object]:
    state.update_psi()
    return {
        "t": float(state.t),
        "phi": finite_stats(state.phi),
        "C": finite_stats(state.C),
        "S": finite_stats(state.S),
        "Ms": finite_stats(state.Ms),
        "psi_s": finite_stats(state.psi_s),
        "regime": state.regime(),
        "meta": dict(state.meta),
    }


def write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.write_text(json.dumps(clean_json(payload), indent=2, sort_keys=True, allow_nan=False))


def write_csv(path: Path, rows: Iterable[Mapping[str, object]]) -> None:
    rows = list(rows)
    if not rows:
        path.write_text("")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def bounded_float(value: object, low: float = 0.0, high: float = VALUE_CAP) -> float:
    """Return a finite toy-model scalar within a declared diagnostic range."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return low
    if not np.isfinite(v):
        return high if v > 0 else low
    return float(np.clip(v, low, high))


# ---------------------------------------------------------------------------
# Standalone AFL math helpers (no engine dependency)
# ---------------------------------------------------------------------------

def laplacian_2d(z: np.ndarray) -> np.ndarray:
    return -4 * z + np.roll(z, 1, 0) + np.roll(z, -1, 0) + np.roll(z, 1, 1) + np.roll(z, -1, 1)


def laplacian_1d(z: np.ndarray) -> np.ndarray:
    return np.roll(z, 1) - 2 * z + np.roll(z, -1)


def operating_ratio(phi: float, c: float, s: float = 1.0, m_s: float = 1.0) -> float:
    phi_b = bounded_float(phi)
    c_b = bounded_float(c, low=VALUE_FLOOR)
    s_b = bounded_float(s, low=0.0)
    ms_b = bounded_float(m_s, low=0.0)
    return bounded_float((phi_b / max(c_b, VALUE_FLOOR)) * s_b * ms_b, high=PSI_CAP)


def regime_label(psi: float, low: float = 0.8, high: float = 1.2) -> str:
    if not np.isfinite(float(psi)):
        return "non-finite"
    if psi < low:
        return "constrained"
    if psi > high:
        return "overload"
    return "balanced"


def euler_step(
    phi: float, c: float, s: float, m_s: float,
    alpha: float, beta: float, kappa_s: float, d_m: float, dt: float,
) -> tuple:
    phi_b = bounded_float(phi)
    c_b = bounded_float(c, low=VALUE_FLOOR)
    s_b = bounded_float(s, low=0.01)
    ms_b = bounded_float(m_s)
    dc = alpha * abs(phi_b) - beta * c_b
    c_new = bounded_float(c_b + dt * dc, low=VALUE_FLOOR)
    psi = operating_ratio(phi_b, c_b, s_b, ms_b)
    s_new = bounded_float(s_b + dt * kappa_s * (psi - s_b), low=0.01)
    dms = np.clip(phi_b * s_b - d_m * ms_b, -VALUE_CAP, VALUE_CAP)
    ms_new = bounded_float(ms_b + dt * dms)
    return c_new, s_new, ms_new


def centered_mask(state: State, radius: int = 3) -> np.ndarray:
    mask = np.zeros_like(state.C, dtype=bool)
    cx, cy = state.nx // 2, state.ny // 2
    mask[max(cx - radius, 0):min(cx + radius, state.nx), max(cy - radius, 0):min(cy + radius, state.ny)] = True
    return mask


def safe_plot() -> object | None:
    try:
        os.environ.setdefault("MPLCONFIGDIR", str(Path("/tmp") / "cdfd_partiii_mplconfig"))
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        return plt
    except Exception:
        return None
