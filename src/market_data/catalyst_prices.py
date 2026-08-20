"""Fetch prices trying point-in-time ticker mappings."""

from __future__ import annotations

from datetime import date

import pandas as pd

from src.market_data.history import fetch_or_load
from src.market_data.ticker_resolver import resolve_price_tickers


def fetch_for_catalyst(
    ticker_at_event: str,
    announcement_date: date | str,
    start: str,
    end: str | None = None,
    force_refresh: bool = False,
) -> tuple[pd.DataFrame, str]:
    """
    Try predecessor tickers then current ticker.

    Returns (price_df, ticker_used).
    """
    ann = pd.Timestamp(announcement_date)
    last_needed = ann - pd.Timedelta(days=7)
    first_needed = ann + pd.Timedelta(days=7)

    for ticker in resolve_price_tickers(ticker_at_event, announcement_date):
        df = fetch_or_load(ticker, start=start, end=end, force_refresh=force_refresh)
        if df.empty:
            continue
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])
        if df["date"].min() <= first_needed and df["date"].max() >= last_needed:
            return df, ticker
    return pd.DataFrame(), ticker_at_event.upper()
