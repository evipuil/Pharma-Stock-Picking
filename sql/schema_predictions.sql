-- Catalyst-level predictions and OOS ledger (Stage 6-9)

CREATE TABLE IF NOT EXISTS catalyst_predictions (
    prediction_id          TEXT PRIMARY KEY,
    catalyst_id            TEXT NOT NULL REFERENCES catalysts(catalyst_id),
    model_version          TEXT NOT NULL,
    p_success              REAL,
    e_car_given_success    REAL,
    e_car_given_failure    REAL,
    expected_car           REAL,
    expected_car_lower     REAL,
    expected_car_upper     REAL,
    train_cutoff_year      INTEGER,
    prediction_split       TEXT,  -- train | validation | test | oos
    feature_set            TEXT,
    computed_at            TEXT DEFAULT (datetime('now')),
    UNIQUE (catalyst_id, model_version, train_cutoff_year)
);

CREATE TABLE IF NOT EXISTS walk_forward_ledger (
    ledger_id              TEXT PRIMARY KEY,
    catalyst_id            TEXT NOT NULL REFERENCES catalysts(catalyst_id),
    train_end_year         INTEGER NOT NULL,
    test_year              INTEGER NOT NULL,
    p_success              REAL,
    expected_car           REAL,
    realized_car           REAL,
    clinical_success       INTEGER,
    trade_signal           TEXT,
    model_version          TEXT,
    computed_at            TEXT DEFAULT (datetime('now')),
    UNIQUE (catalyst_id, train_end_year, test_year)
);

CREATE INDEX IF NOT EXISTS idx_catalyst_predictions_catalyst ON catalyst_predictions(catalyst_id);
CREATE INDEX IF NOT EXISTS idx_walk_forward_ledger_year ON walk_forward_ledger(test_year);
