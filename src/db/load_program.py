"""Load curated program data into SQLite."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import date
from pathlib import Path
from typing import Any


def _id() -> str:
    return str(uuid.uuid4())


def upsert_company(conn: sqlite3.Connection, ticker: str, name: str) -> str:
    row = conn.execute("SELECT company_id FROM companies WHERE ticker = ?", (ticker,)).fetchone()
    if row:
        return row[0]
    company_id = _id()
    conn.execute(
        """
        INSERT INTO companies (company_id, ticker, company_name, is_biotech_sponsor)
        VALUES (?, ?, ?, 1)
        """,
        (company_id, ticker, name),
    )
    return company_id


def insert_program_bundle(conn: sqlite3.Connection, bundle: dict[str, Any]) -> str:
    """Insert company, program, t0, trial, outcome, publications, animal studies."""
    company_id = upsert_company(conn, bundle["ticker"], bundle["company_name"])
    program_id = bundle.get("program_id") or _id()

    conn.execute(
        """
        INSERT OR REPLACE INTO programs (
            program_id, company_id, drug_name, indication, modality, target,
            biomarker_strategy, development_stage_at_t0, primary_nct_id, mvp_wave, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'PHASE2', ?, ?, ?)
        """,
        (
            program_id,
            company_id,
            bundle["drug_name"],
            bundle["indication"],
            bundle.get("modality"),
            bundle.get("target"),
            bundle.get("biomarker_strategy"),
            bundle["primary_nct_id"],
            bundle.get("mvp_wave", "wave_1"),
            bundle.get("notes"),
        ),
    )

    t0 = bundle["t0_date"]
    if isinstance(t0, date):
        t0_str = t0.isoformat()
    else:
        t0_str = str(t0)

    src_id = _id()
    conn.execute(
        """
        INSERT INTO source_records (source_record_id, source_type, source_identifier, url, title)
        VALUES (?, 'CTGOV', ?, ?, ?)
        """,
        (src_id, bundle["primary_nct_id"], f"https://clinicaltrials.gov/study/{bundle['primary_nct_id']}", bundle.get("brief_title")),
    )

    conn.execute(
        """
        INSERT OR REPLACE INTO program_t0 (
            program_id, t0_date, t0_definition, t0_source_type, t0_source_record_id, t0_rationale
        ) VALUES (?, ?, ?, 'CTGOV', ?, ?)
        """,
        (program_id, t0_str, bundle.get("t0_definition", "TRIAL_START"), src_id, bundle.get("t0_rationale")),
    )

    trial = bundle["trial"]
    conn.execute(
        """
        INSERT OR REPLACE INTO clinical_trials (
            nct_id, program_id, brief_title, phase, condition, intervention, sponsor,
            start_date, primary_completion_date, study_completion_date,
            first_posted_date, results_first_posted_date, enrollment, allocation, masking,
            api_fetched_at, raw_json_path
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?)
        """,
        (
            bundle["primary_nct_id"],
            program_id,
            trial.get("brief_title"),
            trial.get("phase"),
            json.dumps(trial.get("conditions")),
            json.dumps(trial.get("interventions")),
            trial.get("sponsor"),
            _d(trial.get("start_date")),
            _d(trial.get("primary_completion_date")),
            _d(trial.get("study_completion_date")),
            _d(trial.get("first_posted_date")),
            _d(trial.get("results_first_posted_date")),
            trial.get("enrollment"),
            trial.get("allocation"),
            trial.get("masking"),
            bundle.get("raw_json_path"),
        ),
    )

    outcome = bundle["outcome"]
    conn.execute(
        """
        INSERT OR REPLACE INTO trial_outcomes (
            outcome_id, program_id, nct_id, outcome_level, clinical_success,
            met_primary_endpoint, advanced_to_phase3, technical_failure, safety_failure,
            commercial_discontinuation, outcome_unknown, failure_reason_detail,
            outcome_date, labeling_rule_version, notes
        ) VALUES (?, ?, ?, 'PHASE2', ?, ?, ?, ?, ?, ?, ?, ?, ?, 'v1.0', ?)
        """,
        (
            _id(),
            program_id,
            bundle["primary_nct_id"],
            outcome.get("clinical_success"),
            outcome.get("met_primary_endpoint"),
            outcome.get("advanced_to_phase3"),
            outcome.get("technical_failure"),
            outcome.get("safety_failure"),
            outcome.get("commercial_discontinuation"),
            outcome.get("outcome_unknown"),
            outcome.get("failure_reason_detail"),
            outcome.get("outcome_date"),
            outcome.get("notes"),
        ),
    )

    n_studies = 0
    for pub in bundle.get("publications") or []:
        pub_id = _id()
        src_id = _id()
        conn.execute(
            """
            INSERT INTO source_records (
                source_record_id, source_type, source_identifier, url, title,
                publication_date, is_peer_reviewed
            ) VALUES (?, 'PUBMED', ?, ?, ?, ?, 1)
            """,
            (
                src_id,
                pub.get("pmid"),
                f"https://pubmed.ncbi.nlm.nih.gov/{pub.get('pmid')}/",
                pub.get("title"),
                pub.get("publication_date"),
            ),
        )
        conn.execute(
            """
            INSERT INTO publications (publication_id, source_record_id, pmid, doi, abstract, study_type_inferred)
            VALUES (?, ?, ?, ?, ?, 'ANIMAL_EFFICACY')
            """,
            (pub_id, src_id, pub.get("pmid"), pub.get("doi"), pub.get("abstract")),
        )
        conn.execute(
            """
            INSERT INTO publication_program_links (link_id, publication_id, program_id, relevance, linked_by)
            VALUES (?, ?, ?, 'PRIMARY_EFFICACY', 'auto')
            """,
            (_id(), pub_id, program_id),
        )

        # Create placeholder animal study row per publication (MVP — manual feature extraction later)
        study_id = _id()
        conn.execute(
            """
            INSERT INTO animal_studies (
                study_id, program_id, publication_id, drug_name, extracted_by,
                extraction_confidence, verification_status
            ) VALUES (?, ?, ?, ?, 'nlp', 0.3, 'pending')
            """,
            (study_id, program_id, pub_id, bundle["drug_name"]),
        )
        conn.execute(
            """
            INSERT INTO animal_study_features (study_id, peer_reviewed, feature_extraction_method)
            VALUES (?, 1, 'pubmed_metadata_only')
            """,
            (study_id,),
        )
        n_studies += 1

    conn.execute(
        """
        INSERT OR REPLACE INTO program_preclinical_features (
            program_id, n_animal_studies, aggregation_rule_version
        ) VALUES (?, ?, 'v1.0_mvp_auto')
        """,
        (program_id, n_studies),
    )

    if bundle.get("financial_event"):
        ev = bundle["financial_event"]
        conn.execute(
            """
            INSERT OR REPLACE INTO program_financial_events (
                event_id, program_id, event_type, event_date, event_date_source, outcome_direction
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (_id(), program_id, ev.get("event_type", "PHASE2_READOUT"), ev["event_date"], ev.get("source"), ev.get("direction")),
        )

    return program_id


def _d(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value.isoformat()
    return str(value)[:10]
