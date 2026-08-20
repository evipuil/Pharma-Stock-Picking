import sqlite3
from pathlib import Path

conn = sqlite3.connect(Path("data/processed/research.db"))
rows = conn.execute(
    """
SELECT s.program_id, s.study_id, s.verification_status, pub.pmid, sr.publication_date
FROM animal_studies s
JOIN publications pub ON s.publication_id = pub.publication_id
JOIN source_records sr ON pub.source_record_id = sr.source_record_id
WHERE s.program_id IN ('C005', 'C009')
ORDER BY s.program_id, s.verification_status
"""
).fetchall()
for r in rows:
    print(r)
