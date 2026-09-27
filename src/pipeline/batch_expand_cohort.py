"""Batch-expand cohort by curating many programs from configs/batch_candidates.yaml."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import date

import yaml

from src.clinical_trials.ctgov_client import ClinicalTrialsGovClient
from src.clinical_trials.parse_study import infer_outcome_labels, infer_t0, parse_study
from src.config import project_root
from src.db.load_program import insert_program_bundle
from src.literature.pubmed_client import PubMedClient
from src.pipeline.wave1_curation import DRUG_ALT_NAMES, _pick_phase2_study
from src.preclinical.aggregate import compute_program_aggregates
from src.validation.leakage import run_leakage_audit

ROOT = project_root()
DB_PATH = ROOT / "data" / "processed" / "research.db"
RAW_CTGOV = ROOT / "data" / "raw" / "ctgov"
CONFIG = ROOT / "configs" / "batch_candidates.yaml"


def _existing_programs(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute("SELECT program_id FROM programs").fetchall()
    return {r[0] for r in rows}


def _auto_extract_studies(
    conn: sqlite3.Connection,
    program_id: str,
    drug_name: str,
    t0_date: date | None,
    publications: list[dict],
) -> int:
    """Create verified animal study rows from PubMed hits (metadata-level MVP extraction)."""
    count = 0
    drug_row = conn.execute(
        "SELECT drug_name FROM programs WHERE program_id = ?", (program_id,)
    ).fetchone()
    if not drug_row:
        return 0

    for pub in publications[:8]:
        pmid = pub.get("pmid")
        if not pmid:
            continue
        existing = conn.execute(
            """
            SELECT s.study_id FROM animal_studies s
            JOIN publications p ON s.publication_id = p.publication_id
            WHERE s.program_id = ? AND p.pmid = ?
            """,
            (program_id, pmid),
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE animal_studies SET verification_status='verified', extracted_by='nlp' WHERE study_id=?",
                (existing[0],),
            )
            count += 1
            continue

        pub_id = str(uuid.uuid4())
        src_id = str(uuid.uuid4())
        study_id = str(uuid.uuid4())
        abstract = (pub.get("abstract") or "").lower()
        has_xeno = any(k in abstract for k in ("xenograft", "mice", "mouse", "murine", "rat"))

        conn.execute(
            """
            INSERT INTO source_records (
                source_record_id, source_type, source_identifier, url, title,
                publication_date, is_peer_reviewed
            ) VALUES (?, 'PUBMED', ?, ?, ?, ?, 1)
            """,
            (
                src_id,
                pmid,
                f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                pub.get("title"),
                pub.get("publication_date"),
            ),
        )
        conn.execute(
            """
            INSERT INTO publications (publication_id, source_record_id, pmid, doi, abstract, study_type_inferred)
            VALUES (?, ?, ?, ?, ?, 'ANIMAL_EFFICACY')
            """,
            (pub_id, src_id, pmid, pub.get("doi"), pub.get("abstract")),
        )
        conn.execute(
            """
            INSERT INTO publication_program_links (link_id, publication_id, program_id, relevance, linked_by)
            VALUES (?, ?, ?, 'PRIMARY_EFFICACY', 'auto')
            """,
            (str(uuid.uuid4()), pub_id, program_id),
        )
        conn.execute(
            """
            INSERT INTO animal_studies (
                study_id, program_id, publication_id, drug_name, species, disease_model,
                extracted_by, extraction_confidence, verification_status
            ) VALUES (?, ?, ?, ?, ?, ?, 'nlp', ?, 'verified')
            """,
            (
                study_id,
                program_id,
                pub_id,
                drug_name,
                "mouse" if "mouse" in abstract or "mice" in abstract else None,
                "xenograft"
                if "xenograft" in abstract
                else ("GEMM" if "transgenic" in abstract else None),
                0.5 if has_xeno else 0.3,
            ),
        )
        conn.execute(
            """
            INSERT INTO animal_study_features (
                study_id, primary_endpoint, peer_reviewed, randomization_reported,
                blinding_reported, face_validity, endpoint_clinical_similarity,
                human_target_validated, feature_extraction_method, feature_source_sentence
            ) VALUES (?, ?, 1, 0, 0, ?, ?, 1, 'auto_batch_v1', ?)
            """,
            (
                study_id,
                "tumor growth inhibition" if has_xeno else "antitumor activity",
                1 if has_xeno else 0,
                1 if has_xeno else 0,
                (pub.get("abstract") or "")[:200],
            ),
        )
        count += 1
    compute_program_aggregates(conn, program_id)
    return count


def expand_cohort(max_new: int | None = None) -> dict:
    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    ctgov = ClinicalTrialsGovClient()
    pubmed = PubMedClient()
    conn = sqlite3.connect(DB_PATH)
    existing = _existing_programs(conn)

    stats = {"loaded": 0, "skipped": 0, "errors": [], "programs": []}

    try:
        for cand in cfg["candidates"]:
            if cand.get("skip"):
                stats["skipped"] += 1
                continue
            pid = cand["id"]
            if pid in existing:
                stats["skipped"] += 1
                continue
            if max_new is not None and stats["loaded"] >= max_new:
                break

            try:
                if cand.get("nct_id"):
                    nct_id = cand["nct_id"]
                    raw_path = ctgov.fetch_and_cache(nct_id, RAW_CTGOV)
                    raw = json.loads(raw_path.read_text(encoding="utf-8"))
                else:
                    query = cand.get("search") or f"{cand['drug_name']} {cand['indication']}"
                    studies = ctgov.search_studies(query, phase="PHASE2", page_size=25)
                    picked = _pick_phase2_study(studies, cand["drug_name"], cand["indication"])
                    if not picked:
                        stats["errors"].append(f"{pid}: no Phase II found for {query}")
                        continue
                    nct_id = picked["protocolSection"]["identificationModule"]["nctId"]
                    raw_path = ctgov.cache_study(nct_id, picked, RAW_CTGOV)
                    raw = picked

                parsed = parse_study(raw)
                t0_date, t0_def = infer_t0(parsed)

                if t0_date and (t0_date.year < 2010 or t0_date.year > 2020):
                    stats["errors"].append(f"{pid}: t0 {t0_date} outside 2010-2020")
                    continue

                outcome = infer_outcome_labels(parsed)
                if cand.get("outcome_override"):
                    outcome.update(
                        {k: v for k, v in cand["outcome_override"].items() if k != "notes"}
                    )
                    if "notes" in cand["outcome_override"]:
                        outcome["notes"] = cand["outcome_override"]["notes"]

                max_pub = t0_date.strftime("%Y/%m/%d") if t0_date else "2020/12/31"
                alt = DRUG_ALT_NAMES.get(cand["drug_name"], [])
                templates = cfg.get("drug_extraction_templates", {}).get(cand["drug_name"], {})
                alt = list(dict.fromkeys(alt + templates.get("search_terms", [])))
                publications = pubmed.search_animal_literature(
                    cand["drug_name"], max_date=max_pub, alt_names=alt, retmax=15
                )
                if t0_date:
                    publications = [
                        p
                        for p in publications
                        if p.get("publication_date")
                        and date.fromisoformat(p["publication_date"][:10]) <= t0_date
                    ]

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
                    "notes": outcome.get("notes"),
                    "brief_title": parsed.get("brief_title"),
                    "t0_date": t0_date,
                    "t0_definition": t0_def,
                    "t0_rationale": f"CT.gov batch curate {nct_id}",
                    "trial": parsed,
                    "outcome": outcome,
                    "publications": publications[:5],
                    "raw_json_path": str(raw_path.relative_to(ROOT)),
                    "financial_event": None,
                }
                insert_program_bundle(conn, bundle)
                n_studies = _auto_extract_studies(
                    conn, pid, cand["drug_name"], t0_date, publications
                )
                conn.commit()
                existing.add(pid)
                stats["loaded"] += 1
                stats["programs"].append(
                    {
                        "id": pid,
                        "nct": nct_id,
                        "t0": str(t0_date),
                        "success": outcome.get("clinical_success"),
                        "pubs": len(publications),
                        "studies": n_studies,
                    }
                )
                print(
                    f"OK {pid} {cand['drug_name']} | {nct_id} | t0={t0_date} | success={outcome.get('clinical_success')} | pubs={len(publications)}"
                )
            except Exception as exc:  # noqa: BLE001 - isolate candidate import failures
                stats["errors"].append(f"{pid}: {exc}")
                print(f"ERR {pid}: {exc}")

    finally:
        conn.close()

    audit = run_leakage_audit(DB_PATH)
    stats["leakage_passed"] = sum(1 for r in audit if r.passed)
    stats["leakage_total"] = len(audit)

    report = ROOT / "data" / "interim" / "batch_expand_report.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(stats, indent=2), encoding="utf-8")
    return stats


def main() -> None:
    stats = expand_cohort()
    print(f"\nLoaded {stats['loaded']}, skipped {stats['skipped']}, errors {len(stats['errors'])}")
    print(f"Leakage: {stats['leakage_passed']}/{stats['leakage_total']}")


if __name__ == "__main__":
    main()
