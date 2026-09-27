"""Pre-catalyst market expectation features (Stage 5)."""

from __future__ import annotations

import sqlite3
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import load_yaml, project_root
from src.market_data.catalyst_prices import fetch_for_catalyst
from src.market_data.history import load_benchmarks


def _apply_schema(conn: sqlite3.Connection) -> None:
    schema = project_root() / "sql" / "schema_market_features.sql"
    if schema.exists():
        conn.executescript(schema.read_text(encoding="utf-8"))


def _cum_return(rets: pd.Series, n_days: int) -> float | None:
    if len(rets) < n_days:
        return None
    window = rets.iloc[-n_days:]
    return float((1 + window).prod() - 1)


def _realized_vol(rets: pd.Series, n_days: int = 20) -> float | None:
    if len(rets) < n_days:
        return None
    return float(rets.iloc[-n_days:].std() * np.sqrt(252))


def compute_features_for_catalyst(
    ticker: str,
    cutoff_date: pd.Timestamp,
    stock_prices: pd.DataFrame,
    xbi_rets: pd.Series,
) -> dict | None:
    """Compute market features using only data strictly before cutoff_date."""
    prices = stock_prices.copy()
    prices["date"] = pd.to_datetime(prices["date"])
    prices = prices.sort_values("date")
    prices = prices[prices["date"] < cutoff_date]
    if len(prices) < 30:
        return None

    close = prices.set_index("date")["adj_close"].astype(float)
    rets = close.pct_change().dropna()
    volume = (
        prices.set_index("date")["volume"].astype(float) if "volume" in prices.columns else None
    )

    price_at = float(close.iloc[-1])
    high_52w = float(close.iloc[-min(252, len(close)) :].max())
    dist_52w = (price_at / high_52w - 1.0) if high_52w > 0 else None

    # Align XBI for abnormal returns ending at cutoff
    xbi_aligned = xbi_rets.reindex(rets.index).dropna()
    common = rets.index.intersection(xbi_aligned.index)
    if len(common) < 25:
        abn_20 = abn_60 = None
    else:
        sr = rets.loc[common]
        xr = xbi_aligned.loc[common]
        r20 = _cum_return(sr, 20)
        x20 = _cum_return(xr, 20)
        r60 = _cum_return(sr, 60)
        x60 = _cum_return(xr, 60)
        abn_20 = (r20 - x20) if r20 is not None and x20 is not None else None
        abn_60 = (r60 - x60) if r60 is not None and x60 is not None else None

    vol_ratio = None
    if volume is not None and len(volume) >= 20:
        recent = volume.iloc[-5:].mean()
        base = volume.iloc[-60:-5].mean() if len(volume) >= 60 else volume.iloc[:-5].mean()
        if base and base > 0:
            vol_ratio = float(recent / base)

    return {
        "feature_as_of_date": str(close.index[-1].date()),
        "price_at_cutoff": price_at,
        "return_1d": _cum_return(rets, 1),
        "return_5d": _cum_return(rets, 5),
        "return_20d": _cum_return(rets, 20),
        "return_60d": _cum_return(rets, 60),
        "return_120d": _cum_return(rets, 120) if len(rets) >= 120 else None,
        "abnormal_return_20d_xbi": abn_20,
        "abnormal_return_60d_xbi": abn_60,
        "distance_from_52w_high": dist_52w,
        "realized_vol_20d": _realized_vol(rets, 20),
        "volume_ratio_20d": vol_ratio,
        "pre_catalyst_runup_60d": _cum_return(rets, 60),
    }


def compute_all_market_features(db_path: Path | None = None) -> dict:
    cfg = load_yaml(project_root() / "configs" / "stock_picking.yaml")
    start = cfg["market_data"]["history_start"]
    db_path = db_path or project_root() / "data" / "processed" / "research.db"

    conn = sqlite3.connect(db_path)
    _apply_schema(conn)

    xbi = load_benchmarks(start=start).get("XBI", pd.Series(dtype=float))

    rows = conn.execute(
        """
        SELECT c.catalyst_id, ct.ticker_at_event, c.announcement_date,
               COALESCE(tc.entry_cutoff_date, c.trading_cutoff_date, c.announcement_date) AS cutoff
        FROM catalysts c
        JOIN catalyst_ticker_history ct ON c.catalyst_id = ct.catalyst_id
        LEFT JOIN catalyst_trading_cutoffs tc ON c.catalyst_id = tc.catalyst_id
        WHERE cutoff IS NOT NULL
        """
    ).fetchall()

    stats = {"computed": 0, "skipped_no_prices": 0, "errors": 0}

    for catalyst_id, ticker, ann_date, cutoff_str in rows:
        cutoff = pd.Timestamp(cutoff_str)
        try:
            prices, ticker_used = fetch_for_catalyst(
                ticker,
                ann_date or cutoff_str,
                start=(cutoff - timedelta(days=400)).strftime("%Y-%m-%d"),
                end=cutoff.strftime("%Y-%m-%d"),
            )
            feats = compute_features_for_catalyst(ticker_used, cutoff, prices, xbi)
            if feats is None:
                stats["skipped_no_prices"] += 1
                continue

            conn.execute(
                """
                INSERT INTO catalyst_market_features (
                    catalyst_id, as_of_date, ticker, price_at_cutoff,
                    return_1d, return_5d, return_20d, return_60d, return_120d,
                    abnormal_return_20d_xbi, abnormal_return_60d_xbi,
                    distance_from_52w_high, realized_vol_20d, volume_ratio_20d,
                    pre_catalyst_runup_60d, data_source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'yfinance')
                ON CONFLICT(catalyst_id) DO UPDATE SET
                    as_of_date = excluded.as_of_date,
                    ticker = excluded.ticker,
                    price_at_cutoff = excluded.price_at_cutoff,
                    return_1d = excluded.return_1d,
                    return_5d = excluded.return_5d,
                    return_20d = excluded.return_20d,
                    return_60d = excluded.return_60d,
                    return_120d = excluded.return_120d,
                    abnormal_return_20d_xbi = excluded.abnormal_return_20d_xbi,
                    abnormal_return_60d_xbi = excluded.abnormal_return_60d_xbi,
                    distance_from_52w_high = excluded.distance_from_52w_high,
                    realized_vol_20d = excluded.realized_vol_20d,
                    volume_ratio_20d = excluded.volume_ratio_20d,
                    pre_catalyst_runup_60d = excluded.pre_catalyst_runup_60d,
                    computed_at = datetime('now')
                """,
                (
                    catalyst_id,
                    feats["feature_as_of_date"],
                    ticker_used,
                    feats["price_at_cutoff"],
                    feats["return_1d"],
                    feats["return_5d"],
                    feats["return_20d"],
                    feats["return_60d"],
                    feats["return_120d"],
                    feats["abnormal_return_20d_xbi"],
                    feats["abnormal_return_60d_xbi"],
                    feats["distance_from_52w_high"],
                    feats["realized_vol_20d"],
                    feats["volume_ratio_20d"],
                    feats["pre_catalyst_runup_60d"],
                ),
            )
            stats["computed"] += 1
        except Exception:  # noqa: BLE001 - record per-catalyst failures and continue
            stats["errors"] += 1

    conn.commit()
    conn.close()
    return stats


def export_market_features_csv(out_path: Path | None = None) -> Path:
    db_path = project_root() / "data" / "processed" / "research.db"
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(
        """
        SELECT mf.*, c.drug_name, c.indication, c.clinical_success, c.outcome_category
        FROM catalyst_market_features mf
        JOIN catalysts c ON mf.catalyst_id = c.catalyst_id
        """,
        conn,
    )
    conn.close()
    out_path = out_path or project_root() / "data" / "processed" / "catalyst_market_features.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    return out_path
