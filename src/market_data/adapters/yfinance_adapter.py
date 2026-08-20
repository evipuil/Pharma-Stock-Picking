"""yfinance price adapter (active + recent tickers; limited delisted coverage)."""

from __future__ import annotations

import pandas as pd

from src.market_data.adapters.base import PriceAdapter


class YFinanceAdapter(PriceAdapter):
    name = "yfinance"

    def supports_ticker(self, ticker: str) -> bool:
        return bool(ticker and ticker.strip())

    def fetch_daily(
        self,
        ticker: str,
        start: str,
        end: str | None = None,
    ) -> pd.DataFrame:
        import yfinance as yf

        data = yf.download(
            ticker,
            start=start,
            end=end,
            auto_adjust=False,
            progress=False,
        )
        if data.empty:
            return _empty_frame()

        out = data.reset_index()
        if isinstance(out.columns, pd.MultiIndex):
            out.columns = [
                str(c[0]).lower() if isinstance(c, tuple) else str(c).lower()
                for c in out.columns
            ]
        else:
            out.columns = [str(c).lower() for c in out.columns]

        rename = {
            "adj close": "adj_close",
            "stock splits": "split",
            "dividends": "dividend",
        }
        out = out.rename(columns={k: v for k, v in rename.items() if k in out.columns})

        if "adj_close" not in out.columns and "close" in out.columns:
            out["adj_close"] = out["close"]

        cols = [c for c in ["date", "open", "high", "low", "close", "adj_close", "volume"] if c in out.columns]
        return out[cols].copy()


def _empty_frame() -> pd.DataFrame:
    return pd.DataFrame(
        columns=["date", "open", "high", "low", "close", "adj_close", "volume"]
    )
