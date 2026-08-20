"""Company / asset exposure scoring for catalyst impact scaling."""

from __future__ import annotations

import sqlite3
import uuid
from pathlib import Path

import pandas as pd
import yaml

from src.config import project_root


def _load_exposure_config() -> dict:
    path = project_root() / "configs" / "exposure.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def classify_ticker(ticker: str, cfg: dict | None = None) -> tuple[str, float]:
    cfg = cfg or _load_exposure_config()
    t = (ticker or "").upper()
    scores = cfg["dependency_scores"]
    if t in cfg.get("large_pharma_tickers", []):
        return "large_pharma", scores["large_pharma"]
    if t in cfg.get("mid_cap_tickers", []):
        return "mid_cap", scores["mid_cap"]
    return "small_cap", scores["small_cap"]


def compute_exposure_for_catalysts(db_path: Path | None = None) -> dict:
    db_path = db_path or project_root() / "data" / "processed" / "research.db"
    cfg = _load_exposure_config()
    conn = sqlite3.connect(db_path)

    rows = conn.execute(
        """
        SELECT c.catalyst_id, ct.ticker_at_event, mf.price_at_cutoff,
               COALESCE(mf.as_of_date, tc.entry_cutoff_date, c.trading_cutoff_date,
                        c.announcement_date) AS as_of_date,
               p.modality
        FROM catalysts c
        JOIN catalyst_ticker_history ct ON c.catalyst_id = ct.catalyst_id
        LEFT JOIN catalyst_market_features mf ON c.catalyst_id = mf.catalyst_id
        LEFT JOIN catalyst_trading_cutoffs tc ON c.catalyst_id = tc.catalyst_id
        LEFT JOIN programs p ON c.program_id = p.program_id
        """
    ).fetchall()

    stats = {"updated": 0, "skipped_sec": 0}
    for catalyst_id, ticker, price, as_of, modality in rows:
        existing = conn.execute(
            "SELECT data_source FROM asset_exposure WHERE catalyst_id = ?", (catalyst_id,)
        ).fetchone()
        if existing and existing[0] == "sec_edgar":
            stats["skipped_sec"] += 1
            continue
        sponsor_class, dependency = classify_ticker(ticker, cfg)
        is_lead = 1 if sponsor_class == "small_cap" else 0
        is_single = 1 if sponsor_class == "small_cap" else 0
        # Market cap proxy: price alone is not market cap; store price for future SEC merge
        market_cap_proxy = float(price) if price else None

        conn.execute(
            """
            INSERT INTO asset_exposure (
                catalyst_id, market_cap_usd, is_lead_asset, is_single_asset_company,
                company_dependency, as_of_date, data_source
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(catalyst_id) DO UPDATE SET
                market_cap_usd = excluded.market_cap_usd,
                is_lead_asset = excluded.is_lead_asset,
                is_single_asset_company = excluded.is_single_asset_company,
                company_dependency = excluded.company_dependency,
                as_of_date = excluded.as_of_date,
                data_source = excluded.data_source
            """,
            (
                catalyst_id,
                market_cap_proxy,
                is_lead,
                is_single,
                dependency,
                as_of,
                f"heuristic_{sponsor_class}",
            ),
        )
        stats["updated"] += 1

    conn.commit()
    conn.close()
    return stats


def load_exposure_frame(db_path: Path | None = None) -> pd.DataFrame:
    db_path = db_path or project_root() / "data" / "processed" / "research.db"
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(
        """
        SELECT c.catalyst_id, c.drug_name, c.indication, ct.ticker_at_event,
               ae.company_dependency, ae.is_lead_asset, ae.is_single_asset_company,
               ae.data_source AS exposure_source
        FROM catalysts c
        JOIN catalyst_ticker_history ct ON c.catalyst_id = ct.catalyst_id
        LEFT JOIN asset_exposure ae ON c.catalyst_id = ae.catalyst_id
        """,
        conn,
    )
    conn.close()
    return df
