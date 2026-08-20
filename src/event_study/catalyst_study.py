"""Multi-window catalyst event study with SPY/XBI benchmarks."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import load_yaml, project_root
from src.event_study.car import cumulative_abnormal_return, estimate_market_model_beta
from src.event_study.windows import nearest_trading_index, parse_window, window_slice
from src.market_data.catalyst_prices import fetch_for_catalyst
from src.market_data.history import load_benchmarks


def _estimation_slice(index: pd.DatetimeIndex, event_idx: int, est_start: int, est_end: int):
    lo = max(0, event_idx + est_start)
    hi = min(len(index) - 1, event_idx + est_end)
    if lo >= hi:
        return index[:0]
    return index[lo : hi + 1]


def run_catalyst_event_study(
    db_path: Path | None = None,
    persist: bool = True,
) -> pd.DataFrame:
    cfg = load_yaml(project_root() / "configs" / "stock_picking.yaml")
    es_cfg = cfg["event_study"]
    db_path = db_path or project_root() / "data" / "processed" / "research.db"

    conn = sqlite3.connect(db_path)
    catalysts = pd.read_sql_query(
        """
        SELECT c.catalyst_id, c.drug_name, c.indication, c.announcement_date,
               c.clinical_success, c.outcome_category,
               ct.ticker_at_event AS ticker
        FROM catalysts c
        JOIN catalyst_ticker_history ct ON c.catalyst_id = ct.catalyst_id
        WHERE c.announcement_date IS NOT NULL
        """,
        conn,
    )

    if catalysts.empty:
        conn.close()
        return pd.DataFrame()

    start = cfg["market_data"]["history_start"]
    benchmarks = load_benchmarks(start=start)
    spy = benchmarks.get("SPY", pd.Series(dtype=float))
    xbi = benchmarks.get("XBI", pd.Series(dtype=float))

    rows: list[dict] = []
    for _, cat in catalysts.iterrows():
        ticker = cat["ticker"]
        event_date = pd.to_datetime(cat["announcement_date"])
        cfg_start = cfg["market_data"]["history_start"]
        fetch_start = min(pd.Timestamp(cfg_start), event_date - timedelta(days=400))
        try:
            prices, ticker_used = fetch_for_catalyst(
                ticker, cat["announcement_date"], start=fetch_start.strftime("%Y-%m-%d")
            )
        except Exception:
            rows.append(_failed_row(cat, "price_fetch_error"))
            continue
        if prices.empty:
            rows.append(_failed_row(cat, "no_price_data"))
            continue

        prices["date"] = pd.to_datetime(prices["date"])
        stock_ret = prices.set_index("date")["adj_close"].astype(float).pct_change().dropna()

        aligned = pd.concat([stock_ret, spy, xbi], axis=1, join="inner").dropna()
        aligned.columns = ["stock", "spy", "xbi"]
        if len(aligned) < 80:
            rows.append(_failed_row(cat, "insufficient_history"))
            continue

        event_idx = nearest_trading_index(aligned.index, event_date)
        if event_idx is None:
            rows.append(_failed_row(cat, "no_event_date_match"))
            continue

        min_pre_event = abs(es_cfg["estimation_window"]["start_offset_trading_days"])
        if event_idx < min_pre_event:
            rows.append(_failed_row(cat, "insufficient_pre_event_history"))
            continue

        matched_date = aligned.index[event_idx]
        if abs((matched_date - event_date).days) > 7:
            rows.append(_failed_row(cat, "event_date_outside_price_range"))
            continue

        est_idx = _estimation_slice(
            aligned.index,
            event_idx,
            es_cfg["estimation_window"]["start_offset_trading_days"],
            es_cfg["estimation_window"]["end_offset_trading_days"],
        )
        if len(est_idx) < 30:
            rows.append(_failed_row(cat, "short_estimation_window"))
            continue

        alpha_s, beta_s = estimate_market_model_beta(
            aligned.loc[est_idx, "stock"], aligned.loc[est_idx, "spy"]
        )
        alpha_x, beta_x = estimate_market_model_beta(
            aligned.loc[est_idx, "stock"], aligned.loc[est_idx, "xbi"]
        )

        for wlabel in es_cfg["event_windows"]:
            try:
                w0, w1 = parse_window(wlabel)
            except ValueError:
                continue
            win = window_slice(aligned.index, event_idx, w0, w1)
            if len(win) == 0:
                continue

            raw_ret = float(aligned.loc[win, "stock"].sum())
            spy_adj = float(aligned.loc[win, "stock"].sum() - aligned.loc[win, "spy"].sum())
            xbi_adj = float(aligned.loc[win, "stock"].sum() - aligned.loc[win, "xbi"].sum())
            car_spy = cumulative_abnormal_return(
                aligned["stock"], aligned["spy"], alpha_s, beta_s, win
            )
            car_xbi = cumulative_abnormal_return(
                aligned["stock"], aligned["xbi"], alpha_x, beta_x, win
            )

            for benchmark, car, alpha, beta in [
                ("RAW", raw_ret, None, None),
                ("SPY", spy_adj, None, None),
                ("XBI", xbi_adj, None, None),
                ("MARKET_MODEL", car_spy, alpha_s, beta_s),
                ("XBI_MODEL", car_xbi, alpha_x, beta_x),
            ]:
                rec = {
                    "catalyst_id": cat["catalyst_id"],
                    "drug_name": cat["drug_name"],
                    "ticker": ticker,
                    "announcement_date": cat["announcement_date"],
                    "clinical_success": cat["clinical_success"],
                    "outcome_category": cat["outcome_category"],
                    "window_label": wlabel,
                    "benchmark": benchmark,
                    "raw_return": raw_ret if benchmark == "RAW" else None,
                    "car": car,
                    "alpha": alpha,
                    "beta": beta,
                    "price_status": "ok",
                }
                rows.append(rec)
                if persist:
                    _upsert_es(conn, cat["catalyst_id"], wlabel, benchmark, rec, est_idx, ticker_used)

    conn.commit()
    conn.close()

    df = pd.DataFrame(rows)
    out = project_root() / "data" / "processed" / "catalyst_event_study.csv"
    if not df.empty:
        df.to_csv(out, index=False)
    return df


def _failed_row(cat: pd.Series, reason: str) -> dict:
    return {
        "catalyst_id": cat["catalyst_id"],
        "drug_name": cat["drug_name"],
        "ticker": cat.get("ticker"),
        "announcement_date": cat["announcement_date"],
        "clinical_success": cat["clinical_success"],
        "outcome_category": cat.get("outcome_category"),
        "window_label": None,
        "benchmark": None,
        "car": np.nan,
        "price_status": reason,
    }


def _upsert_es(conn, catalyst_id, wlabel, benchmark, rec, est_idx, ticker):
    conn.execute(
        """
        DELETE FROM catalyst_event_study
        WHERE catalyst_id = ? AND window_label = ? AND benchmark = ?
        """,
        (catalyst_id, wlabel, benchmark),
    )
    conn.execute(
        """
        INSERT INTO catalyst_event_study (
            es_id, catalyst_id, window_label, benchmark, raw_return, car,
            alpha, beta, estimation_window_start, estimation_window_end,
            n_estimation_days, price_source, ticker_used
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            str(uuid.uuid4()),
            catalyst_id,
            wlabel,
            benchmark,
            rec.get("raw_return"),
            rec.get("car"),
            rec.get("alpha"),
            rec.get("beta"),
            str(est_idx[0])[:10] if len(est_idx) else None,
            str(est_idx[-1])[:10] if len(est_idx) else None,
            len(est_idx),
            "yfinance",
            ticker,
        ),
    )


def summarize_by_outcome(df: pd.DataFrame) -> pd.DataFrame:
    """Mean CAR [-1,+1] MARKET_MODEL by success/failure."""
    if df.empty:
        return pd.DataFrame()
    sub = df[
        (df["window_label"] == "[-1,+1]")
        & (df["benchmark"] == "MARKET_MODEL")
        & (df["price_status"] == "ok")
    ]
    return (
        sub.groupby("clinical_success")["car"]
        .agg(["count", "mean", "median", "std"])
        .reset_index()
    )
