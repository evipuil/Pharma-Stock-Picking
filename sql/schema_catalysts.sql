-- Catalyst-level extensions for stock-picking system
-- Apply additively after schema.sql (non-destructive)

PRAGMA foreign_keys = ON;

-- =============================================================================
-- CATALYSTS (primary unit of analysis)
-- =============================================================================

CREATE TABLE IF NOT EXISTS catalysts (
    catalyst_id              TEXT PRIMARY KEY,
    program_id               TEXT REFERENCES programs(program_id),
    company_id               TEXT REFERENCES companies(company_id),
    drug_name                TEXT NOT NULL,
    indication               TEXT NOT NULL,
    nct_id                   TEXT,
    trial_phase              TEXT,
    catalyst_type            TEXT NOT NULL DEFAULT 'PHASE2_READOUT' CHECK (catalyst_type IN (
        'PHASE1_READOUT', 'PHASE2_READOUT', 'PHASE3_READOUT',
        'INTERIM', 'PDUFA', 'ADCOM', 'OTHER'
    )),
    line_of_therapy          TEXT,
    biomarker_population     TEXT,
    combination_flag         INTEGER CHECK (combination_flag IN (0, 1)),
    comparator               TEXT,
    primary_endpoint         TEXT,
    enrollment               INTEGER,
    -- Timing (critical for backtest)
    expected_readout_date    DATE,
    announcement_date        DATE,
    announcement_timestamp   TEXT,  -- ISO8601 when known
    announcement_timing      TEXT CHECK (announcement_timing IN (
        'BMO', 'AMC', 'DURING', 'UNKNOWN'
    )) DEFAULT 'UNKNOWN',
    announcement_source      TEXT,
    announcement_source_url  TEXT,
    trading_cutoff_date      DATE,
    trading_day_before       DATE,
    first_trading_day_after  DATE,
    -- Outcome
    clinical_success         INTEGER CHECK (clinical_success IN (0, 1)),
    outcome_category         TEXT CHECK (outcome_category IN (
        'SUCCESS', 'EFFICACY_FAILURE', 'SAFETY_FAILURE', 'MIXED', 'UNKNOWN'
    )),
    met_primary_endpoint     INTEGER CHECK (met_primary_endpoint IN (0, 1)),
    outcome_notes            TEXT,
    -- Preclinical missingness (no publication required for inclusion)
    preclinical_evidence_found INTEGER CHECK (preclinical_evidence_found IN (0, 1)),
    n_preclinical_publications INTEGER DEFAULT 0,
    publication_coverage_confidence REAL,
    -- Provenance
    cohort_phase             TEXT DEFAULT 'phase_a',  -- phase_a | phase_b | holdout
    data_source              TEXT,
    created_at               TEXT DEFAULT (datetime('now')),
    updated_at               TEXT DEFAULT (datetime('now')),
    UNIQUE (drug_name, indication, nct_id, catalyst_type, announcement_date)
);

CREATE TABLE IF NOT EXISTS catalyst_ticker_history (
    map_id                   TEXT PRIMARY KEY,
    catalyst_id              TEXT NOT NULL REFERENCES catalysts(catalyst_id),
    ticker_at_event          TEXT NOT NULL,
    ticker_current           TEXT,
    exchange_at_event        TEXT,
    cik                      TEXT,
    delisted                 INTEGER CHECK (delisted IN (0, 1)) DEFAULT 0,
    delist_date              DATE,
    successor_ticker         TEXT,
    map_source               TEXT,
    notes                    TEXT
);

CREATE TABLE IF NOT EXISTS catalyst_trading_cutoffs (
    catalyst_id              TEXT PRIMARY KEY REFERENCES catalysts(catalyst_id),
    entry_cutoff_date        DATE NOT NULL,
    exit_rule                TEXT DEFAULT 'first_day_after',
    exit_date                DATE,
    cutoff_rationale         TEXT,
    execution_confidence     TEXT DEFAULT 'MEDIUM' CHECK (execution_confidence IN (
        'HIGH', 'MEDIUM', 'LOW'
    ))
);

-- =============================================================================
-- MARKET DATA (expanded OHLCV)
-- =============================================================================

CREATE TABLE IF NOT EXISTS market_bars_daily (
    bar_id                   TEXT PRIMARY KEY,
    ticker                   TEXT NOT NULL,
    date                     DATE NOT NULL,
    open                     REAL,
    high                     REAL,
    low                      REAL,
    close                    REAL,
    adj_close                REAL,
    volume                   REAL,
    provider                 TEXT NOT NULL,
    split_adjusted           INTEGER CHECK (split_adjusted IN (0, 1)) DEFAULT 1,
    UNIQUE (ticker, date, provider)
);

CREATE INDEX IF NOT EXISTS idx_market_bars_ticker_date ON market_bars_daily(ticker, date);

-- =============================================================================
-- EVENT STUDY RESULTS (catalyst-level)
-- =============================================================================

CREATE TABLE IF NOT EXISTS catalyst_event_study (
    es_id                    TEXT PRIMARY KEY,
    catalyst_id              TEXT NOT NULL REFERENCES catalysts(catalyst_id),
    window_label             TEXT NOT NULL,  -- e.g. '[-1,+1]', '[0,+5]'
    benchmark                TEXT NOT NULL,  -- RAW, SPY, XBI, IBB, MARKET_MODEL
    raw_return               REAL,
    abnormal_return          REAL,
    car                      REAL,
    alpha                    REAL,
    beta                     REAL,
    estimation_window_start  DATE,
    estimation_window_end    DATE,
    n_estimation_days        INTEGER,
    price_source             TEXT,
    ticker_used              TEXT,
    computed_at              TEXT DEFAULT (datetime('now')),
    UNIQUE (catalyst_id, window_label, benchmark)
);

-- =============================================================================
-- ASSET EXPOSURE & FUNDAMENTALS (Stage 5+, schema ready)
-- =============================================================================

CREATE TABLE IF NOT EXISTS asset_exposure (
    catalyst_id              TEXT PRIMARY KEY REFERENCES catalysts(catalyst_id),
    market_cap_usd           REAL,
    enterprise_value_usd     REAL,
    cash_usd                 REAL,
    debt_usd                 REAL,
    revenue_ttm_usd          REAL,
    n_clinical_assets        INTEGER,
    n_late_stage_assets      INTEGER,
    is_lead_asset            INTEGER CHECK (is_lead_asset IN (0, 1)),
    is_single_asset_company  INTEGER CHECK (is_single_asset_company IN (0, 1)),
    company_dependency       REAL,  -- 0-1 scale
    as_of_date               DATE NOT NULL,
    data_source              TEXT
);

CREATE TABLE IF NOT EXISTS point_in_time_fundamentals (
    fund_id                  TEXT PRIMARY KEY,
    catalyst_id              TEXT NOT NULL REFERENCES catalysts(catalyst_id),
    filing_type              TEXT,
    filing_date              DATE NOT NULL,
    period_end               DATE,
    cash_usd                 REAL,
    debt_usd                 REAL,
    shares_outstanding       REAL,
    market_cap_usd           REAL,
    revenue_usd              REAL,
    operating_cash_flow_usd  REAL,
    cash_runway_months       REAL,
    source                   TEXT,
    UNIQUE (catalyst_id, filing_date, filing_type)
);

-- =============================================================================
-- VIEWS
-- =============================================================================

CREATE VIEW IF NOT EXISTS v_catalysts_prospective AS
SELECT
    c.*,
    ct.ticker_at_event,
    ct.delisted,
    tc.entry_cutoff_date,
    ces.car AS car_m1_p1_spy,
    ces_xbi.car AS car_m1_p1_xbi
FROM catalysts c
LEFT JOIN catalyst_ticker_history ct ON c.catalyst_id = ct.catalyst_id
LEFT JOIN catalyst_trading_cutoffs tc ON c.catalyst_id = tc.catalyst_id
LEFT JOIN catalyst_event_study ces
    ON c.catalyst_id = ces.catalyst_id
    AND ces.window_label = '[-1,+1]' AND ces.benchmark = 'MARKET_MODEL'
LEFT JOIN catalyst_event_study ces_xbi
    ON c.catalyst_id = ces_xbi.catalyst_id
    AND ces_xbi.window_label = '[-1,+1]' AND ces_xbi.benchmark = 'XBI_MODEL';

CREATE INDEX IF NOT EXISTS idx_catalysts_announcement ON catalysts(announcement_date);
CREATE INDEX IF NOT EXISTS idx_catalysts_program ON catalysts(program_id);
