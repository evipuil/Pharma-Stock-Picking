"""Tests for catalyst price fetch with point-in-time tickers."""

from unittest.mock import patch

import pandas as pd

from src.market_data.catalyst_prices import fetch_for_catalyst


def _price_df(start: str, end: str) -> pd.DataFrame:
    dates = pd.bdate_range(start, end)
    return pd.DataFrame(
        {
            "date": dates,
            "open": 1.0,
            "high": 1.0,
            "low": 1.0,
            "close": 1.0,
            "adj_close": 1.0,
            "volume": 1000,
        }
    )


def test_skips_predecessor_when_history_ends_before_event():
    immu = _price_df("2009-01-02", "2017-03-31")
    gild = _price_df("2009-01-02", "2020-12-31")

    def fake_fetch(ticker, start, end=None, force_refresh=False):
        if ticker == "IMMU":
            return immu
        if ticker == "GILD":
            return gild
        return pd.DataFrame()

    with patch("src.market_data.catalyst_prices.fetch_or_load", side_effect=fake_fetch):
        df, used = fetch_for_catalyst("GILD", "2017-06-06", start="2008-01-01")

    assert used == "GILD"
    assert len(df) > 0
    assert df["date"].max() >= pd.Timestamp("2017-06-06")


def test_uses_predecessor_when_it_covers_event():
    pcyc = _price_df("2009-01-02", "2015-05-01")
    abbv = _price_df("2013-01-02", "2020-12-31")

    def fake_fetch(ticker, start, end=None, force_refresh=False):
        if ticker == "PCYC":
            return pcyc
        if ticker == "ABBV":
            return abbv
        return pd.DataFrame()

    with patch("src.market_data.catalyst_prices.fetch_or_load", side_effect=fake_fetch):
        df, used = fetch_for_catalyst("ABBV", "2012-12-08", start="2008-01-01")

    assert used == "PCYC"
    assert not df.empty
