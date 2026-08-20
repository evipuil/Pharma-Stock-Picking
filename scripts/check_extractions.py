import sqlite3
from pathlib import Path

conn = sqlite3.connect(Path("data/processed/research.db"))
conn.row_factory = sqlite3.Row
rows = conn.execute(
    """
SELECT p.program_id, pub.pmid, s.verification_status, s.species, s.disease_model,
       f.primary_endpoint, f.face_validity, pf.n_animal_studies
FROM programs p
JOIN animal_studies s ON p.program_id = s.program_id
JOIN publications pub ON s.publication_id = pub.publication_id
LEFT JOIN animal_study_features f ON s.study_id = f.study_id
LEFT JOIN program_preclinical_features pf ON p.program_id = pf.program_id
WHERE s.verification_status = 'verified'
ORDER BY p.program_id, pub.pmid
"""
).fetchall()
for r in rows:
    print(dict(r))
print("verified", len(rows))
print("rejected", conn.execute("SELECT COUNT(*) FROM animal_studies WHERE verification_status='rejected'").fetchone()[0])
