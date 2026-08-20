"""Tests for curated announcement overrides."""

from src.catalysts.apply_announcement_overrides import _load_overrides


def test_overrides_have_dates_and_tickers():
    ov = _load_overrides()
    assert "CAT-F013" in ov
    assert ov["CAT-F013"]["announcement_date"] == "2015-10-20"
    assert ov["CAT-F026"]["ticker"] == "CLDX"
    assert ov["CAT-C068"]["ticker"] == "STML"
    assert ov["CAT-F045"]["ticker"] == "OMED"
