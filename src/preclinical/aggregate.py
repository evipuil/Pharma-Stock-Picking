"""Program-level preclinical feature aggregation."""

from __future__ import annotations

import sqlite3


def compute_program_aggregates(conn: sqlite3.Connection, program_id: str) -> None:
    """Aggregate verified animal_study_features to program_preclinical_features."""
    rows = conn.execute(
        """
        SELECT
            s.study_id, s.species, s.disease_model, s.is_humanized_model, s.is_pdx,
            f.effect_size, f.dose_response, f.survival_benefit, f.p_value,
            f.randomization_reported, f.blinding_reported, f.sample_size_calculation,
            f.independent_lab_replication, f.replicated_across_models, f.replicated_across_species,
            f.face_validity, f.endpoint_clinical_similarity, f.pkpd_relevance,
            f.human_target_validated
        FROM animal_studies s
        JOIN animal_study_features f ON s.study_id = f.study_id
        WHERE s.program_id = ? AND s.verification_status = 'verified'
        """,
        (program_id,),
    ).fetchall()

    if not rows:
        conn.execute(
            """
            INSERT OR REPLACE INTO program_preclinical_features (
                program_id, n_animal_studies, aggregation_rule_version, computed_at
            ) VALUES (?, 0, 'v1.0_manual', datetime('now'))
            """,
            (program_id,),
        )
        return

    effect_sizes = [r[5] for r in rows if r[5] is not None]
    rand = [r[9] for r in rows if r[9] is not None]
    blind = [r[10] for r in rows if r[10] is not None]
    species_set = {r[1] for r in rows if r[1]}
    models_set = {r[2] for r in rows if r[2]}

    conn.execute(
        """
        INSERT OR REPLACE INTO program_preclinical_features (
            program_id, n_animal_studies, n_species, n_models,
            best_effect_size, median_effect_size,
            any_dose_response, pct_studies_randomized, pct_studies_blinded,
            any_independent_replication, any_humanized_or_pdx,
            aggregation_rule_version, computed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'v1.0_manual', datetime('now'))
        """,
        (
            program_id,
            len(rows),
            len(species_set),
            len(models_set),
            max(effect_sizes) if effect_sizes else None,
            sorted(effect_sizes)[len(effect_sizes) // 2] if effect_sizes else None,
            1 if any(r[6] == 1 for r in rows) else 0,
            sum(rand) / len(rand) if rand else None,
            sum(blind) / len(blind) if blind else None,
            1 if any(r[12] == 1 for r in rows) else 0,
            1 if any(r[3] == 1 or r[4] == 1 for r in rows) else 0,
        ),
    )


def export_extraction_summary(conn: sqlite3.Connection) -> list[dict]:
    """Return human-readable extraction summary for reporting."""
    cur = conn.execute(
        """
        SELECT
            p.program_id, p.drug_name, pub.pmid, sr.title,
            s.species, s.disease_model, s.verification_status,
            f.primary_endpoint, f.effect_size, f.face_validity,
            f.endpoint_clinical_similarity, f.randomization_reported,
            f.feature_source_sentence, pf.n_animal_studies
        FROM programs p
        JOIN animal_studies s ON p.program_id = s.program_id
        JOIN publications pub ON s.publication_id = pub.publication_id
        JOIN source_records sr ON pub.source_record_id = sr.source_record_id
        LEFT JOIN animal_study_features f ON s.study_id = f.study_id
        LEFT JOIN program_preclinical_features pf ON p.program_id = pf.program_id
        ORDER BY p.program_id, sr.publication_date
        """
    )
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]
