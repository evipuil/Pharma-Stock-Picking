"""Tests for point-in-time ticker resolution."""

from src.market_data.ticker_resolver import resolve_price_tickers, resolve_primary_ticker


def test_abbv_2012_maps_to_pcyc():
    tickers = resolve_price_tickers("ABBV", "2012-12-08")
    assert tickers[0] == "PCYC"
    assert "ABBV" in tickers


def test_abbv_2015_uses_abbv_only():
    tickers = resolve_price_tickers("ABBV", "2015-06-01")
    assert tickers == ["ABBV"]


def test_bmy_celg_pre_acquisition():
    assert resolve_primary_ticker("BMY", "2018-01-01") == "CELG"


def test_plyx_maps_to_phm_mc():
    assert resolve_primary_ticker("PLYX", "2020-12-02") == "PHM.MC"


def test_qed_maps_to_bbio():
    assert resolve_primary_ticker("QED", "2022-07-15") == "BBIO"


def test_ptla_maps_to_pphm():
    assert resolve_primary_ticker("PTLA", "2012-05-24") == "PPHM"


def test_ocn_maps_to_omed():
    assert resolve_primary_ticker("OCN", "2017-04-10") == "OMED"


def test_sgmo_maps_to_stml():
    assert resolve_primary_ticker("SGMO", "2016-12-05") == "STML"
