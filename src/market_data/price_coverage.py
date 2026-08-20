"""Audit and batch-sync price history for catalyst tickers."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd
import yaml

from src.market_data.catalyst_prices import fetch_for_catalyst
from src.config import load_yaml, project_root


def _load_delist_map() -> dict:
    path = project_root() / "configs" / "ticker_delist_map.yaml"
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")).get("tickers", {})


def audit_price_coverage(db_path: Path | None = None) -> pd.DataFrame:
    """Check which catalyst tickers have fetchable price history."""
    cfg = load_yaml(project_root() / "configs" / "stock_picking.yaml")
    start = cfg["market_data"]["history_start"]
    delist = _load_delist_map()
    db_path = db_path or project_root() / "data" / "processed" / "research.db"
    conn = sqlite3.connect(db_path)

    rows = conn.execute(
        """
        SELECT c.catalyst_id, c.drug_name, ct.ticker_at_event, c.announcement_date,
               es.car IS NOT NULL AS has_event_study
        FROM catalysts c
        JOIN catalyst_ticker_history ct ON c.catalyst_id = ct.catalyst_id
        LEFT JOIN catalyst_event_study es ON c.catalyst_id = es.catalyst_id
            AND es.window_label = '[-1,+1]' AND es.benchmark = 'MARKET_MODEL'
        """
    ).fetchall()
    conn.close()

    results = []
    seen: dict[str, tuple[int, str | None]] = {}
    for catalyst_id, drug, ticker, ann, has_es in rows:
        t = ticker.upper()
        meta = delist.get(t, {})
        cache_key = f"{t}|{ann}"
        if cache_key in seen:
            n_bars, ticker_used = seen[cache_key]
        else:
            df, ticker_used = fetch_for_catalyst(t, ann, start=start)
            n_bars = len(df) if not df.empty else 0
            seen[cache_key] = (n_bars, ticker_used)

        results.append(
            {
                "catalyst_id": catalyst_id,
                "drug_name": drug,
                "ticker": t,
                "ticker_used": ticker_used,
                "announcement_date": ann,
                "n_bars": n_bars,
                "has_price_data": n_bars > 0,
                "has_event_study": bool(has_es),
                "known_delisted": bool(meta.get("delisted")),
                "successor_ticker": meta.get("successor_ticker"),
                "blocker": "delisted_needs_polygon" if meta.get("delisted") and n_bars == 0 else (
                    "no_price_data" if n_bars == 0 else None
                ),
            }
        )
    return pd.DataFrame(results)


def sync_catalyst_prices(force_refresh: bool = False) -> dict:
    """Prefetch price history for all unique catalyst tickers."""
    cfg = load_yaml(project_root() / "configs" / "stock_picking.yaml")
    start = cfg["market_data"]["history_start"]
    db_path = project_root() / "data" / "processed" / "research.db"
    conn = sqlite3.connect(db_path)
    tickers = [
        r[0]
        for r in conn.execute(
            "SELECT DISTINCT ticker_at_event FROM catalyst_ticker_history"
        ).fetchall()
    ]
    conn.close()

    stats = {"fetched": 0, "empty": 0, "bars_total": 0}
    for ticker in tickers:
        df = fetch_or_load(ticker, start=start, force_refresh=force_refresh)
        if df.empty:
            stats["empty"] += 1
        else:
            stats["fetched"] += 1
            stats["bars_total"] += len(df)
    return stats


def generate_price_coverage_report(db_path: Path | None = None) -> Path:
    df = audit_price_coverage(db_path)
    delisted_blocked = df[(df["known_delisted"]) & (~df["has_price_data"])]
    other_blocked = df[(~df["known_delisted"]) & (~df["has_price_data"])]
    priced_no_es = df[(df["has_price_data"]) & (~df["has_event_study"])]

    lines = [
        "# Price Coverage Audit",
        "",
        f"- Total catalysts: {len(df)}",
        f"- With price data: {int(df['has_price_data'].sum())}",
        f"- With event study: {int(df['has_event_study'].sum())}",
        f"- Priced but missing event study: {len(priced_no_es)}",
        f"- Delisted blocked (need Polygon/CRSP): {len(delisted_blocked)}",
        f"- Other missing price: {len(other_blocked)}",
        "",
        "## Delisted tickers without history",
        "",
    ]
    if not delisted_blocked.empty:
        lines.append(
            delisted_blocked[["ticker", "drug_name", "successor_ticker"]]
            .drop_duplicates("ticker")
            .to_string(index=False)
        )
    else:
        lines.append("None")

    out = project_root() / "reports" / "price_coverage.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")

    csv_path = project_root() / "data" / "processed" / "price_coverage_audit.csv"
    df.to_csv(csv_path, index=False)
    return out
