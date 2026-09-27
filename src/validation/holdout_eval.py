"""Legacy holdout evaluation for the already-inspected 2019–2021 period."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.config import load_yaml, project_root
from src.fundamentals.exposure import load_exposure_frame
from src.return_models.dataset import load_catalyst_modeling_frame, resolve_split_feature_cols
from src.return_models.expected_car import (
    ExpectedCarBundle,
    _bootstrap_interval,
    _fit_conditional_car,
    _make_logistic,
    conditional_car_fallbacks,
    predict_expected_car,
    predict_with_wong_prior,
)


def _fit_bundle(
    train: pd.DataFrame,
    p_cols: list[str],
    car_cols: list[str],
    version: str,
    seed: int,
) -> ExpectedCarBundle:
    p_model = _make_logistic(seed)
    p_model.fit(train[p_cols], train["clinical_success"].astype(int))
    success_fallback, failure_fallback = conditional_car_fallbacks(train)
    return ExpectedCarBundle(
        version=version,
        feature_cols=p_cols,
        p_feature_cols=p_cols,
        car_feature_cols=car_cols,
        p_success_model=p_model,
        car_success_model=_fit_conditional_car(train, car_cols, 1),
        car_failure_model=_fit_conditional_car(train, car_cols, 0),
        car_success_fallback=success_fallback,
        car_failure_fallback=failure_fallback,
        training_data_policy="strict_point_in_time_sanitized",
    )


def _apply_exposure(preds: pd.DataFrame) -> pd.DataFrame:
    exposure = load_exposure_frame()
    out = preds.merge(exposure[["catalyst_id", "company_dependency"]], on="catalyst_id", how="left")
    out["company_dependency"] = out["company_dependency"].fillna(0.9)
    out["expected_car_adj"] = out["expected_car"] * out["company_dependency"]
    return out


def run_locked_holdout(
    feature_set: str = "market_only",
    db_path: Path | None = None,
) -> pd.DataFrame:
    """
    Train on pre-period catalysts and evaluate retrospectively on 2019–2021.
    """
    cfg = load_yaml(project_root() / "configs" / "stock_picking.yaml")
    holdout = cfg["holdout"]["final_locked"]
    start_year = holdout["start_year"]
    end_year = holdout["end_year"]
    seed = cfg["random_seed"]

    df = load_catalyst_modeling_frame(db_path)
    df = df.dropna(subset=["catalyst_year"]).copy()

    train = df[df["catalyst_year"] < start_year]
    test = df[(df["catalyst_year"] >= start_year) & (df["catalyst_year"] <= end_year)]

    if feature_set == "market_plus_preclinical" or feature_set in (
        "market_only",
        "market_plus_trial",
        "market_plus_trial_plus_preclinical",
        "trial_only",
    ):
        p_cols, car_cols = resolve_split_feature_cols(feature_set)
    else:
        p_cols, car_cols = resolve_split_feature_cols("market_plus_trial")

    bundle = _fit_bundle(train, p_cols, car_cols, f"holdout_{feature_set}", seed)
    preds = predict_expected_car(test, bundle)
    preds = _apply_exposure(preds)
    preds["model"] = feature_set
    preds["split"] = "locked_holdout"
    return preds


def run_holdout_baselines(db_path: Path | None = None) -> dict[str, pd.DataFrame]:
    """Full model, preclinical-augmented model, and Wong prior on the legacy period."""
    cfg = load_yaml(project_root() / "configs" / "stock_picking.yaml")
    holdout = cfg["holdout"]["final_locked"]
    start_year = holdout["start_year"]
    end_year = holdout["end_year"]

    df = load_catalyst_modeling_frame(db_path)
    df = df.dropna(subset=["catalyst_year"]).copy()
    train = df[df["catalyst_year"] < start_year]
    test = df[(df["catalyst_year"] >= start_year) & (df["catalyst_year"] <= end_year)]

    results: dict[str, pd.DataFrame] = {}
    for feature_set in (
        "market_only",
        "market_plus_trial",
        "market_plus_preclinical",
        "market_plus_trial_plus_preclinical",
    ):
        results[feature_set] = run_locked_holdout(feature_set, db_path)

    wong = predict_with_wong_prior(test, calibration_df=train)
    wong = _apply_exposure(wong)
    wong["model"] = "wong_prior"
    wong["split"] = "locked_holdout"
    results["wong_prior"] = wong
    return results


def summarize_holdout(preds: pd.DataFrame) -> dict:
    if preds.empty:
        return {"n": 0}

    exp = (
        preds["expected_car_adj"] if "expected_car_adj" in preds.columns else preds["expected_car"]
    )
    realized = preds["realized_car"].dropna()
    exp_aligned = exp.loc[realized.index]

    corr = float(exp_aligned.corr(realized)) if len(realized) > 2 else None
    mean_realized = float(realized.mean())
    mean_expected = float(exp_aligned.mean())

    boot_lo, boot_hi = _bootstrap_interval(realized.values)
    corr_boot_lo, corr_boot_hi = _bootstrap_corr_interval(exp_aligned.values, realized.values)

    long_mask = exp_aligned > 0.03
    short_mask = exp_aligned < -0.03

    return {
        "n": len(preds),
        "n_success": int(preds["clinical_success"].sum()),
        "correlation_expected_realized": corr,
        "correlation_ci_95": (corr_boot_lo, corr_boot_hi),
        "mean_realized_car": mean_realized,
        "mean_realized_car_ci_95": (boot_lo, boot_hi),
        "mean_expected_car_adj": mean_expected,
        "n_long_signals": int(long_mask.sum()),
        "n_short_signals": int(short_mask.sum()),
        "mean_realized_long": float(realized[long_mask].mean()) if long_mask.any() else None,
        "mean_realized_short": float(realized[short_mask].mean()) if short_mask.any() else None,
    }


def _bootstrap_corr_interval(
    x: np.ndarray,
    y: np.ndarray,
    n_boot: int = 500,
    seed: int = 42,
) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    if len(x) < 3:
        return np.nan, np.nan
    corrs = []
    n = len(x)
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        if np.std(x[idx]) == 0 or np.std(y[idx]) == 0:
            continue
        corrs.append(float(np.corrcoef(x[idx], y[idx])[0, 1]))
    if not corrs:
        return np.nan, np.nan
    return float(np.percentile(corrs, 2.5)), float(np.percentile(corrs, 97.5))


def generate_holdout_report(db_path: Path | None = None) -> Path:
    baselines = run_holdout_baselines(db_path)
    cfg = load_yaml(project_root() / "configs" / "stock_picking.yaml")
    holdout = cfg["holdout"]["final_locked"]

    lines = [
        "# Legacy Holdout Evaluation (Not Pristine)",
        "",
        f"**Holdout window:** {holdout['start_year']}–{holdout['end_year']}",
        f"**Training cutoff:** catalysts with year < {holdout['start_year']}",
        "",
        "This period appears in existing repository artifacts and is not a pristine final holdout.",
        "Use a newly timestamped prospective cohort for confirmatory evaluation.",
        "",
    ]

    for name, preds in baselines.items():
        summary = summarize_holdout(preds)
        lines.extend([f"## {name}", ""])
        for k, v in summary.items():
            lines.append(f"- {k}: {v}")
        lines.append("")

    out = project_root() / "reports" / "holdout_evaluation.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")

    csv_path = project_root() / "data" / "processed" / "holdout_predictions.csv"
    all_preds = pd.concat(baselines.values(), ignore_index=True)
    all_preds.to_csv(csv_path, index=False)
    return out
