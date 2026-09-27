"""Stooq daily OHLCV adapter (free tier requires STOOQ_API_KEY)."""

from __future__ import annotations

import io
import os

import pandas as pd
import requests

from src.config import load_yaml, project_root
from src.market_data.adapters.base import PriceAdapter


class StooqAdapter(PriceAdapter):
    """
    Stooq historical daily CSV download.

    Register at https://stooq.com/db/i/ for a free API key (daily quota).
    Set STOOQ_API_KEY in the environment.
    """

    name = "stooq"

    def __init__(self, api_key: str | None = None, timeout: int = 30) -> None:
        cfg = load_yaml(project_root() / "configs" / "data_sources.yaml")
        stooq_cfg = cfg.get("market_data", {}).get("stooq", {})
        self.base_url = stooq_cfg.get("base_url", "https://stooq.com/q/d/l/")
        self.api_key = api_key or os.environ.get(
            stooq_cfg.get("api_key_env", "STOOQ_API_KEY")
        )
        self.timeout = timeout

    def supports_ticker(self, ticker: str) -> bool:
        return bool(self.api_key and ticker)

    def _symbol(self, ticker: str) -> str:
        t = ticker.lower()
        return t if t.endswith(".us") else f"{t}.us"

    def fetch_daily(
        self,
        ticker: str,
        start: str,
        end: str | None = None,
    ) -> pd.DataFrame:
        if not self.api_key:
            return _empty_frame()

        start_ts = pd.Timestamp(start)
        end_ts = pd.Timestamp(end) if end else pd.Timestamp.today()

        params = {
            "s": self._symbol(ticker),
            "i": "d",
            "d1": start_ts.strftime("%Y%m%d"),
            "d2": end_ts.strftime("%Y%m%d"),
            "f": "sd2ohlcv",
            "h": "",
            "e": "csv",
            "apikey": self.api_key,
        }
        resp = requests.get(self.base_url, params=params, timeout=self.timeout)
        if resp.status_code != 200:
            return _empty_frame()
        text = resp.text.strip()
        if not text or text.startswith("<") or "Date" not in text.split("\n", 1)[0]:
            return _empty_frame()

        try:
            df = pd.read_csv(io.StringIO(resp.text))
        except pd.errors.EmptyDataError:
            return _empty_frame()

        df.columns = [str(c).strip().lower() for c in df.columns]
        if "date" not in df.columns:
            return _empty_frame()

        df["date"] = pd.to_datetime(df["date"])
        rename = {"vol": "volume"}
        df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
        if "adj_close" not in df.columns and "close" in df.columns:
            df["adj_close"] = df["close"]

        cols = [
            c
            for c in ["date", "open", "high", "low", "close", "adj_close", "volume"]
            if c in df.columns
        ]
        return df[cols].sort_values("date").reset_index(drop=True)


def _empty_frame() -> pd.DataFrame:
    return pd.DataFrame(
        columns=["date", "open", "high", "low", "close", "adj_close", "volume"]
    )
