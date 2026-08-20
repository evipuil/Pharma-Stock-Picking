"""Event study for Wave 1 programs with financial events."""

from __future__ import annotations

import sqlite3
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import project_root
from src.event_study.car import cumulative_abnormal_return, estimate_market_model_beta
from src.market_data.prices import download_adj_close


def run_event_study(db_path: Path | None = None) -> pd.DataFrame:
    db_path = db_path or project_root() / "data" / "processed" / "research.db"
    conn = sqlite3.connect(db_path)
    events = pd.read_sql_query(
        """
        SELECT e.event_id, e.program_id, e.event_date, c.ticker, p.drug_name, o.clinical_success
        FROM program_financial_events e
        JOIN programs p ON e.program_id = p.program_id
        JOIN companies c ON p.company_id = c.company_id
        LEFT JOIN trial_outcomes o ON p.program_id = o.program_id AND o.outcome_level = 'PHASE2'
        """,
        conn,
    )
    conn.close()

    if events.empty:
        return pd.DataFrame()

    spy = download_adj_close("SPY", start="2010-01-01")
    spy["date"] = pd.to_datetime(spy["date"])
    spy = spy.set_index("date")["adj_close"].pct_change().dropna()

    rows = []
    for _, ev in events.iterrows():
        ticker = ev["ticker"]
        event_date = pd.to_datetime(ev["event_date"])
        try:
            stock = download_adj_close(ticker, start=(event_date - timedelta(days=400)).strftime("%Y-%m-%d"))
        except Exception:
            continue
        if stock.empty:
            continue
        stock["date"] = pd.to_datetime(stock["date"])
        stock_ret = stock.set_index("date")["adj_close"].pct_change().dropna()

        aligned = pd.concat([stock_ret, spy], axis=1, join="inner").dropna()
        aligned.columns = ["stock", "market"]
        if len(aligned) < 60:
            continue

        est = aligned.loc[aligned.index < event_date - timedelta(days=30)]
        if len(est) < 30:
            continue
        alpha, beta = estimate_market_model_beta(est["stock"], est["market"])

        # Event window [-1, +1] trading days
        idx = aligned.index.get_indexer([event_date], method="nearest")[0]
        if idx < 1 or idx >= len(aligned) - 1:
            continue
        window_idx = aligned.index[idx - 1 : idx + 2]
        car = cumulative_abnormal_return(
            aligned["stock"], aligned["market"], alpha, beta, window_idx
        )
        rows.append({
            "program_id": ev["program_id"],
            "drug_name": ev["drug_name"],
            "ticker": ticker,
            "event_date": ev["event_date"],
            "clinical_success": ev["clinical_success"],
            "car_-1_+1": car,
            "alpha": alpha,
            "beta": beta,
        })

    df = pd.DataFrame(rows)
    out = project_root() / "data" / "processed" / "event_study_results.csv"
    df.to_csv(out, index=False)
    return df


def main() -> None:
    df = run_event_study()
    if df.empty:
        print("No event study results (missing prices or events)")
        return
    print(df.to_string(index=False))
    print(f"\nMean CAR: {df['car_-1_+1'].mean():.4f}")
