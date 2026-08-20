"""Add Wave 2 failure programs for trainable classification."""

from __future__ import annotations

import json
import sqlite3
import uuid
from pathlib import Path

from src.clinical_trials.ctgov_client import ClinicalTrialsGovClient
from src.clinical_trials.parse_study import infer_t0, parse_study
from src.config import project_root
from src.db.load_program import insert_program_bundle
from src.literature.pubmed_client import PubMedClient
from src.pipeline.wave1_curation import DRUG_ALT_NAMES
from src.preclinical.apply_extractions import apply_extractions

ROOT = project_root()
DB_PATH = ROOT / "data" / "processed" / "research.db"
RAW_CTGOV = ROOT / "data" / "raw" / "ctgov"

# Phase II failures / negative readouts — NCT IDs verified on CT.gov
FAILURE_PROGRAMS = [
    {
        "program_id": "F001",
        "candidate_id": "F001",
        "ticker": "INCY",
        "company_name": "Incyte Corporation",
        "drug_name": "epacadostat",
        "indication": "head_and_neck_cancer",
        "modality": "small_molecule",
        "primary_nct_id": "NCT03463161",
        "mvp_wave": "wave_2",
        "outcome": {
            "clinical_success": 0,
            "met_primary_endpoint": 0,
            "advanced_to_phase3": 0,
            "technical_failure": 1,
            "safety_failure": 0,
            "commercial_discontinuation": 0,
            "outcome_unknown": 0,
            "notes": "Phase II HNSCC combo terminated early",
        },
    },
    {
        "program_id": "F002",
        "candidate_id": "F002",
        "ticker": "INCY",
        "company_name": "Incyte Corporation",
        "drug_name": "epacadostat",
        "indication": "melanoma",
        "modality": "small_molecule",
        "primary_nct_id": "NCT02752074",
        "mvp_wave": "wave_2",
        "outcome": {
            "clinical_success": 0,
            "met_primary_endpoint": 0,
            "advanced_to_phase3": 0,
            "technical_failure": 1,
            "safety_failure": 0,
            "commercial_discontinuation": 0,
            "outcome_unknown": 0,
            "notes": "ECHO-301 Phase III failed primary PFS vs pembrolizumab alone",
        },
    },
    {
        "program_id": "F003",
        "candidate_id": "F003",
        "ticker": "AVEO",
        "company_name": "AVEO Pharmaceuticals",
        "drug_name": "tivozanib",
        "indication": "RCC",
        "modality": "small_molecule",
        "primary_nct_id": "NCT01030783",
        "mvp_wave": "wave_2",
        "outcome": {
            "clinical_success": 0,
            "met_primary_endpoint": 0,
            "advanced_to_phase3": 0,
            "technical_failure": 1,
            "safety_failure": 0,
            "commercial_discontinuation": 0,
            "outcome_unknown": 0,
            "notes": "TIVO-1 Phase III failed primary PFS vs sorafenib",
        },
    },
    {
        "program_id": "F004",
        "candidate_id": "F004",
        "ticker": "CLVS",
        "company_name": "Clovis Oncology",
        "drug_name": "rucaparib",
        "indication": "prostate_cancer",
        "modality": "small_molecule",
        "primary_nct_id": "NCT03442556",
        "mvp_wave": "wave_2",
        "outcome": {
            "clinical_success": 0,
            "met_primary_endpoint": 0,
            "advanced_to_phase3": 0,
            "technical_failure": 1,
            "safety_failure": 0,
            "commercial_discontinuation": 0,
            "outcome_unknown": 0,
            "notes": "TRITON3 Phase III rucaparib vs physician's choice in BRCA-mutant mCRPC — failed primary",
        },
    },
]


def load_failures() -> None:
    ctgov = ClinicalTrialsGovClient()
    pubmed = PubMedClient()
    conn = sqlite3.connect(DB_PATH)

    try:
        for spec in FAILURE_PROGRAMS:
            nct = spec["primary_nct_id"]
            raw_path = ctgov.fetch_and_cache(nct, RAW_CTGOV)
            raw = json.loads(raw_path.read_text(encoding="utf-8"))
            parsed = parse_study(raw)
            t0_date, t0_def = infer_t0(parsed)

            max_pub = t0_date.strftime("%Y/%m/%d") if t0_date else "2020/12/31"
            alt = DRUG_ALT_NAMES.get(spec["drug_name"], [])
            publications = pubmed.search_animal_literature(
                spec["drug_name"], max_date=max_pub, alt_names=alt, retmax=10
            )
            if t0_date:
                from datetime import date

                publications = [
                    p
                    for p in publications
                    if p.get("publication_date")
                    and date.fromisoformat(p["publication_date"][:10]) <= t0_date
                ]

            bundle = {
                **spec,
                "t0_date": t0_date,
                "t0_definition": t0_def,
                "t0_rationale": f"CT.gov start for {nct}",
                "brief_title": parsed.get("brief_title"),
                "trial": parsed,
                "publications": publications[:5],
                "raw_json_path": str(raw_path.relative_to(ROOT)),
                "financial_event": None,
            }
            insert_program_bundle(conn, bundle)
            print(f"Loaded {spec['program_id']}: {spec['drug_name']} success={spec['outcome']['clinical_success']}")
        conn.commit()
    finally:
        conn.close()

    # Re-apply manual extractions for shared drugs (epacadostat, tivozanib, rucaparib)
    apply_extractions(DB_PATH)


if __name__ == "__main__":
    load_failures()
