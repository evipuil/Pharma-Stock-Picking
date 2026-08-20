"""Point-in-time fundamentals from SEC EDGAR company facts."""

from __future__ import annotations

import sqlite3
import uuid
from datetime import date
from pathlib import Path

import pandas as pd

from src.config import project_root
from src.fundamentals.edgar_client import fetch_company_facts, load_ticker_cik_map, lookup_cik

# US-GAAP tags to extract (first available wins)
FACT_TAGS = {
    "cash_usd": [
        "CashAndCashEquivalentsAtCarryingValue",
        "CashCashEquivalentsAndShortTermInvestments",
    ],
    "debt_usd": [
        "LongTermDebtNoncurrent",
        "LongTermDebt",
        "DebtInstrumentCarryingAmount",
    ],
    "shares_outstanding": [
        "CommonStockSharesOutstanding",
        "EntityCommonStockSharesOutstanding",
    ],
    "revenue_usd": [
        "Revenues",
        "RevenueFromContractWithCustomerExcludingAssessedTax",
    ],
}


def _pick_fact_as_of(fact_obj: dict, cutoff: date) -> dict | None:
    """Most recent filed observation with end date on/before cutoff."""
    units = fact_obj.get("units", {})
    usd_entries = units.get("USD") or units.get("shares") or units.get("pure") or []
    if not usd_entries and units:
        usd_entries = next(iter(units.values()), [])

    best = None
    for entry in usd_entries:
        end = entry.get("end")
        filed = entry.get("filed")
        if not end or not filed:
            continue
        end_d = date.fromisoformat(str(end)[:10])
        filed_d = date.fromisoformat(str(filed)[:10])
        if end_d > cutoff or filed_d > cutoff:
            continue
        if best is None or filed_d > date.fromisoformat(str(best["filed"])[:10]):
            best = entry
    return best


def extract_point_in_time(facts: dict, cutoff: date) -> dict:
    """Extract fundamentals as of trading cutoff from companyfacts payload."""
    gaap = facts.get("facts", {}).get("us-gaap", {})
    out: dict = {}
    for field, tags in FACT_TAGS.items():
        val = None
        src_tag = None
        filing_date = None
        period_end = None
        for tag in tags:
            if tag not in gaap:
                continue
            picked = _pick_fact_as_of(gaap[tag], cutoff)
            if picked:
                val = picked.get("val")
                src_tag = tag
                filing_date = picked.get("filed")
                period_end = picked.get("end")
                break
        out[field] = val
        if field == "cash_usd":
            out["cash_source_tag"] = src_tag
            out["filing_date"] = filing_date
            out["period_end"] = period_end
    return out


def _dependency_from_market_cap(market_cap_usd: float | None) -> float | None:
    if market_cap_usd is None or market_cap_usd <= 0:
        return None
    if market_cap_usd >= 50e9:
        return 0.15
    if market_cap_usd >= 5e9:
        return 0.45
    return 0.85


def compute_fundamentals_for_catalysts(db_path: Path | None = None) -> dict:
    db_path = db_path or project_root() / "data" / "processed" / "research.db"
    conn = sqlite3.connect(db_path)
    ticker_map = load_ticker_cik_map()

    rows = conn.execute(
        """
        SELECT c.catalyst_id, ct.ticker_at_event,
               COALESCE(tc.entry_cutoff_date, c.trading_cutoff_date, c.announcement_date) AS cutoff,
               mf.price_at_cutoff
        FROM catalysts c
        JOIN catalyst_ticker_history ct ON c.catalyst_id = ct.catalyst_id
        LEFT JOIN catalyst_trading_cutoffs tc ON c.catalyst_id = tc.catalyst_id
        LEFT JOIN catalyst_market_features mf ON c.catalyst_id = mf.catalyst_id
        """
    ).fetchall()

    stats = {"computed": 0, "skipped_no_cik": 0, "skipped_no_facts": 0}
    facts_cache: dict[int, dict] = {}

    for catalyst_id, ticker, cutoff, price in rows:
        if not cutoff:
            continue
        cutoff_d = date.fromisoformat(str(cutoff)[:10])
        cik = lookup_cik(ticker, ticker_map)
        if not cik:
            stats["skipped_no_cik"] += 1
            continue

        if cik not in facts_cache:
            try:
                facts_cache[cik] = fetch_company_facts(cik)
            except Exception:
                stats["skipped_no_facts"] += 1
                continue

        pit = extract_point_in_time(facts_cache[cik], cutoff_d)
        if not any(pit.get(k) for k in FACT_TAGS):
            stats["skipped_no_facts"] += 1
            continue

        shares = pit.get("shares_outstanding")
        market_cap = None
        if shares and price:
            market_cap = float(shares) * float(price)

        fund_id = str(uuid.uuid4())
        conn.execute(
            """
            INSERT INTO point_in_time_fundamentals (
                fund_id, catalyst_id, filing_type, filing_date, period_end,
                cash_usd, debt_usd, shares_outstanding, market_cap_usd,
                revenue_usd, source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(catalyst_id, filing_date, filing_type) DO UPDATE SET
                cash_usd = excluded.cash_usd,
                debt_usd = excluded.debt_usd,
                shares_outstanding = excluded.shares_outstanding,
                market_cap_usd = excluded.market_cap_usd,
                revenue_usd = excluded.revenue_usd
            """,
            (
                fund_id,
                catalyst_id,
                "10-Q/10-K",
                pit.get("filing_date"),
                pit.get("period_end"),
                pit.get("cash_usd"),
                pit.get("debt_usd"),
                shares,
                market_cap,
                pit.get("revenue_usd"),
                "sec_edgar_companyfacts",
            ),
        )

        dependency = _dependency_from_market_cap(market_cap)
        if dependency is not None:
            conn.execute(
                """
                INSERT INTO asset_exposure (
                    catalyst_id, market_cap_usd, cash_usd, debt_usd,
                    revenue_ttm_usd, company_dependency, as_of_date, data_source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(catalyst_id) DO UPDATE SET
                    market_cap_usd = COALESCE(excluded.market_cap_usd, asset_exposure.market_cap_usd),
                    cash_usd = excluded.cash_usd,
                    debt_usd = excluded.debt_usd,
                    revenue_ttm_usd = excluded.revenue_ttm_usd,
                    company_dependency = excluded.company_dependency,
                    as_of_date = excluded.as_of_date,
                    data_source = excluded.data_source
                """,
                (
                    catalyst_id,
                    market_cap,
                    pit.get("cash_usd"),
                    pit.get("debt_usd"),
                    pit.get("revenue_usd"),
                    dependency,
                    str(cutoff)[:10],
                    "sec_edgar",
                ),
            )
        stats["computed"] += 1

    conn.commit()
    conn.close()
    return stats


def export_fundamentals_csv(db_path: Path | None = None) -> Path:
    db_path = db_path or project_root() / "data" / "processed" / "research.db"
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM point_in_time_fundamentals", conn)
    conn.close()
    path = project_root() / "data" / "processed" / "point_in_time_fundamentals.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return path
