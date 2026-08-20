"""Export delisted ticker prices to local CSV for offline event studies."""

from __future__ import annotations

from pathlib import Path

import yaml

from src.config import load_yaml, project_root
from src.market_data.adapters.base import MissingCredentialsError
from src.market_data.adapters.polygon_adapter import PolygonAdapter
from src.market_data.adapters.eodhd_adapter import EodhdAdapter


def _pick_adapter():
    poly = PolygonAdapter()
    if poly.api_key:
        return poly, poly.name
    eod = EodhdAdapter()
    if eod.api_key:
        return eod, eod.name
    return None, None


def _delisted_tickers() -> list[str]:
    path = project_root() / "configs" / "ticker_delist_map.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    tickers = data.get("tickers", {})
    return sorted(t for t, meta in tickers.items() if meta.get("delisted"))


def export_delisted_prices(
    output_dir: Path | None = None,
    force: bool = False,
) -> dict:
    """
    Fetch delisted tickers via Polygon or EODHD and write data/external/prices/{TICKER}.csv.

    Requires POLYGON_API_KEY or EODHD_API_KEY.
    """
    cfg = load_yaml(project_root() / "configs" / "stock_picking.yaml")
    start = cfg["market_data"]["history_start"]
    out_dir = output_dir or project_root() / "data" / "external" / "prices"
    out_dir.mkdir(parents=True, exist_ok=True)

    adapter, provider = _pick_adapter()
    if adapter is None:
        raise MissingCredentialsError(
            "export_delisted_prices requires POLYGON_API_KEY or EODHD_API_KEY. "
            "See data/external/prices/README.md"
        )

    stats = {"exported": 0, "skipped": 0, "empty": 0, "errors": 0, "provider": provider}

    for ticker in _delisted_tickers():
        csv_path = out_dir / f"{ticker.upper()}.csv"
        if csv_path.exists() and not force:
            stats["skipped"] += 1
            continue
        try:
            df = adapter.fetch_daily(ticker, start=start)
            if df.empty:
                stats["empty"] += 1
                continue
            df.to_csv(csv_path, index=False)
            stats["exported"] += 1
        except Exception:
            stats["errors"] += 1
    return stats
