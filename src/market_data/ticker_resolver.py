"""Resolve point-in-time ticker for historical price fetches."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import yaml

from src.config import project_root


def _load_mappings() -> list[dict]:
    path = project_root() / "configs" / "ticker_history_map.yaml"
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data.get("mappings", [])


def resolve_price_tickers(
    ticker_at_event: str,
    announcement_date: date | str | None,
) -> list[str]:
    """
    Return ordered ticker candidates for price fetch (predecessor first when applicable).

    The original ticker_at_event is always included as fallback.
    """
    ticker = (ticker_at_event or "").upper()
    if not ticker:
        return []

    if announcement_date is None:
        return [ticker]

    ann = date.fromisoformat(str(announcement_date)[:10])
    candidates: list[str] = []

    for mapping in _load_mappings():
        if mapping.get("current_ticker", "").upper() != ticker:
            continue
        before = date.fromisoformat(str(mapping["before_date"])[:10])
        if ann < before:
            pred = mapping.get("use_ticker", "").upper()
            if pred and pred not in candidates:
                candidates.append(pred)

    if ticker not in candidates:
        candidates.append(ticker)
    return candidates


def resolve_primary_ticker(
    ticker_at_event: str,
    announcement_date: date | str | None,
) -> str:
    """First ticker to try for price fetch."""
    tickers = resolve_price_tickers(ticker_at_event, announcement_date)
    return tickers[0] if tickers else (ticker_at_event or "").upper()
