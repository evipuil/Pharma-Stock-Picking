-- Stage 6: catalyst-level trial design features (point-in-time at trading cutoff)

CREATE TABLE IF NOT EXISTS catalyst_trial_features (
    catalyst_id                  TEXT PRIMARY KEY REFERENCES catalysts(catalyst_id),
    nct_id                       TEXT,
    phase                        TEXT,
    phase_numeric                REAL,
    enrollment                   INTEGER,
    log_enrollment               REAL,
    is_randomized                INTEGER CHECK (is_randomized IN (0, 1)),
    is_blinded                   INTEGER CHECK (is_blinded IN (0, 1)),
    is_combination               INTEGER CHECK (is_combination IN (0, 1)),
    endpoint_os                  INTEGER CHECK (endpoint_os IN (0, 1)),
    endpoint_pfs                 INTEGER CHECK (endpoint_pfs IN (0, 1)),
    endpoint_orr                 INTEGER CHECK (endpoint_orr IN (0, 1)),
    endpoint_safety              INTEGER CHECK (endpoint_safety IN (0, 1)),
    wong_pos_rate                REAL,
    n_prior_same_drug            INTEGER,
    prior_success_rate_same_drug REAL,
    trial_start_date             DATE,
    first_posted_date            DATE,
    data_source                  TEXT DEFAULT 'ctgov',
    computed_at                  TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_catalyst_trial_features_nct ON catalyst_trial_features(nct_id);
