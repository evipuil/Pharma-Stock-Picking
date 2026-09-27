"""Point-in-time provenance checks for catalyst model features."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from src.config import project_root


def point_in_time_mask(
    frame: pd.DataFrame,
    observed_col: str,
    cutoff_col: str = "feature_cutoff_date",
) -> pd.Series:
    """Return rows whose source observation existed by the trading cutoff."""
    observed = pd.to_datetime(frame[observed_col], errors="coerce")
    cutoff = pd.to_datetime(frame[cutoff_col], errors="coerce")
    return observed.notna() & cutoff.notna() & observed.le(cutoff)


def sanitize_feature_family(
    frame: pd.DataFrame,
    feature_cols: list[str],
    observed_col: str,
    *,
    flag_col: str,
    cutoff_col: str = "feature_cutoff_date",
) -> pd.DataFrame:
    """Null a feature family when its source cannot be verified at cutoff."""
    out = frame.copy()
    safe = point_in_time_mask(out, observed_col, cutoff_col)
    out[flag_col] = safe
    present = [col for col in feature_cols if col in out.columns]
    if present:
        out.loc[~safe, present] = pd.NA
    return out


def run_point_in_time_audit(db_path: Path | None = None) -> pd.DataFrame:
    """Return catalyst-level feature provenance failures and unverified snapshots."""
    db_path = db_path or project_root() / "data" / "processed" / "research.db"
    conn = sqlite3.connect(db_path)
    checks = [
        (
            "market_feature_after_cutoff",
            "FAIL",
            """
            SELECT c.catalyst_id, mf.as_of_date, cutoff.cutoff_date
            FROM catalyst_market_features mf
            JOIN catalysts c USING (catalyst_id)
            JOIN (
                SELECT c2.catalyst_id,
                       COALESCE(tc.entry_cutoff_date, c2.trading_cutoff_date,
                                c2.announcement_date) AS cutoff_date
                FROM catalysts c2
                LEFT JOIN catalyst_trading_cutoffs tc USING (catalyst_id)
            ) cutoff USING (catalyst_id)
            WHERE date(mf.as_of_date) > date(cutoff.cutoff_date)
            """,
        ),
        (
            "exposure_after_cutoff",
            "FAIL",
            """
            SELECT c.catalyst_id, ae.as_of_date, cutoff.cutoff_date
            FROM asset_exposure ae
            JOIN catalysts c USING (catalyst_id)
            JOIN (
                SELECT c2.catalyst_id,
                       COALESCE(tc.entry_cutoff_date, c2.trading_cutoff_date,
                                c2.announcement_date) AS cutoff_date
                FROM catalysts c2
                LEFT JOIN catalyst_trading_cutoffs tc USING (catalyst_id)
            ) cutoff USING (catalyst_id)
            WHERE date(ae.as_of_date) > date(cutoff.cutoff_date)
            """,
        ),
        (
            "fundamental_filed_after_cutoff",
            "FAIL",
            """
            SELECT c.catalyst_id, pf.filing_date, cutoff.cutoff_date
            FROM point_in_time_fundamentals pf
            JOIN catalysts c USING (catalyst_id)
            JOIN (
                SELECT c2.catalyst_id,
                       COALESCE(tc.entry_cutoff_date, c2.trading_cutoff_date,
                                c2.announcement_date) AS cutoff_date
                FROM catalysts c2
                LEFT JOIN catalyst_trading_cutoffs tc USING (catalyst_id)
            ) cutoff USING (catalyst_id)
            WHERE date(pf.filing_date) > date(cutoff.cutoff_date)
            """,
        ),
        (
            "trial_snapshot_observed_after_cutoff",
            "UNVERIFIED",
            """
            SELECT c.catalyst_id, ct.api_fetched_at, cutoff.cutoff_date
            FROM catalysts c
            JOIN clinical_trials ct ON c.nct_id = ct.nct_id
            JOIN (
                SELECT c2.catalyst_id,
                       COALESCE(tc.entry_cutoff_date, c2.trading_cutoff_date,
                                c2.announcement_date) AS cutoff_date
                FROM catalysts c2
                LEFT JOIN catalyst_trading_cutoffs tc USING (catalyst_id)
            ) cutoff USING (catalyst_id)
            WHERE date(ct.api_fetched_at) > date(cutoff.cutoff_date)
            """,
        ),
        (
            "trial_first_posted_after_cutoff",
            "FAIL",
            """
            SELECT c.catalyst_id, ct.first_posted_date, cutoff.cutoff_date
            FROM catalysts c
            JOIN clinical_trials ct ON c.nct_id = ct.nct_id
            JOIN (
                SELECT c2.catalyst_id,
                       COALESCE(tc.entry_cutoff_date, c2.trading_cutoff_date,
                                c2.announcement_date) AS cutoff_date
                FROM catalysts c2
                LEFT JOIN catalyst_trading_cutoffs tc USING (catalyst_id)
            ) cutoff USING (catalyst_id)
            WHERE date(ct.first_posted_date) > date(cutoff.cutoff_date)
            """,
        ),
    ]
    rows: list[dict] = []
    try:
        for check, severity, query in checks:
            for catalyst_id, observed_at, cutoff in conn.execute(query).fetchall():
                rows.append(
                    {
                        "catalyst_id": catalyst_id,
                        "check": check,
                        "severity": severity,
                        "observed_at": observed_at,
                        "cutoff_date": cutoff,
                    }
                )
    finally:
        conn.close()
    return pd.DataFrame(
        rows,
        columns=["catalyst_id", "check", "severity", "observed_at", "cutoff_date"],
    )


def summarize_point_in_time_audit(audit: pd.DataFrame) -> dict:
    if audit.empty:
        return {"violations": 0, "unverified": 0, "affected_catalysts": 0}
    return {
        "violations": int((audit["severity"] == "FAIL").sum()),
        "unverified": int((audit["severity"] == "UNVERIFIED").sum()),
        "affected_catalysts": int(audit["catalyst_id"].nunique()),
        "by_check": audit.groupby("check").size().astype(int).to_dict(),
    }


def generate_point_in_time_report(
    audit: pd.DataFrame | None = None,
    path: Path | None = None,
) -> Path:
    audit = run_point_in_time_audit() if audit is None else audit
    summary = summarize_point_in_time_audit(audit)
    lines = [
        "# Point-in-Time Feature Audit",
        "",
        "Feature families with unverifiable source timing are excluded from strict model frames.",
        "A current ClinicalTrials.gov record is not treated as a historical snapshot.",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: {value}")
    if not audit.empty:
        lines.extend(["", "## Findings", "", audit.to_string(index=False)])
    path = path or project_root() / "reports" / "point_in_time_audit.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
