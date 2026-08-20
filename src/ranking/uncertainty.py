"""Conformal / bootstrap uncertainty intervals for expected CAR rankings."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import load_yaml, project_root
from src.return_models.expected_car import _bootstrap_interval, load_bundle, predict_expected_car
from src.return_models.dataset import load_catalyst_modeling_frame


def _load_oos_residuals(db_path: Path) -> np.ndarray:
    """Prefer walk-forward OOS residuals; fall back to in-sample."""
    conn = sqlite3.connect(db_path)
    try:
        wf = pd.read_sql_query(
            "SELECT expected_car, realized_car FROM walk_forward_ledger WHERE realized_car IS NOT NULL",
            conn,
        )
    except Exception:
        wf = pd.DataFrame()
    conn.close()

    if not wf.empty and len(wf) >= 10:
        return (wf["realized_car"] - wf["expected_car"]).values

    df = load_catalyst_modeling_frame(db_path)
    model_path = project_root() / "data" / "processed" / "models" / "expected_car_v1.pkl"
    if model_path.exists():
        preds = predict_expected_car(df, load_bundle(model_path))
        return (preds["realized_car"] - preds["expected_car"]).values
    return (df["realized_car"] - df["realized_car"].mean()).values


def conformal_interval(
    point_estimate: float | np.ndarray,
    residuals: np.ndarray,
    alpha: float = 0.10,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Symmetric conformal interval using absolute OOS calibration residuals.

    Covers ~(1-alpha) of held-out errors under exchangeability.
    """
    if len(residuals) == 0:
        arr = np.asarray(point_estimate, dtype=float)
        return arr, arr
    q = float(np.quantile(np.abs(residuals), 1 - alpha / 2))
    est = np.asarray(point_estimate, dtype=float)
    return est - q, est + q


def bootstrap_expected_car_intervals(
    expected_car: np.ndarray,
    residuals: np.ndarray,
    n_boot: int = 500,
    seed: int = 42,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Bootstrap interval: perturb point estimate with resampled OOS residuals.
    """
    rng = np.random.default_rng(seed)
    if len(residuals) == 0:
        return expected_car.copy(), expected_car.copy()
    est = np.asarray(expected_car, dtype=float)
    n = len(est)
    lowers = np.zeros((n_boot, n))
    uppers = np.zeros((n_boot, n))
    for b in range(n_boot):
        noise = rng.choice(residuals, size=n, replace=True)
        sampled = est + noise
        lowers[b] = sampled
        uppers[b] = sampled
    return (
        np.percentile(lowers, 2.5, axis=0),
        np.percentile(uppers, 97.5, axis=0),
    )


def add_uncertainty_columns(
    preds: pd.DataFrame,
    db_path: Path | None = None,
    alpha: float = 0.10,
    method: str = "conformal",
) -> pd.DataFrame:
    """Add expected_car_lo/hi and exposure-adjusted CI columns."""
    cfg = load_yaml(project_root() / "configs" / "stock_picking.yaml")
    seed = cfg["random_seed"]
    db_path = db_path or project_root() / "data" / "processed" / "research.db"
    residuals = _load_oos_residuals(db_path)

    out = preds.copy()
    exp = out["expected_car"].values
    if method == "bootstrap":
        lo, hi = bootstrap_expected_car_intervals(exp, residuals, seed=seed)
    else:
        lo, hi = conformal_interval(exp, residuals, alpha=alpha)

    out["expected_car_lo"] = lo
    out["expected_car_hi"] = hi
    out["expected_car_ci_width"] = hi - lo

    dep = out["company_dependency"].fillna(0.9) if "company_dependency" in out.columns else 0.9
    out["expected_car_exposure_adj_lo"] = lo * dep
    out["expected_car_exposure_adj_hi"] = hi * dep
    return out


def classify_confidence_signal(row: pd.Series) -> str:
    """Signal requiring lower CI > 0 (long) or upper CI < 0 (short)."""
    lo = row.get("expected_car_exposure_adj_lo", row.get("expected_car_exposure_adj", 0))
    hi = row.get("expected_car_exposure_adj_hi", row.get("expected_car_exposure_adj", 0))
    if lo > 0:
        return "CONFIDENT LONG"
    if hi < 0:
        return "CONFIDENT SHORT"
    return "UNCERTAIN"
