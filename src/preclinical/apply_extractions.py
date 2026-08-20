"""Apply manual feature extractions to the research database."""

from __future__ import annotations

import sqlite3
import uuid
from pathlib import Path
from typing import Any

import yaml

from src.config import project_root
from src.preclinical.aggregate import compute_program_aggregates

ROOT = project_root()
DB_PATH = ROOT / "data" / "processed" / "research.db"
EXTRACTIONS_PATH = ROOT / "configs" / "manual_extractions.yaml"


def _bool_int(val: bool | None) -> int | None:
    if val is None:
        return None
    return 1 if val else 0


def _get_pmid_for_study(conn: sqlite3.Connection, study_id: str) -> str | None:
    row = conn.execute(
        """
        SELECT pub.pmid FROM animal_studies s
        JOIN publications pub ON s.publication_id = pub.publication_id
        WHERE s.study_id = ?
        """,
        (study_id,),
    ).fetchone()
    return row[0] if row else None


def reject_study(conn: sqlite3.Connection, study_id: str, reason: str) -> None:
    conn.execute(
        "UPDATE animal_studies SET verification_status = 'rejected' WHERE study_id = ?",
        (study_id,),
    )
    conn.execute(
        """
        UPDATE animal_study_features SET feature_extraction_method = 'manual_rejected',
        feature_source_sentence = ? WHERE study_id = ?
        """,
        (reason, study_id),
    )


def add_publication_and_study(
    conn: sqlite3.Connection,
    program_id: str,
    drug_name: str,
    spec: dict[str, Any],
) -> str:
    pub_id = str(uuid.uuid4())
    src_id = str(uuid.uuid4())
    study_id = str(uuid.uuid4())

    conn.execute(
        """
        INSERT INTO source_records (
            source_record_id, source_type, source_identifier, url, title,
            publication_date, is_peer_reviewed, data_extraction_timestamp
        ) VALUES (?, 'PUBMED', ?, ?, ?, ?, 1, datetime('now'))
        """,
        (
            src_id,
            spec["pmid"],
            f"https://pubmed.ncbi.nlm.nih.gov/{spec['pmid']}/",
            spec.get("title"),
            spec.get("publication_date"),
        ),
    )
    conn.execute(
        """
        INSERT INTO publications (publication_id, source_record_id, pmid, doi, study_type_inferred)
        VALUES (?, ?, ?, ?, 'ANIMAL_EFFICACY')
        """,
        (pub_id, src_id, spec["pmid"], spec.get("doi")),
    )
    conn.execute(
        """
        INSERT INTO publication_program_links (link_id, publication_id, program_id, relevance, linked_by)
        VALUES (?, ?, ?, ?, 'manual')
        """,
        (str(uuid.uuid4()), pub_id, program_id, spec.get("relevance", "PRIMARY_EFFICACY")),
    )
    conn.execute(
        """
        INSERT INTO animal_studies (
            study_id, program_id, publication_id, drug_name, species, strain, sex, age,
            disease_model, model_induction_method, sample_size_treatment, sample_size_control,
            control_type, is_humanized_model, is_pdx, therapeutic_vs_prophylactic,
            extracted_by, extraction_confidence, verification_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'manual', ?, ?)
        """,
        (
            study_id,
            program_id,
            pub_id,
            drug_name,
            spec.get("species"),
            spec.get("strain"),
            spec.get("sex"),
            spec.get("age"),
            spec.get("disease_model"),
            spec.get("model_induction_method"),
            spec.get("sample_size_treatment"),
            spec.get("sample_size_control"),
            spec.get("control_type"),
            _bool_int(spec.get("is_humanized_model")),
            _bool_int(spec.get("is_pdx")),
            spec.get("therapeutic_vs_prophylactic"),
            spec.get("extraction_confidence", 0.9),
            spec.get("verification_status", "verified"),
        ),
    )
    apply_study_features(conn, study_id, spec)
    return study_id


def apply_study_features(conn: sqlite3.Connection, study_id: str, spec: dict[str, Any]) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO animal_study_features (
            study_id, primary_endpoint, effect_size, effect_size_type, pct_improvement, p_value,
            dose_response, survival_benefit,
            face_validity, construct_validity, predictive_validity,
            endpoint_clinical_similarity, mechanism_similarity, pkpd_relevance,
            biomarker_overlap, human_target_validated,
            randomization_reported, blinding_reported, allocation_concealment,
            sample_size_calculation, exclusions_described, preregistration, peer_reviewed,
            independent_lab_replication, replicated_across_models, replicated_across_species,
            feature_extraction_method, feature_source_sentence, feature_page_ref
        ) VALUES (
            ?, ?, ?, ?, ?, ?,
            ?, ?,
            ?, ?, ?,
            ?, ?, ?,
            ?, ?,
            ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?,
            'manual_v1', ?, ?
        )
        """,
        (
            study_id,
            spec.get("primary_endpoint"),
            spec.get("effect_size"),
            spec.get("effect_size_type"),
            spec.get("pct_improvement"),
            spec.get("p_value"),
            _bool_int(spec.get("dose_response")),
            _bool_int(spec.get("survival_benefit")),
            spec.get("face_validity"),
            spec.get("construct_validity"),
            spec.get("predictive_validity"),
            spec.get("endpoint_clinical_similarity"),
            spec.get("mechanism_similarity"),
            spec.get("pkpd_relevance"),
            _bool_int(spec.get("biomarker_overlap")),
            _bool_int(spec.get("human_target_validated")),
            _bool_int(spec.get("randomization_reported")),
            _bool_int(spec.get("blinding_reported")),
            _bool_int(spec.get("allocation_concealment")),
            _bool_int(spec.get("sample_size_calculation")),
            _bool_int(spec.get("exclusions_described")),
            _bool_int(spec.get("preregistration")),
            _bool_int(spec.get("peer_reviewed")),
            _bool_int(spec.get("independent_lab_replication")),
            _bool_int(spec.get("replicated_across_models")),
            _bool_int(spec.get("replicated_across_species")),
            spec.get("feature_source_sentence"),
            spec.get("reviewer_notes"),
        ),
    )
    conn.execute(
        """
        UPDATE animal_studies SET
            species = COALESCE(?, species),
            disease_model = COALESCE(?, disease_model),
            model_induction_method = COALESCE(?, model_induction_method),
            is_humanized_model = COALESCE(?, is_humanized_model),
            therapeutic_vs_prophylactic = COALESCE(?, therapeutic_vs_prophylactic),
            extracted_by = 'manual',
            extraction_confidence = ?,
            verification_status = ?
        WHERE study_id = ?
        """,
        (
            spec.get("species"),
            spec.get("disease_model"),
            spec.get("model_induction_method"),
            _bool_int(spec.get("is_humanized_model")),
            spec.get("therapeutic_vs_prophylactic"),
            spec.get("extraction_confidence", 0.9),
            spec.get("verification_status", "verified"),
            study_id,
        ),
    )


def apply_extractions(db_path: Path | None = None) -> dict[str, Any]:
    db_path = db_path or DB_PATH
    cfg = yaml.safe_load(EXTRACTIONS_PATH.read_text(encoding="utf-8"))
    conn = sqlite3.connect(db_path)
    summary: dict[str, Any] = {"programs": {}}

    try:
        for program_id, pcfg in cfg["programs"].items():
            if pcfg.get("inherit_from"):
                parent = cfg["programs"][pcfg["inherit_from"]]
                merged = {**parent, **pcfg}
                merged["studies"] = pcfg.get("studies") or parent.get("studies", [])
                merged["add_studies"] = pcfg.get("add_studies") or parent.get("add_studies", [])
                merged["reject_pmids"] = list(
                    set(parent.get("reject_pmids") or []) | set(pcfg.get("reject_pmids") or [])
                )
                pcfg = merged

            drug_row = conn.execute(
                "SELECT drug_name FROM programs WHERE program_id = ?", (program_id,)
            ).fetchone()
            drug_name = drug_row[0] if drug_row else ""

            stats = {"verified": 0, "rejected": 0, "added": 0}

            if pcfg.get("reject_all_existing"):
                rows = conn.execute(
                    "SELECT study_id FROM animal_studies WHERE program_id = ?",
                    (program_id,),
                ).fetchall()
                for (study_id,) in rows:
                    reject_study(conn, study_id, "Rejected: non-drug-specific auto-linked papers")
                    stats["rejected"] += 1

            reject_pmids = set(pcfg.get("reject_pmids") or [])
            rows = conn.execute(
                """
                SELECT s.study_id, pub.pmid FROM animal_studies s
                JOIN publications pub ON s.publication_id = pub.publication_id
                WHERE s.program_id = ?
                """,
                (program_id,),
            ).fetchall()

            extractions_by_pmid = {}  # handled in studies loop below

            for study_id, pmid in rows:
                if pmid in reject_pmids:
                    reject_study(conn, study_id, f"Rejected PMID {pmid}: not primary drug evidence")
                    stats["rejected"] += 1
                    continue
                # non-rejected, non-explicit studies left as pending unless in studies list

            for spec in pcfg.get("studies") or []:
                pmid = spec.get("pmid")
                if not pmid:
                    continue
                existing = conn.execute(
                    """
                    SELECT s.study_id FROM publications pub
                    JOIN animal_studies s ON pub.publication_id = s.publication_id
                    WHERE pub.pmid = ? AND s.program_id = ?
                    """,
                    (pmid, program_id),
                ).fetchone()
                if existing:
                    if spec.get("publication_date"):
                        conn.execute(
                            """
                            UPDATE source_records SET publication_date = ?
                            WHERE source_record_id = (
                                SELECT source_record_id FROM publications WHERE pmid = ?
                            )
                            """,
                            (spec["publication_date"], pmid),
                        )
                    apply_study_features(conn, existing[0], spec)
                    stats["verified"] += 1
                else:
                    add_publication_and_study(conn, program_id, drug_name, spec)
                    stats["added"] += 1
                    stats["verified"] += 1

            for spec in pcfg.get("add_studies") or []:
                existing = conn.execute(
                    "SELECT study_id FROM publications pub JOIN animal_studies s ON pub.publication_id = s.publication_id WHERE pub.pmid = ? AND s.program_id = ?",
                    (spec["pmid"], program_id),
                ).fetchone()
                if existing:
                    apply_study_features(conn, existing[0], spec)
                    stats["verified"] += 1
                else:
                    add_publication_and_study(conn, program_id, drug_name, spec)
                    stats["added"] += 1
                    stats["verified"] += 1

            compute_program_aggregates(conn, program_id)
            summary["programs"][program_id] = stats

        conn.commit()
    finally:
        conn.close()

    return summary


def main() -> None:
    summary = apply_extractions()
    print("Manual extraction applied:")
    for pid, stats in summary["programs"].items():
        print(f"  {pid}: verified={stats['verified']} rejected={stats['rejected']} added={stats['added']}")


if __name__ == "__main__":
    main()
