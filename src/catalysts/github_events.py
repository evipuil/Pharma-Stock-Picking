"""Integrate ejeej/EventsStockPrices GitHub data with catalyst registry."""

from __future__ import annotations

import json
import re
import sqlite3
from datetime import date, timedelta
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd
import yaml

from src.config import project_root

EVENTS_CSV = (
    project_root()
    / "data"
    / "external"
    / "github"
    / "EventsStockPrices"
    / "clinical_phase_events.csv"
)
ALL_EVENTS_CSV = (
    project_root()
    / "data"
    / "external"
    / "github"
    / "EventsStockPrices"
    / "events.csv"
)


def _norm(s: str) -> str:
    s = (s or "").lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return " ".join(s.split())


def _drug_similarity(a: str, b: str) -> float:
    na, nb = _norm(a), _norm(b)
    if not na or not nb:
        return 0.0
    if na in nb or nb in na:
        return 0.95
    return SequenceMatcher(None, na, nb).ratio()


def _is_phase_clinical(stage: str) -> bool:
    s = (stage or "").lower()
    return "phase 2" in s or "phase 3" in s


def load_github_events(clinical_only: bool = True) -> pd.DataFrame:
    path = EVENTS_CSV if clinical_only else ALL_EVENTS_CSV
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Run: python -m src.cli seed-github-data"
        )
    df = pd.read_csv(path, parse_dates=["event_date"])
    return df


def load_catalyst_registry(db_path: Path | None = None) -> pd.DataFrame:
    db_path = db_path or project_root() / "data" / "processed" / "research.db"
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(
        """
        SELECT c.catalyst_id, c.drug_name, c.indication, c.announcement_date,
               c.announcement_source, c.announcement_timing,
               ct.ticker_at_event AS ticker, c.clinical_success, c.outcome_category
        FROM catalysts c
        JOIN catalyst_ticker_history ct ON c.catalyst_id = ct.catalyst_id
        WHERE c.announcement_date IS NOT NULL
        """,
        conn,
    )
    conn.close()
    df["announcement_date"] = pd.to_datetime(df["announcement_date"])
    return df


def _best_event_match(
    row: pd.Series,
    events: pd.DataFrame,
    window_days: int = 365,
) -> pd.Series | None:
    ticker = str(row["ticker"]).upper()
    sub = events[events["ticker"].str.upper() == ticker].copy()
    if sub.empty:
        return None

    sub["drug_score"] = sub["drug"].map(lambda d: _drug_similarity(row["drug_name"], d))
    sub = sub[sub["drug_score"] >= 0.45]
    if sub.empty:
        return None

    sub["date_delta"] = (sub["event_date"] - row["announcement_date"]).abs().dt.days
    sub = sub[sub["date_delta"] <= window_days]
    if sub.empty:
        return None

    sub = sub.sort_values(["drug_score", "date_delta"], ascending=[False, True])
    return sub.iloc[0]


def validate_catalyst_dates(
    window_days: int = 365,
    db_path: Path | None = None,
) -> pd.DataFrame:
    """Match each registry catalyst to nearest GitHub clinical event."""
    registry = load_catalyst_registry(db_path)
    events = load_github_events(clinical_only=True)

    rows = []
    for _, cat in registry.iterrows():
        match = _best_event_match(cat, events, window_days=window_days)
        if match is None:
            rows.append(
                {
                    "catalyst_id": cat["catalyst_id"],
                    "ticker": cat["ticker"],
                    "drug_name": cat["drug_name"],
                    "registry_date": cat["announcement_date"],
                    "announcement_source": cat["announcement_source"],
                    "github_date": pd.NaT,
                    "date_delta_days": None,
                    "drug_score": None,
                    "github_drug": None,
                    "github_stage": None,
                    "github_event_desc": None,
                    "match_status": "NO_MATCH",
                }
            )
            continue

        delta = int((match["event_date"] - cat["announcement_date"]).days)
        abs_delta = abs((match["event_date"] - cat["announcement_date"]).days)

        if abs_delta <= 7:
            status = "EXACT"
        elif abs_delta <= 30:
            status = "CLOSE"
        elif abs_delta <= 90:
            status = "MODERATE_DRIFT"
        else:
            status = "LARGE_DRIFT"

        rows.append(
            {
                "catalyst_id": cat["catalyst_id"],
                "ticker": cat["ticker"],
                "drug_name": cat["drug_name"],
                "registry_date": cat["announcement_date"],
                "announcement_source": cat["announcement_source"],
                "github_date": match["event_date"],
                "date_delta_days": delta,
                "drug_score": round(float(match["drug_score"]), 3),
                "github_drug": match["drug"],
                "github_stage": match["stage_normalized"],
                "github_event_desc": (match.get("event_desc") or "")[:200],
                "match_status": status,
            }
        )

    return pd.DataFrame(rows)


def suggest_github_overrides(
    validation: pd.DataFrame,
    min_drug_score: float = 0.7,
    min_abs_delta_days: int = 30,
) -> dict:
    """
    Suggest announcement date corrections where registry date diverges from GitHub
    and current source is inferred/legacy (not curated press release).
    """
    inferred_sources = {
        "INFERRED_T0_PLUS_18MO",
        "INFERRED_CTGOV_RESULTS",
        "LEGACY_UNTAGGED",
        None,
    }
    suggestions = {}
    for _, row in validation.iterrows():
        if row["match_status"] == "NO_MATCH":
            continue
        if abs(row["date_delta_days"] or 0) < min_abs_delta_days:
            continue
        if (row["drug_score"] or 0) < min_drug_score:
            continue
        if row["announcement_source"] not in inferred_sources:
            continue
        if row["match_status"] not in ("MODERATE_DRIFT", "LARGE_DRIFT"):
            continue

        suggestions[row["catalyst_id"]] = {
            "ticker": row["ticker"],
            "announcement_date": str(pd.Timestamp(row["github_date"]).date()),
            "announcement_timing": "UNKNOWN",
            "announcement_source": "GITHUB_EVENTS_STOCK_PRICES",
            "source_url": "https://github.com/ejeej/EventsStockPrices",
            "notes": (
                f"Suggested from BioPharmCatalyst events; delta={row['date_delta_days']}d "
                f"vs {row['registry_date'].date()}; drug_score={row['drug_score']}"
            ),
        }
    return suggestions


def export_github_candidates(
    year_min: int = 2010,
    year_max: int = 2020,
    max_candidates: int = 200,
    db_path: Path | None = None,
) -> pd.DataFrame:
    """
    Export Phase 2/3 clinical events not already represented in catalyst registry.
    Outcome-agnostic — for cohort expansion review only.
    """
    registry = load_catalyst_registry(db_path)
    events = load_github_events(clinical_only=True)

    events = events[
        (events["event_date"].dt.year >= year_min)
        & (events["event_date"].dt.year <= year_max)
    ].copy()
    events = events[events["stage_normalized"].str.contains(r"Phase\s*[23]", case=False, na=False, regex=True)]

    registry_keys = set()
    for _, r in registry.iterrows():
        registry_keys.add((str(r["ticker"]).upper(), _norm(r["drug_name"])))

    rows = []
    seen: set[tuple[str, str, date]] = set()
    for _, ev in events.sort_values("event_date").iterrows():
        ticker = str(ev["ticker"]).upper()
        drug_norm = _norm(str(ev["drug"]))
        key = (ticker, drug_norm)
        dedupe = (ticker, drug_norm, pd.Timestamp(ev["event_date"]).date())
        if dedupe in seen:
            continue
        seen.add(dedupe)

        # Skip if likely already in registry (ticker + drug overlap)
        if any(
            ticker == tk and (_drug_similarity(drug_norm, dn) >= 0.6 or drug_norm in dn or dn in drug_norm)
            for tk, dn in registry_keys
        ):
            continue

        rows.append(
            {
                "candidate_id": f"GH{len(rows)+1:04d}",
                "ticker": ticker,
                "drug_name": str(ev["drug"])[:120],
                "indication": str(ev["disease"])[:120],
                "announcement_date": str(pd.Timestamp(ev["event_date"]).date()),
                "stage": ev["stage_normalized"],
                "event_desc": (ev.get("event_desc") or "")[:300],
                "source": "ejeej/EventsStockPrices",
                "cohort_phase": "phase_b",
                "announcement_source": "GITHUB_EVENTS_STOCK_PRICES",
            }
        )
        if len(rows) >= max_candidates:
            break

    return pd.DataFrame(rows)


def write_github_candidates_yaml(candidates: pd.DataFrame, path: Path | None = None) -> Path:
    path = path or project_root() / "configs" / "github_events_candidates.yaml"
    entries = []
    for _, row in candidates.iterrows():
        entries.append(
            {
                "id": row["candidate_id"],
                "drug_name": row["drug_name"],
                "ticker": row["ticker"],
                "company_name": row["ticker"],
                "indication": row["indication"],
                "announcement_date": row["announcement_date"],
                "announcement_timing": "UNKNOWN",
                "announcement_source": "GITHUB_EVENTS_STOCK_PRICES",
                "catalyst_type": "PHASE2_READOUT",
                "cohort_phase": row.get("cohort_phase", "phase_b"),
                "github_stage": row["stage"],
                "notes": row.get("event_desc", "")[:200],
            }
        )
    doc = {
        "phase_b_target": 250,
        "source": "ejeej/EventsStockPrices",
        "note": "Outcome-agnostic expansion candidates; review before expand-catalysts",
        "candidates": entries,
    }
    path.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return path


def load_github_date_suggestions(path: Path | None = None) -> dict:
    path = path or project_root() / "configs" / "github_events_date_suggestions.yaml"
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data.get("suggestions", {})


def merge_github_suggestions_into_overrides(
    suggestions: dict | None = None,
    overrides_path: Path | None = None,
) -> tuple[dict, int]:
    """Append GitHub suggestions to catalyst_announcement_overrides.yaml (skip existing keys)."""
    suggestions = suggestions or load_github_date_suggestions()
    overrides_path = overrides_path or project_root() / "configs" / "catalyst_announcement_overrides.yaml"
    doc = yaml.safe_load(overrides_path.read_text(encoding="utf-8")) or {}
    overrides = doc.get("overrides", {})
    added = 0
    for catalyst_id, spec in suggestions.items():
        if catalyst_id in overrides:
            continue
        overrides[catalyst_id] = spec
        added += 1
    doc["overrides"] = overrides
    overrides_path.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return overrides, added


def apply_github_date_suggestions(
    db_path: Path | None = None,
    merge_overrides: bool = True,
) -> dict:
    """
    Apply GitHub event date suggestions to the catalyst registry.
    Skips catalysts already in catalyst_announcement_overrides.yaml.
    """
    from src.catalysts.apply_announcement_overrides import apply_announcement_overrides

    suggestions = load_github_date_suggestions()
    overrides_path = project_root() / "configs" / "catalyst_announcement_overrides.yaml"
    existing = yaml.safe_load(overrides_path.read_text(encoding="utf-8")) or {}
    existing_ids = set((existing.get("overrides") or {}).keys())

    pending = {k: v for k, v in suggestions.items() if k not in existing_ids}
    skipped = len(suggestions) - len(pending)

    merged = 0
    if merge_overrides and pending:
        _, merged = merge_github_suggestions_into_overrides(pending, overrides_path)

    to_apply = pending if not merge_overrides else None
    stats = apply_announcement_overrides(db_path=db_path, overrides=to_apply)
    stats["github_suggestions_total"] = len(suggestions)
    stats["github_suggestions_pending"] = len(pending)
    stats["github_suggestions_skipped_existing"] = skipped
    stats["github_suggestions_merged_to_yaml"] = merged
    return stats


def generate_github_validation_report(db_path: Path | None = None) -> Path:
    validation = validate_catalyst_dates(db_path=db_path)
    suggestions = suggest_github_overrides(validation)

    out_csv = project_root() / "data" / "processed" / "github_events_validation.csv"
    validation.to_csv(out_csv, index=False)

    candidates = export_github_candidates(db_path=db_path)
    cand_csv = project_root() / "data" / "processed" / "github_events_candidates.csv"
    candidates.to_csv(cand_csv, index=False)
    yaml_path = write_github_candidates_yaml(candidates)

    sugg_path = project_root() / "configs" / "github_events_date_suggestions.yaml"
    sugg_doc = {
        "source": "ejeej/EventsStockPrices",
        "note": "Review before apply; only for inferred/legacy announcement dates",
        "suggestions": suggestions,
    }
    sugg_path.write_text(yaml.safe_dump(sugg_doc, sort_keys=False), encoding="utf-8")

    status_counts = validation["match_status"].value_counts().to_dict()
    inferred = validation[validation["announcement_source"].isin(
        ["INFERRED_T0_PLUS_18MO", "INFERRED_CTGOV_RESULTS", "LEGACY_UNTAGGED"]
    )]
    inferred_matched = inferred[inferred["match_status"] != "NO_MATCH"]

    lines = [
        "# GitHub Events Validation Report",
        "",
        f"Source: [ejeej/EventsStockPrices](https://github.com/ejeej/EventsStockPrices)",
        "",
        "## Registry date validation (112 catalysts)",
        "",
        f"- Matched to GitHub clinical event: **{len(validation) - status_counts.get('NO_MATCH', 0)}** / **{len(validation)}**",
        "",
        "### Match quality",
        "",
    ]
    for status, n in sorted(status_counts.items(), key=lambda x: -x[1]):
        lines.append(f"- {status}: {n}")

    lines.extend(
        [
            "",
            "## Inferred/legacy sources with GitHub match",
            "",
            f"- Count: {len(inferred_matched)}",
            f"- Suggested date corrections (≥30d drift, drug_score≥0.7): **{len(suggestions)}**",
            "",
            f"Suggestions file: `{sugg_path.relative_to(project_root())}`",
            "",
            "## Cohort expansion candidates",
            "",
            f"- New Phase 2/3 events (2010–2020, not in registry): **{len(candidates)}**",
            f"- CSV: `{cand_csv.relative_to(project_root())}`",
            f"- YAML: `{yaml_path.relative_to(project_root())}`",
            "",
            "## Largest date drifts (matched, |delta| ≥ 90 days)",
            "",
        ]
    )

    drift = validation[validation["match_status"].isin(["MODERATE_DRIFT", "LARGE_DRIFT"])].copy()
    drift["abs_delta"] = drift["date_delta_days"].abs()
    drift = drift.sort_values("abs_delta", ascending=False).head(20)
    if not drift.empty:
        lines.append(drift[
            ["catalyst_id", "ticker", "drug_name", "registry_date", "github_date",
             "date_delta_days", "match_status", "announcement_source"]
        ].to_string(index=False))
    else:
        lines.append("_None_")

    lines.extend(["", "## Sample new candidates (first 15)", ""])
    if not candidates.empty:
        lines.append(candidates.head(15).to_string(index=False))
    else:
        lines.append("_None_")

    report_path = project_root() / "reports" / "github_events_validation.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")

    summary = {
        "validation_csv": str(out_csv),
        "candidates_csv": str(cand_csv),
        "candidates_yaml": str(yaml_path),
        "suggestions_yaml": str(sugg_path),
        "match_status": status_counts,
        "n_suggestions": len(suggestions),
        "n_candidates": len(candidates),
    }
    (project_root() / "data" / "processed" / "github_events_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    return report_path
