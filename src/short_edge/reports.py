"""Generate short-edge validation reports and verdict."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
from scipy import stats

from src.config import load_yaml, project_root
from src.short_edge.baselines import run_all_baselines
from src.short_edge.dependency import compute_enhanced_dependency, test_failure_car_vs_dependency
from src.short_edge.portfolio import simulate_short_portfolio
from src.short_edge.robustness import run_robustness_suite, slippage_stress_test
from src.short_edge.short_score import top_fraction_mask
from src.short_edge.stratification import run_stratification_report
from src.short_edge.tail_risk import evaluate_tail_classifier, precision_at_k


def _primary_strategy_mask(preds: pd.DataFrame) -> pd.Series:
    """Primary strategy: short each OOS year's top score quintile."""
    return top_fraction_mask(preds, "net_expected_short_return", 0.20)


def _event_study_asymmetry() -> dict:
    path = project_root() / "data" / "processed" / "catalyst_event_study.csv"
    if not path.exists():
        return {"n": 0, "failure_mean": None, "success_mean": None, "p_value": None}
    frame = pd.read_csv(path)
    mask = (frame["window_label"] == "[-1,+1]") & (frame["benchmark"] == "MARKET_MODEL")
    if "price_status" in frame.columns:
        mask &= frame["price_status"] == "ok"
    sub = frame.loc[mask].dropna(subset=["clinical_success", "car"])
    failures = sub.loc[sub["clinical_success"] == 0, "car"]
    successes = sub.loc[sub["clinical_success"] == 1, "car"]
    p_value = None
    if len(failures) >= 2 and len(successes) >= 2:
        p_value = float(stats.ttest_ind(failures, successes, equal_var=False).pvalue)
    return {
        "n": len(sub),
        "failure_mean": float(failures.mean()) if len(failures) else None,
        "success_mean": float(successes.mean()) if len(successes) else None,
        "p_value": p_value,
    }


def _evaluate_success_criteria(
    preds: pd.DataFrame,
    baselines: pd.DataFrame,
    robustness: dict,
    slippage_df: pd.DataFrame,
) -> dict:
    cfg = load_yaml(project_root() / "configs" / "short_edge.yaml")["success_criteria"]
    mask = _primary_strategy_mask(preds)
    trades = preds[mask]
    rets = trades["realized_short_return"].values if len(trades) else np.array([])

    model_row = baselines[baselines["baseline"] == "model_short_top_20pct"]
    short_all = baselines[baselines["baseline"] == "short_all_catalysts"]
    dep_base = baselines[baselines["baseline"] == "short_high_dependency"]

    loo = robustness.get("leave_one_out", pd.DataFrame())
    mean_without_best = (
        float(loo.loc[loo["dropped_return"].idxmax(), "mean_without"])
        if isinstance(loo, pd.DataFrame) and not loo.empty
        else None
    )

    slip_100 = slippage_df[slippage_df["slippage_bps"] == 100]
    era = robustness.get("era_splits", pd.DataFrame())
    multi_era_pos = bool(
        isinstance(era, pd.DataFrame)
        and len(era) >= 2
        and (era["mean_short_return"] > 0).sum() >= 2
    )

    boot = robustness.get("bootstrap", {})
    block_boot = robustness.get("block_bootstrap", {})
    ci = block_boot.get(
        "block_bootstrap_ci_95",
        boot.get("bootstrap_ci_95", (None, None)),
    )

    checks = {
        "min_oos_short_trades": len(trades) >= cfg["min_oos_short_trades"],
        "positive_mean": float(rets.mean()) > 0 if len(rets) else False,
        "ci_above_zero": ci[0] is not None and ci[0] > 0,
        "multi_era_positive": multi_era_pos,
        "beats_short_all": (
            float(model_row["mean_short_return"].iloc[0])
            > float(short_all["mean_short_return"].iloc[0])
            if len(model_row) and len(short_all)
            else False
        ),
        "beats_dependency_heuristic": (
            float(model_row["mean_short_return"].iloc[0])
            > float(dep_base["mean_short_return"].iloc[0])
            if len(model_row) and len(dep_base)
            else False
        ),
        "survives_100bps_slippage": (
            float(slip_100["mean_short_return"].iloc[0]) > 0 if len(slip_100) else False
        ),
        "survives_remove_largest_winner": mean_without_best is not None and mean_without_best > 0,
    }

    n_pass = sum(checks.values())
    n_total = len(checks)

    if (
        n_pass >= 7
        and checks["min_oos_short_trades"]
        and checks["positive_mean"]
        and checks["beats_dependency_heuristic"]
    ):
        verdict = "ROBUST OOS EDGE"
    elif (
        n_pass >= 5
        and checks["positive_mean"]
        and checks["beats_short_all"]
        and checks["beats_dependency_heuristic"]
    ):
        verdict = "PROMISING BUT UNVALIDATED EDGE"
    elif checks["positive_mean"] or (len(rets) and float(rets.mean()) > 0.005):
        verdict = "WEAK / INCONCLUSIVE EDGE"
    else:
        verdict = "NO EVIDENCE OF SHORT EDGE"

    return {
        "checks": checks,
        "n_pass": n_pass,
        "n_total": n_total,
        "verdict": verdict,
        "primary_strategy_n": len(trades),
        "primary_strategy_mean": float(rets.mean()) if len(rets) else None,
    }


def generate_short_edge_reports(
    preds: pd.DataFrame,
    baselines: pd.DataFrame | None = None,
) -> dict:
    root = project_root()
    cfg = load_yaml(root / "configs" / "short_edge.yaml")

    if baselines is None:
        baselines = run_all_baselines(preds, cfg["costs"]["default_slippage_bps"])

    mask = _primary_strategy_mask(preds)
    robustness = run_robustness_suite(preds, mask)
    slippage_df = slippage_stress_test(preds[mask], cfg["costs"]["slippage_stress_bps"])
    strat_df = run_stratification_report(preds)
    dep_df = compute_enhanced_dependency(preds)
    dep_test = test_failure_car_vs_dependency(dep_df)

    # Tail risk OOS eval
    tail_eval = evaluate_tail_classifier(
        preds["major_negative_event"].values,
        preds["p_major_drop"].values,
    )
    tail_eval["precision_at_5"] = precision_at_k(
        preds["major_negative_event"].values, preds["p_major_drop"].values, 5
    )
    tail_eval["precision_at_10"] = precision_at_k(
        preds["major_negative_event"].values, preds["p_major_drop"].values, 10
    )

    portfolio = simulate_short_portfolio(preds[mask])
    criteria = _evaluate_success_criteria(preds, baselines, robustness, slippage_df)
    event_asymmetry = _event_study_asymmetry()

    # Export trades
    trades_path = root / "data" / "oos_short_trades.csv"
    preds[mask].to_csv(trades_path, index=False)

    # --- short_baselines.md ---
    base_lines = [
        "# Short Strategy Baselines",
        "",
        f"OOS predictions: **{len(preds)}** catalysts",
        f"Primary model strategy: short each OOS year's top 20% by net expected short return (**{mask.sum()}** trades)",
        "",
        "## All baselines vs model strategies",
        "",
        baselines.to_string(index=False),
        "",
        "## Interpretation",
        "",
        "Model must beat `short_all_catalysts` and `short_high_dependency` to claim incremental value.",
    ]
    (root / "reports" / "short_baselines.md").write_text("\n".join(base_lines), encoding="utf-8")

    # --- tail_risk_model.md ---
    tail_lines = [
        "# Tail Risk Model Report",
        "",
        f"Target: CAR <= {cfg['tail_risk']['major_drop_car']:.0%}",
        "",
        "## OOS classifier metrics",
        "",
    ]
    for k, v in tail_eval.items():
        tail_lines.append(f"- {k}: {v}")
    tail_lines.extend(
        [
            "",
            "## Ranking comparison",
            "",
            f"- Mean tail_risk_score (major events): {preds.loc[preds['major_negative_event'] == 1, 'tail_risk_score'].mean():.4f}",
            f"- Mean tail_risk_score (non-events): {preds.loc[preds['major_negative_event'] == 0, 'tail_risk_score'].mean():.4f}",
        ]
    )
    (root / "reports" / "tail_risk_model.md").write_text("\n".join(tail_lines), encoding="utf-8")

    # --- robustness_tests.md ---
    boot = robustness.get("bootstrap", {})
    block_boot = robustness.get("block_bootstrap", {})
    loo = robustness.get("leave_one_out", pd.DataFrame())
    win = robustness.get("winsorized_means", {})
    rob_lines = [
        "# Robustness Tests (Short Top 20% Strategy)",
        "",
        f"N trades: **{mask.sum()}**",
        "",
        "## Bootstrap",
        "",
    ]
    for k, v in boot.items():
        rob_lines.append(f"- {k}: {v}")
    rob_lines.extend(["", "## Year-block bootstrap", ""])
    for k, v in block_boot.items():
        rob_lines.append(f"- {k}: {v}")
    rob_lines.extend(["", "## Winsorized / trimmed means", ""])
    for k, v in win.items():
        rob_lines.append(f"- {k}: {v:.4f}")
    rob_lines.append(f"- trimmed_mean_10pct: {robustness.get('trimmed_mean_10pct', 'N/A')}")
    if isinstance(loo, pd.DataFrame) and not loo.empty:
        worst = loo.loc[loo["dropped_return"].idxmax()]
        rob_lines.extend(
            [
                "",
                "## Leave-one-out (largest winner removed)",
                "",
                f"- Largest winner return: {worst['dropped_return']:.4f}",
                f"- Mean without: {worst['mean_without']:.4f}",
                f"- Delta: {worst['delta_mean']:.4f}",
                "",
                "### Full LOO table",
                "",
                loo.to_string(index=False),
            ]
        )
    rob_lines.extend(["", "## Slippage stress", "", slippage_df.to_string(index=False)])
    era = robustness.get("era_splits", pd.DataFrame())
    if isinstance(era, pd.DataFrame) and not era.empty:
        rob_lines.extend(["", "## Era splits", "", era.to_string(index=False)])
    (root / "reports" / "robustness_tests.md").write_text("\n".join(rob_lines), encoding="utf-8")

    model_row = baselines[baselines["baseline"] == "model_short_top_20pct"]
    dep_row = baselines[baselines["baseline"] == "short_high_dependency"]
    model_mean = float(model_row["mean_short_return"].iloc[0]) if len(model_row) else None
    model_n = int(model_row["n_trades"].iloc[0]) if len(model_row) else 0
    dep_mean = float(dep_row["mean_short_return"].iloc[0]) if len(dep_row) else None
    dep_n = int(dep_row["n_trades"].iloc[0]) if len(dep_row) else 0
    beats_dep = model_mean is not None and dep_mean is not None and model_mean > dep_mean
    comparison = "beats" if beats_dep else "does not beat"
    model_result = (
        f"The year-local model top-20% strategy ({model_mean:+.1%} mean, n={model_n}) "
        f"**{comparison}**"
        if model_mean is not None
        else "The model strategy was unavailable."
    )
    dependency_result = (
        f"shorting high-dependency small-cap biotech ({dep_mean:+.1%} mean, n={dep_n})."
        if dep_mean is not None
        else "The dependency baseline was unavailable."
    )
    incremental_result = (
        "The point-in-time-safe model demonstrates incremental development-sample value over "
        "this heuristic, pending a genuinely new prospective holdout."
        if beats_dep
        else "Model scoring adds no demonstrated incremental OOS value in this sample."
    )
    final_holdout_start = cfg["holdout"]["final_locked_start"]
    market_safe = int(preds.get("market_features_point_in_time", pd.Series(False)).sum())
    company_safe = int(preds.get("company_features_point_in_time", pd.Series(False)).sum())
    clinical_safe = int(preds.get("clinical_features_point_in_time", pd.Series(False)).sum())

    # --- SHORT_EDGE_VALIDATION.md ---
    val_lines = [
        "# Short Edge Validation Report",
        "",
        f"**Verdict: {criteria['verdict']}**",
        "",
        (
            f"Generated from {len(preds)} development walk-forward OOS predictions; "
            f"the legacy holdout beginning {final_holdout_start} is quarantined and excluded."
        ),
        "",
        "## Core hypothesis",
        "",
        "> High P(failure) × high company exposure → asymmetric downside before binary catalysts",
        "",
        "## Point-in-time provenance",
        "",
        f"- Market feature rows verified at cutoff: {market_safe}/{len(preds)}",
        f"- Company feature rows verified at cutoff: {company_safe}/{len(preds)}",
        f"- Historical trial snapshots verified at cutoff: {clinical_safe}/{len(preds)}",
        (
            "- Unversioned ClinicalTrials.gov fields are excluded from strict model features; "
            "phase-stratified baselines are therefore unavailable."
        ),
        "",
        "## Predefined success criteria",
        "",
    ]
    for k, v in criteria["checks"].items():
        val_lines.append(f"- {k}: {'PASS' if v else 'FAIL'}")
    val_lines.append(f"\n**Score: {criteria['n_pass']}/{criteria['n_total']} criteria met**")
    val_lines.extend(
        [
            "",
            "## Key OOS metrics (primary strategy: each test year's top 20%)",
            "",
            f"- N short trades: {criteria['primary_strategy_n']}",
            f"- Mean net short return: {criteria['primary_strategy_mean']:.4f}"
            if criteria["primary_strategy_mean"] is not None
            else "- Mean: N/A",
            f"- Bootstrap 95% CI: {boot.get('bootstrap_ci_95')}",
            f"- Year-block bootstrap 95% CI: {block_boot.get('block_bootstrap_ci_95')}",
            f"- P(mean > 0): {boot.get('p_mean_positive')}",
            f"- Permutation p-value: {boot.get('permutation_p_value')}",
            "",
            f"## Event study asymmetry (descriptive, N={event_asymmetry['n']})",
            "",
            f"- Failure mean CAR: {event_asymmetry['failure_mean']}",
            f"- Success mean CAR: {event_asymmetry['success_mean']}",
            f"- Welch difference p-value: {event_asymmetry['p_value']}",
            "",
            "## Model vs baselines",
            "",
            baselines.to_string(index=False),
            "",
            "## Company dependency analysis",
            "",
            f"- Failure CAR vs enhanced dependency: {dep_test}",
            "",
            "## Portfolio simulation (2% max per catalyst, 20% max short exposure)",
            "",
        ]
    )
    for k, v in portfolio.items():
        if k != "nav_history":
            val_lines.append(f"- {k}: {v}")
    val_lines.extend(
        [
            "",
            "## Stratification diagnostics",
            "",
            strat_df.to_string(index=False)
            if not strat_df.empty
            else "_Insufficient data per bucket_",
            "",
            "## Critical finding: model vs naive heuristics",
            "",
            model_result,
            dependency_result,
            incremental_result,
            "",
            "## Sample size requirements before live stock selection",
            "",
            (
                f"- Current development OOS short candidates: **{mask.sum()}** "
                f"(year-local top 20% of {len(preds)} OOS rows) — far below target of **≥100**"
            ),
            "- Need **≥100 OOS short trades** (preferably ≥200) before strong claims",
            "- Expand catalyst universe independently of outcome (oncology Ph2/3, neurology, immunology, rare disease)",
            "- Complete 5 missing CAR observations via Polygon/EODHD/CRSP",
            (
                "- The legacy 2022+ holdout appeared in earlier artifacts; keep it quarantined "
                "and establish a new prospective holdout for final claims"
            ),
            "",
            "## What was NOT done (by design)",
            "",
            "- No threshold tuning on test-year outcomes",
            "- No LONG signals produced",
            "- No live stock picker until validation passes",
            "- No retroactive optimization of baseline expected-CAR model",
        ]
    )
    (root / "reports" / "SHORT_EDGE_VALIDATION.md").write_text(
        "\n".join(val_lines), encoding="utf-8"
    )

    # Save criteria JSON
    (root / "data" / "processed" / "short_edge_verdict.json").write_text(
        json.dumps(criteria, indent=2, default=str), encoding="utf-8"
    )

    return {
        "verdict": criteria["verdict"],
        "criteria": criteria,
        "baselines": baselines,
        "robustness": robustness,
        "portfolio": {k: v for k, v in portfolio.items() if k != "nav_history"},
    }
