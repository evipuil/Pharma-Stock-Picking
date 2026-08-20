"""Tests for Polygon price adapter."""

from unittest.mock import MagicMock, patch

import pandas as pd

from src.market_data.adapters.polygon_adapter import PolygonAdapter


def test_polygon_fetch_parses_bars():
    adapter = PolygonAdapter(api_key="test-key")
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "status": "OK",
        "results": [
            {"t": 1609459200000, "o": 10.0, "h": 11.0, "l": 9.5, "c": 10.5, "v": 100000},
            {"t": 1609545600000, "o": 10.5, "h": 11.5, "l": 10.0, "c": 11.0, "v": 120000},
        ],
    }
    with patch("src.market_data.adapters.polygon_adapter.requests.get", return_value=mock_resp):
        df = adapter.fetch_daily("IMMU", start="2021-01-01", end="2021-01-31")

    assert len(df) == 2
    assert list(df.columns) == ["date", "open", "high", "low", "close", "adj_close", "volume"]
    assert df["adj_close"].iloc[0] == 10.5


def test_polygon_empty_results():
    adapter = PolygonAdapter(api_key="test-key")
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"status": "OK", "results": []}
    with patch("src.market_data.adapters.polygon_adapter.requests.get", return_value=mock_resp):
        df = adapter.fetch_daily("DELISTED", start="2015-01-01")
    assert df.empty
