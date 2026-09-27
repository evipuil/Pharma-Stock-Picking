"""Rank catalysts by exposure-adjusted expected CAR."""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

from src.config import load_yaml, project_root
from src.fundamentals.exposure import load_exposure_frame
from src.ranking.signals import classify_signal_from_percentile
from src.ranking.uncertainty import add_uncertainty_columns, classify_confidence_signal
from src.return_models.dataset import load_catalyst_modeling_frame
from src.return_models.expected_car import load_bundle, predict_expected_car


def rank_catalysts(
    as_of: date | None = None,
    model_path: Path | None = None,
    *,
    include_historical: bool = False,
) -> pd.DataFrame:
    cfg = load_yaml(project_root() / "configs" / "stock_picking.yaml")
    model_path = (
        model_path or project_root() / "data" / "processed" / "models" / "expected_car_v1.pkl"
    )

    effective_as_of = None if include_historical else (as_of or datetime.now(timezone.utc).date())
    df = load_catalyst_modeling_frame(labeled_only=False, as_of=effective_as_of)
    if df.empty:
        return pd.DataFrame()

    if model_path.exists():
        bundle = load_bundle(model_path)
        policy = getattr(bundle, "training_data_policy", "unverified")
        if policy != "strict_point_in_time_sanitized":
            raise ValueError(
                "Expected-CAR model lacks strict point-in-time training provenance; retrain it"
            )
        preds = predict_expected_car(df, bundle)
    else:
        raise FileNotFoundError(
            f"Expected-CAR model not found at {model_path}; refusing to rank with realized outcomes"
        )

    exposure = load_exposure_frame()
    exposure_cols = [
        "catalyst_id",
        "company_dependency",
        "is_lead_asset",
        "exposure_source",
        "exposure_as_of",
        "company_features_point_in_time",
    ]
    preds = preds.merge(
        exposure[[col for col in exposure_cols if col in exposure.columns]],
        on="catalyst_id",
        how="left",
    )
    preds["company_dependency"] = preds["company_dependency"].fillna(0.9)
    preds["expected_car_exposure_adj"] = preds["expected_car"] * preds["company_dependency"]
    structured_safe = preds.get(
        "structured_features_point_in_time",
        pd.Series(False, index=preds.index),
    ).fillna(False)
    company_safe = preds.get(
        "company_features_point_in_time",
        pd.Series(False, index=preds.index),
    ).fillna(False)
    preds["point_in_time_verified"] = structured_safe & company_safe
    preds["ranking_as_of"] = effective_as_of.isoformat() if effective_as_of else None
    preds["model_training_policy"] = bundle.training_data_policy
    preds = add_uncertainty_columns(preds)

    preds["expected_car_pct"] = preds["expected_car_exposure_adj"].rank(pct=True)
    preds["signal"] = preds["expected_car_pct"].apply(
        lambda p: classify_signal_from_percentile(p, cfg)
    )
    preds["confidence_signal"] = preds.apply(classify_confidence_signal, axis=1)

    out_cols = [
        "catalyst_id",
        "ticker",
        "drug_name",
        "indication",
        "catalyst_year",
        "ranking_as_of",
        "market_feature_as_of",
        "trial_source_observed_at",
        "exposure_as_of",
        "point_in_time_verified",
        "model_training_policy",
        "p_success",
        "e_car_given_success",
        "e_car_given_failure",
        "expected_car",
        "company_dependency",
        "expected_car_exposure_adj",
        "expected_car_exposure_adj_lo",
        "expected_car_exposure_adj_hi",
        "expected_car_ci_width",
        "signal",
        "confidence_signal",
    ]
    ranked = preds[[c for c in out_cols if c in preds.columns]].sort_values(
        "expected_car_exposure_adj", ascending=False
    )
    ranked.insert(0, "rank", range(1, len(ranked) + 1))
    return ranked


def export_rankings(df: pd.DataFrame, path: Path | None = None) -> Path:
    path = path or project_root() / "data" / "processed" / "catalyst_rankings.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return path


def format_decomposition(row: pd.Series) -> str:
    """Human-readable recommendation decomposition."""
    p = row.get("p_success", 0)
    es = row.get("e_car_given_success", 0)
    ef = row.get("e_car_given_failure", 0)
    exp = row.get("expected_car", 0)
    dep = row.get("company_dependency", 1)
    adj = row.get("expected_car_exposure_adj", exp)
    adj_lo = row.get("expected_car_exposure_adj_lo", adj)
    adj_hi = row.get("expected_car_exposure_adj_hi", adj)
    signal = row.get("signal", "NO TRADE")
    conf_signal = row.get("confidence_signal", "UNCERTAIN")
    lines = [
        f"**{row.get('drug_name')}** ({row.get('ticker')}) — {row.get('indication')}",
        "",
        "Scientific:",
        f"- P(success) = {p:.0%}",
        "",
        "Market reaction (conditional):",
        f"- E(CAR|success) = {es:+.1%}",
        f"- E(CAR|failure) = {ef:+.1%}",
        f"- Expected CAR = {p:.0%}×({es:+.1%}) + {1 - p:.0%}×({ef:+.1%}) = {exp:+.1%}",
        "",
        "Company:",
        f"- company_dependency = {dep:.0%}",
        f"- Exposure-adjusted expected CAR = {adj:+.1%}",
        f"- 90% conformal interval = [{adj_lo:+.1%}, {adj_hi:+.1%}]",
        "",
        f"**Signal: {signal}**",
        f"**Confidence signal: {conf_signal}**",
    ]
    return "\n".join(lines)
