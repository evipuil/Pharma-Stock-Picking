"""Tests for price coverage audit."""

from src.market_data.price_coverage import _load_delist_map


def test_delist_map_loads():
    m = _load_delist_map()
    assert "IMMU" in m
    assert m["IMMU"]["delisted"] is True
    assert m["LOXO"]["successor_ticker"] == "LLY"
