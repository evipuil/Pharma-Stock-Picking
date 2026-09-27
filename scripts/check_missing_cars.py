import sqlite3
import pandas as pd

conn = sqlite3.connect("data/processed/research.db")
missing = pd.read_sql(
    """
    SELECT c.catalyst_id, ct.ticker_at_event, c.announcement_date, c.drug_name
    FROM catalysts c
    JOIN catalyst_ticker_history ct ON c.catalyst_id = ct.catalyst_id
    LEFT JOIN catalyst_event_study es ON c.catalyst_id = es.catalyst_id
        AND es.window_label = '[-1,+1]' AND es.benchmark = 'MARKET_MODEL'
    WHERE es.car IS NULL
    """,
    conn,
)
print("Missing CAR:", len(missing))
print(missing.to_string(index=False))
n = conn.execute(
    "SELECT COUNT(DISTINCT catalyst_id) FROM catalyst_event_study "
    "WHERE car IS NOT NULL AND window_label='[-1,+1]'"
).fetchone()[0]
print("Priced catalysts:", n)
