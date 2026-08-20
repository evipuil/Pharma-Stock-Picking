"""Expand catalyst calendar toward Phase A target (N≥100)."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import date
from pathlib import Path

import yaml

from src.clinical_trials.ctgov_client import ClinicalTrialsGovClient
from src.clinical_trials.parse_study import infer_outcome_labels, infer_t0, parse_study
from src.config import project_root
from src.db.load_program import insert_program_bundle
from src.event_study.windows import infer_trading_cutoff
from src.literature.pubmed_client import PubMedClient
from src.pipeline.batch_expand_cohort import _auto_extract_studies, _existing_programs
from src.pipeline.wave1_curation import DRUG_ALT_NAMES, _pick_phase2_study
from src.catalysts.migrate_from_programs import apply_catalyst_schema, migrate_programs_to_catalysts

ROOT = project_root()
DB_PATH = ROOT / "data" / "processed" / "research.db"
CONFIG = ROOT / "configs" / "catalyst_candidates.yaml"
RAW_CTGOV = ROOT / "data" / "raw" / "ctgov"


def _insert_catalyst_from_program(
    conn: sqlite3.Connection,
    program_id: str,
    cand: dict,
    nct_id: str,
    ann_date: date | None,
) -> bool:
    existing = conn.execute(
        "SELECT catalyst_id FROM catalysts WHERE program_id = ?", (program_id,)
    ).fetchone()
    if existing:
        return False

    row = conn.execute(
        """
        SELECT p.company_id, p.drug_name, p.indication, c.ticker,
               o.clinical_success, o.met_primary_endpoint, o.technical_failure,
               o.safety_failure, o.outcome_unknown, COALESCE(pf.n_animal_studies, 0)
        FROM programs p
        JOIN companies c ON p.company_id = c.company_id
        JOIN trial_outcomes o ON p.program_id = o.program_id AND o.outcome_level = 'PHASE2'
        LEFT JOIN program_preclinical_features pf ON p.program_id = pf.program_id
        WHERE p.program_id = ?
        """,
        (program_id,),
    ).fetchone()
    if not row:
        return False

    (
        company_id, drug, indication, ticker, success, met_pe,
        tech, safety, unknown, n_preclin,
    ) = row
    catalyst_id = f"CAT-{program_id}"
    ann = ann_date
    if not ann:
        od = conn.execute(
            "SELECT outcome_date FROM trial_outcomes WHERE program_id = ? AND outcome_level='PHASE2'",
            (program_id,),
        ).fetchone()
        if od and od[0]:
            ann = date.fromisoformat(str(od[0])[:10])

    cutoff, day_before, day_after, conf = (
        infer_trading_cutoff(ann, cand.get("announcement_timing", "UNKNOWN"))
        if ann
        else (None, None, None, "LOW")
    )

    if success and not tech and not safety:
        cat = "SUCCESS"
    elif safety:
        cat = "SAFETY_FAILURE"
    elif tech or not success:
        cat = "EFFICACY_FAILURE"
    else:
        cat = "MIXED"

    conn.execute(
        """
        INSERT INTO catalysts (
            catalyst_id, program_id, company_id, drug_name, indication, nct_id,
            catalyst_type, announcement_date, announcement_timing,
            trading_cutoff_date, trading_day_before, first_trading_day_after,
            clinical_success, outcome_category, met_primary_endpoint,
            preclinical_evidence_found, n_preclinical_publications,
            publication_coverage_confidence, data_source, cohort_phase
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            catalyst_id,
            program_id,
            company_id,
            drug,
            indication,
            nct_id,
            cand.get("catalyst_type", "PHASE2_READOUT"),
            str(ann)[:10] if ann else None,
            cand.get("announcement_timing", "UNKNOWN"),
            str(cutoff)[:10] if cutoff else None,
            str(day_before)[:10] if day_before else None,
            str(day_after)[:10] if day_after else None,
            success,
            cat,
            met_pe,
            1 if n_preclin else 0,
            n_preclin,
            1.0 if n_preclin else 0.0,
            "expand_catalyst_v1",
            cand.get("cohort_phase", "phase_a"),
        ),
    )
    conn.execute(
        """
        INSERT OR IGNORE INTO catalyst_ticker_history (
            map_id, catalyst_id, ticker_at_event, ticker_current, map_source
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (str(uuid.uuid4()), catalyst_id, ticker, ticker, "expand_catalyst"),
    )
    if cutoff:
        conn.execute(
            """
            INSERT OR IGNORE INTO catalyst_trading_cutoffs (
                catalyst_id, entry_cutoff_date, execution_confidence
            ) VALUES (?, ?, ?)
            """,
            (catalyst_id, str(cutoff)[:10], conf),
        )
    return True


def expand_catalyst_cohort(max_new: int | None = None) -> dict:
    apply_catalyst_schema(DB_PATH)
    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    ctgov = ClinicalTrialsGovClient()
    pubmed = PubMedClient()
    conn = sqlite3.connect(DB_PATH)
    existing = _existing_programs(conn)
    existing_cats = {
        r[0]
        for r in conn.execute("SELECT catalyst_id FROM catalysts").fetchall()
    }

    stats = {"programs_loaded": 0, "catalysts_created": 0, "skipped": 0, "errors": []}

    try:
        for cand in cfg.get("candidates", []):
            if cand.get("skip"):
                stats["skipped"] += 1
                continue
            pid = cand["id"]
            cat_id = f"CAT-{pid}"
            if cat_id in existing_cats:
                stats["skipped"] += 1
                continue
            if max_new is not None and stats["catalysts_created"] >= max_new:
                break

            try:
                # Load program if missing
                if pid not in existing:
                    if cand.get("nct_id"):
                        nct_id = cand["nct_id"]
                        raw_path = ctgov.fetch_and_cache(nct_id, RAW_CTGOV)
                        raw = json.loads(raw_path.read_text(encoding="utf-8"))
                    else:
                        query = cand.get("search") or f"{cand['drug_name']} {cand['indication']}"
                        studies = ctgov.search_studies(query, phase="PHASE2", page_size=25)
                        picked = _pick_phase2_study(studies, cand["drug_name"], cand["indication"])
                        if not picked:
                            stats["errors"].append(f"{pid}: no Phase II found")
                            continue
                        nct_id = picked["protocolSection"]["identificationModule"]["nctId"]
                        raw_path = RAW_CTGOV / f"{nct_id}.json"
                        raw_path.write_text(json.dumps(picked, indent=2), encoding="utf-8")
                        raw = picked

                    parsed = parse_study(raw)
                    t0_date, t0_def = infer_t0(parsed)
                    if t0_date and (t0_date.year < 2010 or t0_date.year > 2020):
                        stats["errors"].append(f"{pid}: t0 {t0_date} outside window")
                        continue

                    outcome = infer_outcome_labels(parsed)
                    if cand.get("outcome_override"):
                        outcome.update(
                            {k: v for k, v in cand["outcome_override"].items() if k != "notes"}
                        )

                    max_pub = t0_date.strftime("%Y/%m/%d") if t0_date else "2020/12/31"
                    alt = DRUG_ALT_NAMES.get(cand["drug_name"], [])
                    publications = pubmed.search_animal_literature(
                        cand["drug_name"], max_date=max_pub, alt_names=alt, retmax=10
                    )

                    bundle = {
                        "program_id": pid,
                        "candidate_id": pid,
                        "ticker": cand["ticker"],
                        "company_name": cand["company_name"],
                        "drug_name": cand["drug_name"],
                        "indication": cand["indication"],
                        "modality": cand.get("modality", "small_molecule"),
                        "primary_nct_id": nct_id,
                        "mvp_wave": cand.get("mvp_wave", "wave_2"),
                        "brief_title": parsed.get("brief_title"),
                        "t0_date": t0_date,
                        "t0_definition": t0_def,
                        "t0_rationale": f"catalyst expand {nct_id}",
                        "trial": parsed,
                        "outcome": outcome,
                        "publications": publications[:5],
                        "raw_json_path": str(raw_path.relative_to(ROOT)),
                        "financial_event": cand.get("financial_event"),
                    }
                    insert_program_bundle(conn, bundle)
                    _auto_extract_studies(conn, pid, cand["drug_name"], t0_date, publications)
                    conn.commit()
                    existing.add(pid)
                    stats["programs_loaded"] += 1
                else:
                    nct_id = cand.get("nct_id") or conn.execute(
                        "SELECT primary_nct_id FROM programs WHERE program_id = ?", (pid,)
                    ).fetchone()[0]

                ann = None
                if cand.get("announcement_date"):
                    ann = date.fromisoformat(cand["announcement_date"])
                elif cand.get("financial_event", {}).get("event_date"):
                    ann = date.fromisoformat(cand["financial_event"]["event_date"])

                if _insert_catalyst_from_program(conn, pid, cand, nct_id, ann):
                    stats["catalysts_created"] += 1
                    existing_cats.add(f"CAT-{pid}")
                    conn.commit()
                    print(f"OK catalyst CAT-{pid} {cand['drug_name']}")
            except Exception as exc:
                stats["errors"].append(f"{pid}: {exc}")
                print(f"ERR {pid}: {exc}")
    finally:
        conn.close()

    # Ensure all programs have catalyst rows
    mig = migrate_programs_to_catalysts(DB_PATH)
    stats["migration"] = mig
    stats["total_catalysts"] = sqlite3.connect(DB_PATH).execute(
        "SELECT COUNT(*) FROM catalysts"
    ).fetchone()[0]

    report = ROOT / "data" / "interim" / "catalyst_expand_report.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(stats, indent=2), encoding="utf-8")
    return stats
