"""Generate catalyst dataset coverage report."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from src.config import load_yaml, project_root


def generate_coverage_report(db_path: Path | None = None) -> Path:
    db_path = db_path or project_root() / "data" / "processed" / "research.db"
    cfg = load_yaml(project_root() / "configs" / "stock_picking.yaml")
    conn = sqlite3.connect(db_path)

    n_cat = conn.execute("SELECT COUNT(*) FROM catalysts").fetchone()[0]
    n_prog = conn.execute("SELECT COUNT(*) FROM programs").fetchone()[0]
    n_with_ann = conn.execute(
        "SELECT COUNT(*) FROM catalysts WHERE announcement_date IS NOT NULL"
    ).fetchone()[0]
    n_with_es = conn.execute(
        "SELECT COUNT(DISTINCT catalyst_id) FROM catalyst_event_study WHERE car IS NOT NULL"
    ).fetchone()[0]
    try:
        n_market_feats = conn.execute(
            "SELECT COUNT(*) FROM catalyst_market_features"
        ).fetchone()[0]
    except Exception:
        n_market_feats = 0
    try:
        n_trial_feats = conn.execute(
            "SELECT COUNT(*) FROM catalyst_trial_features"
        ).fetchone()[0]
    except Exception:
        n_trial_feats = 0
    n_preclin = conn.execute(
        "SELECT COUNT(*) FROM catalysts WHERE preclinical_evidence_found = 1"
    ).fetchone()[0]
    n_no_preclin = conn.execute(
        "SELECT COUNT(*) FROM catalysts WHERE preclinical_evidence_found = 0 OR preclinical_evidence_found IS NULL"
    ).fetchone()[0]

    outcomes = pd.read_sql_query(
        """
        SELECT outcome_category, COUNT(*) AS n
        FROM catalysts GROUP BY outcome_category
        """,
        conn,
    )

    price_status = pd.read_sql_query(
        """
        SELECT c.catalyst_id, c.drug_name, ct.ticker_at_event, c.announcement_date,
               c.clinical_success, c.outcome_category
        FROM catalysts c
        LEFT JOIN catalyst_ticker_history ct ON c.catalyst_id = ct.catalyst_id
        LEFT JOIN (
            SELECT catalyst_id, MAX(car) AS car_m1p1
            FROM catalyst_event_study
            WHERE window_label = '[-1,+1]' AND benchmark = 'MARKET_MODEL'
            GROUP BY catalyst_id
        ) es ON c.catalyst_id = es.catalyst_id
        ORDER BY c.announcement_date
        """,
        conn,
    )

    es_raw = pd.read_sql_query(
        """
        SELECT c.clinical_success, es.car
        FROM catalyst_event_study es
        JOIN catalysts c ON es.catalyst_id = c.catalyst_id
        WHERE es.window_label = '[-1,+1]' AND es.benchmark = 'MARKET_MODEL'
        """,
        conn,
    )
    if not es_raw.empty:
        es_summary = (
            es_raw.groupby("clinical_success")["car"]
            .agg(n="count", mean_car="mean", median_car="median", std="std")
            .reset_index()
        )
    else:
        es_summary = pd.DataFrame()

    conn.close()

    target = cfg["cohort"]["phase_a_target"]
    def _df_md(df: pd.DataFrame) -> str:
        if df.empty:
            return "_No data_"
        return df.to_string(index=False)

    lines = [
        "# Catalyst Dataset Coverage Report",
        "",
        f"**Generated from:** `{db_path}`",
        "",
        "## Cohort size",
        "",
        f"| Metric | Count | Target |",
        f"|--------|------:|-------:|",
        f"| Catalysts | {n_cat} | ≥{target} (Phase A) |",
        f"| Underlying programs | {n_prog} | — |",
        f"| With announcement date | {n_with_ann} | — |",
        f"| With event study CAR | {n_with_es} | — |",
        f"| With market features | {n_market_feats} | — |",
        f"| With trial design features | {n_trial_feats} | — |",
        f"| Preclinical evidence found | {n_preclin} | — |",
        f"| No preclinical evidence | {n_no_preclin} | — |",
        "",
        "## Outcome mix",
        "",
        _df_md(outcomes),
        "",
        "## Event study: CAR [-1,+1] market model by outcome",
        "",
        _df_md(es_summary),
        "",
        "## Known blockers",
        "",
        "### Price data",
        "- **yfinance**: Active tickers only; many delisted biotech symbols return empty history",
        "- **Delisted examples**: IMMU, AVEO, CLVS, LOXO, CELG, SNTA, CYTR — require Polygon or CRSP",
        "- **Adapter stubs**: `PolygonAdapter` (needs `POLYGON_API_KEY`), `CRSPAdapter` (needs WRDS)",
        "",
        "### Announcement timing",
        "- Most catalysts use `announcement_timing=UNKNOWN` until SEC/press release parsing is built",
        "- Executable backtest uses conservative prior-close cutoff when timing unknown",
        "",
        "### Fundamentals",
        "- `point_in_time_fundamentals` schema ready; SEC EDGAR ingestion not yet implemented",
        "",
        "## Next stages",
        "",
        "1. Stage 5: Point-in-time market + fundamentals features",
        "2. Stage 6–7: Indication-level P(success) and E(CAR|success/failure) models",
        "3. Stage 9: Walk-forward backtester with OOS ledger",
        "",
    ]

    out = project_root() / "reports" / "catalyst_coverage.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")

    es_out = project_root() / "reports" / "event_study.md"
    es_lines = [
        "# Event Study Report",
        "",
        "## Methodology",
        "- Estimation window: [-250, -30] trading days",
        "- Windows: [-5,+5], [-1,+1], [0,+1], [0,+5], [0,+20]",
        "- Benchmarks: RAW, SPY, XBI, MARKET_MODEL, XBI_MODEL",
        "",
        "## Success vs failure CAR (market model, [-1,+1])",
        "",
        _df_md(es_summary),
        "",
        "## Price coverage by catalyst",
        "",
        f"Total catalysts with prices: **{n_with_es}** / **{n_cat}**",
        "",
    ]
    es_out.write_text("\n".join(es_lines), encoding="utf-8")
    return out
