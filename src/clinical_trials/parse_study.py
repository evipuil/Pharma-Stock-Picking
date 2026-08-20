"""Parse ClinicalTrials.gov API v2 study JSON into pipeline fields."""

from __future__ import annotations

from datetime import date
from typing import Any


def _get(d: dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(key, default)
    return d


def _parse_ctgov_date(value: str | None) -> date | None:
    if not value:
        return None
    # Formats: "2015-03-01" or "2015-03" or "2015"
    parts = value.split("-")
    try:
        y = int(parts[0])
        m = int(parts[1]) if len(parts) > 1 else 1
        d = int(parts[2]) if len(parts) > 2 else 1
        return date(y, m, d)
    except (ValueError, IndexError):
        return None


def parse_study(raw: dict[str, Any]) -> dict[str, Any]:
    """Extract structured fields from CT.gov v2 study payload."""
    ps = raw.get("protocolSection", {})
    id_mod = ps.get("identificationModule", {})
    status_mod = ps.get("statusModule", {})
    design_mod = ps.get("designModule", {})
    cond_mod = ps.get("conditionsModule", {})
    arms_mod = ps.get("armsInterventionsModule", {})
    sponsor_mod = ps.get("sponsorCollaboratorsModule", {})
    outcomes_mod = ps.get("outcomesModule", {})
    results_mod = raw.get("resultsSection") or {}

    phases = design_mod.get("phases") or []
    phase = phases[0] if phases else "UNKNOWN"

    interventions = arms_mod.get("interventions") or []
    intervention_names = [i.get("name", "") for i in interventions]

    start_date = _parse_ctgov_date(status_mod.get("startDateStruct", {}).get("date"))
    primary_completion = _parse_ctgov_date(
        status_mod.get("primaryCompletionDateStruct", {}).get("date")
    )
    completion = _parse_ctgov_date(status_mod.get("completionDateStruct", {}).get("date"))
    first_posted = _parse_ctgov_date(status_mod.get("studyFirstPostDateStruct", {}).get("date"))
    results_posted = _parse_ctgov_date(
        status_mod.get("resultsFirstPostDateStruct", {}).get("date")
    )

    overall_status = status_mod.get("overallStatus", "")

    primary_outcomes = outcomes_mod.get("primaryOutcomes") or []
    primary_outcome_measures = [o.get("measure", "") for o in primary_outcomes]

    # Results section parsing (when available)
    results_outcomes = _get(results_mod, "outcomeMeasuresModule", "outcomeMeasures") or []
    primary_met: bool | None = None
    for om in results_outcomes:
        if om.get("type") == "PRIMARY":
            analyses = om.get("analyses") or []
            for a in analyses:
                p_val = a.get("pValue")
                if p_val and p_val != "NA":
                    try:
                        primary_met = float(str(p_val).replace("<", "").replace(">", "")) < 0.05
                    except ValueError:
                        pass

    why_stopped = status_mod.get("whyStopped")

    return {
        "nct_id": id_mod.get("nctId"),
        "brief_title": id_mod.get("briefTitle"),
        "phase": phase,
        "conditions": cond_mod.get("conditions") or [],
        "interventions": intervention_names,
        "sponsor": _get(sponsor_mod, "leadSponsor", "name"),
        "overall_status": overall_status,
        "why_stopped": why_stopped,
        "start_date": start_date,
        "primary_completion_date": primary_completion,
        "study_completion_date": completion,
        "first_posted_date": first_posted,
        "results_first_posted_date": results_posted,
        "enrollment": _get(design_mod, "enrollmentInfo", "count"),
        "allocation": _get(design_mod, "designInfo", "allocation"),
        "masking": _get(design_mod, "designInfo", "maskingInfo", "masking"),
        "primary_outcomes": primary_outcome_measures,
        "primary_endpoint_met_inferred": primary_met,
        "raw": raw,
    }


def infer_t0(parsed: dict[str, Any]) -> tuple[date | None, str]:
    """Use trial start date as t0 proxy when FPI unavailable."""
    start = parsed.get("start_date")
    if start:
        return start, "TRIAL_START"
    return parsed.get("first_posted_date"), "OTHER"


def infer_outcome_labels(parsed: dict[str, Any]) -> dict[str, int | None]:
    """
    Heuristic outcome labeling from CT.gov status + results.
    Requires manual adjudication for production; sufficient for MVP pipeline demo.
    """
    status = (parsed.get("overall_status") or "").upper()
    why = (parsed.get("why_stopped") or "").lower()
    phase = parsed.get("phase", "")
    primary_met = parsed.get("primary_endpoint_met_inferred")

    technical_failure = 0
    safety_failure = 0
    commercial_discontinuation = 0
    outcome_unknown = 0
    clinical_success: int | None = None
    met_primary: int | None = None
    advanced_p3: int | None = None

    if primary_met is True:
        met_primary = 1
    elif primary_met is False:
        met_primary = 0

    if status in ("COMPLETED", "ACTIVE_NOT_RECRUITING", "RECRUITING", "ENROLLING_BY_INVITATION"):
        if met_primary == 1:
            clinical_success = 1
        elif met_primary == 0:
            clinical_success = 0
            technical_failure = 1
        else:
            outcome_unknown = 1

    elif status == "TERMINATED":
        if any(w in why for w in ("safety", "toxic", "adverse", "death")):
            clinical_success = 0
            safety_failure = 1
        elif any(w in why for w in ("efficacy", "futility", "lack of", "failed")):
            clinical_success = 0
            technical_failure = 1
        elif any(w in why for w in ("business", "strategic", "sponsor", "commercial")):
            clinical_success = 0
            commercial_discontinuation = 1
        else:
            clinical_success = 0
            outcome_unknown = 1

    elif status in ("WITHDRAWN", "SUSPENDED"):
        clinical_success = 0
        outcome_unknown = 1

    # Phase III existence heuristic deferred — set NULL
    return {
        "clinical_success": clinical_success,
        "met_primary_endpoint": met_primary,
        "advanced_to_phase3": advanced_p3,
        "technical_failure": technical_failure,
        "safety_failure": safety_failure,
        "commercial_discontinuation": commercial_discontinuation,
        "outcome_unknown": outcome_unknown,
    }
