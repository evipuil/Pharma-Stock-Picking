-- Stage 5: pre-catalyst market expectation features (point-in-time at trading cutoff)

CREATE TABLE IF NOT EXISTS catalyst_market_features (
    catalyst_id              TEXT PRIMARY KEY REFERENCES catalysts(catalyst_id),
    as_of_date               DATE NOT NULL,
    ticker                   TEXT NOT NULL,
    price_at_cutoff          REAL,
    return_1d                REAL,
    return_5d                REAL,
    return_20d               REAL,
    return_60d               REAL,
    return_120d               REAL,
    abnormal_return_20d_xbi  REAL,
    abnormal_return_60d_xbi  REAL,
    distance_from_52w_high   REAL,
    realized_vol_20d         REAL,
    volume_ratio_20d         REAL,
    pre_catalyst_runup_60d   REAL,
    data_source              TEXT DEFAULT 'yfinance',
    computed_at              TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_catalyst_market_features_date ON catalyst_market_features(as_of_date);
