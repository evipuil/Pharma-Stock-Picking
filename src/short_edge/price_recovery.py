"""Export missing price requirements for delisted catalysts."""

from __future__ import annotations

import sqlite3
from datetime import timedelta
from pathlib import Path

import pandas as pd

from src.config import project_root


def export_missing_price_requirements(db_path: Path | None = None) -> Path:
    db_path = db_path or project_root() / "data" / "processed" / "research.db"
    conn = sqlite3.connect(db_path)
    missing = pd.read_sql(
        """
        SELECT c.catalyst_id, c.drug_name, c.announcement_date, ct.ticker_at_event,
               c.clinical_success, c.outcome_category
        FROM catalysts c
        JOIN catalyst_ticker_history ct ON c.catalyst_id = ct.catalyst_id
        LEFT JOIN catalyst_event_study es ON c.catalyst_id = es.catalyst_id
            AND es.window_label = '[-1,+1]' AND es.benchmark = 'MARKET_MODEL'
        WHERE es.car IS NULL
        """,
        conn,
    )
    conn.close()

    rows = []
    for _, r in missing.iterrows():
        ann = pd.to_datetime(r["announcement_date"])
        rows.append({
            "catalyst_id": r["catalyst_id"],
            "ticker": r["ticker_at_event"],
            "drug_name": r["drug_name"],
            "announcement_date": str(ann.date()) if pd.notna(ann) else None,
            "price_start_required": str((ann - timedelta(days=400)).date()) if pd.notna(ann) else None,
            "price_end_required": str((ann + timedelta(days=30)).date()) if pd.notna(ann) else None,
            "source_needed": "Polygon/EODHD/CRSP/local_csv",
            "notes": "Delisted or truncated history post-2017",
        })

    out = project_root() / "data" / "processed" / "missing_price_requirements.csv"
    pd.DataFrame(rows).to_csv(out, index=False)
    return out


def try_extend_prices_via_stooq(tickers: list[str] | None = None) -> dict:
    """Fetch post-2017 bars from Stooq and merge into local CSV files."""
    from src.market_data.adapters.stooq_adapter import StooqAdapter

    adapter = StooqAdapter()
    if not adapter.api_key:
        return {"status": "skipped", "reason": "STOOQ_API_KEY not set"}

    req_path = export_missing_price_requirements()
    req = pd.read_csv(req_path)
    if tickers:
        req = req[req["ticker"].isin(tickers)]

    out_dir = project_root() / "data" / "external" / "prices"
    stats = {"attempted": 0, "extended": 0, "errors": []}

    for ticker in sorted(req["ticker"].dropna().unique()):
        sub = req[req["ticker"] == ticker]
        start = sub["price_start_required"].min()
        end = sub["price_end_required"].max()
        stats["attempted"] += 1
        try:
            df = adapter.fetch_daily(ticker, start=start, end=end)
            if df.empty:
                stats["errors"].append(f"{ticker}: empty Stooq response")
                continue
            csv_path = out_dir / f"{ticker.upper()}.csv"
            if csv_path.exists():
                existing = pd.read_csv(csv_path, parse_dates=["date"])
                df = (
                    pd.concat([existing, df], ignore_index=True)
                    .drop_duplicates("date")
                    .sort_values("date")
                )
            df.to_csv(csv_path, index=False)
            stats["extended"] += 1
        except Exception as exc:
            stats["errors"].append(f"{ticker}: {exc}")

    return stats


def try_recover_missing_cars() -> dict:
    """Attempt event study on missing catalysts using available adapters."""
    from src.event_study.catalyst_study import run_catalyst_event_study

    db_path = project_root() / "data" / "processed" / "research.db"
    req_path = export_missing_price_requirements()
    req = pd.read_csv(req_path)
    if req.empty:
        return {"attempted": 0, "recovered": 0}

    before = _count_cars(db_path)
    stooq_stats = try_extend_prices_via_stooq()
    run_catalyst_event_study()
    after = _count_cars(db_path)
    return {
        "attempted": len(req),
        "recovered": after - before,
        "still_missing": len(req) - (after - before),
        "requirements_csv": str(req_path),
        "stooq": stooq_stats,
    }


def _count_cars(db_path: Path) -> int:
    conn = sqlite3.connect(db_path)
    n = conn.execute(
        "SELECT COUNT(*) FROM catalyst_event_study WHERE window_label='[-1,+1]' AND benchmark='MARKET_MODEL' AND car IS NOT NULL"
    ).fetchone()[0]
    conn.close()
    return n
