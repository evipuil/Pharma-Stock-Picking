"""Import a filtered pilot batch of GitHub EventsStockPrices candidates."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import yaml

from src.config import project_root

LARGE_CAP_TICKERS = {
    "MRK", "PFE", "BMY", "ABBV", "JNJ", "GSK", "AZN", "AMGN", "GILD", "REGN",
    "VRTX", "BIIB", "LLY", "NVS", "SNY", "TAK", "RHHBY", "RHHBY", "NVO", "SAN",
    "BAYRY", "ROG", "NOVN", "GSK", "ABT", "MDT", "UNH",
}

READOUT_KEYWORDS = re.compile(
    r"top.?line|primary endpoint|did not meet|met primary|phase [23]|readout|trial data",
    re.I,
)


def filter_github_candidates(
    max_candidates: int = 20,
    year_min: int = 2010,
    year_max: int = 2020,
    source_yaml: Path | None = None,
) -> pd.DataFrame:
    source_yaml = source_yaml or project_root() / "configs" / "github_events_candidates.yaml"
    data = yaml.safe_load(source_yaml.read_text(encoding="utf-8")) or {}
    rows = []
    for cand in data.get("candidates", []):
        ticker = str(cand.get("ticker", "")).upper()
        if ticker in LARGE_CAP_TICKERS:
            continue
        ann = cand.get("announcement_date")
        if not ann:
            continue
        year = int(str(ann)[:4])
        if year < year_min or year > year_max:
            continue
        stage = str(cand.get("github_stage", ""))
        if not re.search(r"Phase\s*[23]", stage, re.I):
            continue
        notes = str(cand.get("notes", ""))
        if not READOUT_KEYWORDS.search(notes):
            continue
        rows.append(cand)
        if len(rows) >= max_candidates:
            break
    return pd.DataFrame(rows)


def write_pilot_import_yaml(
    max_candidates: int = 20,
    output_path: Path | None = None,
) -> Path:
    output_path = output_path or project_root() / "configs" / "github_import_pilot.yaml"
    df = filter_github_candidates(max_candidates=max_candidates)
    entries = []
    for _, row in df.iterrows():
        entries.append(
            {
                "id": row["id"],
                "drug_name": row["drug_name"],
                "ticker": row["ticker"],
                "company_name": row.get("company_name", row["ticker"]),
                "indication": row["indication"],
                "announcement_date": row["announcement_date"],
                "announcement_timing": row.get("announcement_timing", "UNKNOWN"),
                "announcement_source": "GITHUB_EVENTS_STOCK_PRICES",
                "catalyst_type": row.get("catalyst_type", "PHASE2_READOUT"),
                "cohort_phase": "phase_b",
                "search": f"{row['drug_name']} {row['indication']}",
                "notes": row.get("notes", "")[:200],
            }
        )
    doc = {
        "phase_b_target": 250,
        "source": "ejeej/EventsStockPrices pilot import",
        "note": "Outcome-agnostic; CT.gov NCT resolved at import time",
        "candidates": entries,
    }
    output_path.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return output_path


def import_github_pilot(max_candidates: int = 20, max_new: int | None = None) -> dict:
    yaml_path = write_pilot_import_yaml(max_candidates=max_candidates)
    from src.catalysts.expand_cohort import expand_catalyst_cohort

    stats = expand_catalyst_cohort(max_new=max_new, config_path=yaml_path)
    stats["pilot_yaml"] = str(yaml_path)
    stats["pilot_candidates"] = max_candidates
    return stats
