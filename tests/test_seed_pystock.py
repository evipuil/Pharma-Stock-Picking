"""Tests for pystock price seeding."""

from pathlib import Path
from unittest.mock import patch

import pandas as pd

from src.market_data.seed_pystock import _extract_prices, _normalize


def test_extract_prices_filters_symbols():
    import io
    import tarfile

    csv = (
        "symbol,date,open,high,low,close,volume,adj_close\n"
        "PCYC,2012-01-03,10,11,9,10.5,1000,10.5\n"
        "AAPL,2012-01-03,400,410,390,405,2000,405\n"
    )
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        data = csv.encode("utf-8")
        info = tarfile.TarInfo(name="prices.csv")
        info.size = len(data)
        tf.addfile(info, io.BytesIO(data))
    buf.seek(0)

    out = _extract_prices(buf.read(), {"PCYC"})
    assert list(out) == ["PCYC"]
    assert len(out["PCYC"]) == 1


def test_normalize_columns():
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2012-01-03"]),
            "open": [1.0],
            "high": [2.0],
            "low": [0.5],
            "close": [1.5],
            "adj_close": [1.5],
            "volume": [100],
        }
    )
    norm = _normalize(df)
    assert list(norm.columns) == ["date", "open", "high", "low", "close", "adj_close", "volume"]
