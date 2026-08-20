-- Preclinical Translation & Biotech Mispricing Research Database
-- SQLite-compatible DDL (PostgreSQL: change TEXT PK to UUID, adjust JSON types)

PRAGMA foreign_keys = ON;

-- =============================================================================
-- REFERENCE & PROVENANCE
-- =============================================================================

CREATE TABLE IF NOT EXISTS source_records (
    source_record_id     TEXT PRIMARY KEY,
    source_type          TEXT NOT NULL CHECK (source_type IN (
        'PUBMED', 'PMC', 'CROSSREF', 'EUROPE_PMC', 'CTGOV', 'SEC', 'PRESS', 'MANUAL', 'OTHER'
    )),
    source_identifier    TEXT,
    url                  TEXT,
    title                TEXT,
    publication_date     DATE,
    online_first_date    DATE,
    trial_registration_date DATE,
    company_announcement_date DATE,
    data_extraction_timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    is_peer_reviewed     INTEGER CHECK (is_peer_reviewed IN (0, 1)),
    full_text_available  INTEGER CHECK (full_text_available IN (0, 1)),
    raw_storage_path     TEXT
);

CREATE TABLE IF NOT EXISTS companies (
    company_id               TEXT PRIMARY KEY,
    ticker                   TEXT NOT NULL,
    cik                      TEXT,
    company_name             TEXT NOT NULL,
    exchange                 TEXT,
    is_biotech_sponsor       INTEGER CHECK (is_biotech_sponsor IN (0, 1)),
    market_cap_usd_at_t0     REAL,
    cash_usd_at_t0           REAL,
    portfolio_drug_count_at_t0 INTEGER,
    created_at               TEXT DEFAULT (datetime('now')),
    updated_at               TEXT DEFAULT (datetime('now'))
);

-- =============================================================================
-- PROGRAMS & T0
-- =============================================================================

CREATE TABLE IF NOT EXISTS programs (
    program_id               TEXT PRIMARY KEY,
    company_id               TEXT NOT NULL REFERENCES companies(company_id),
    drug_name                TEXT NOT NULL,
    drug_synonyms            TEXT,  -- JSON array
    indication               TEXT NOT NULL,
    indication_mesh          TEXT,
    modality                 TEXT,
    target                   TEXT,
    biomarker_strategy       TEXT,
    development_stage_at_t0  TEXT NOT NULL DEFAULT 'PHASE2',
    primary_nct_id           TEXT,
    cohort_inclusion_date    DATE,
    mvp_wave                 TEXT DEFAULT 'wave_1',
    notes                    TEXT,
    UNIQUE (drug_name, indication, development_stage_at_t0, primary_nct_id)
);

CREATE TABLE IF NOT EXISTS program_t0 (
    program_id           TEXT PRIMARY KEY REFERENCES programs(program_id),
    t0_date              DATE NOT NULL,
    t0_definition        TEXT NOT NULL CHECK (t0_definition IN (
        'FIRST_PATIENT_DOSED', 'TRIAL_START', 'OTHER'
    )),
    t0_source_type       TEXT,
    t0_source_record_id  TEXT REFERENCES source_records(source_record_id),
    t0_rationale         TEXT,
    defined_by           TEXT,
    defined_at           TEXT DEFAULT (datetime('now'))
);

-- =============================================================================
-- CLINICAL TRIALS & OUTCOMES
-- =============================================================================

CREATE TABLE IF NOT EXISTS clinical_trials (
    nct_id                       TEXT PRIMARY KEY,
    program_id                   TEXT NOT NULL REFERENCES programs(program_id),
    brief_title                  TEXT,
    phase                        TEXT,
    study_type                   TEXT,
    condition                    TEXT,
    intervention                 TEXT,
    sponsor                      TEXT,
    collaborator                 TEXT,
    start_date                   DATE,
    primary_completion_date      DATE,
    study_completion_date        DATE,
    first_posted_date            DATE,
    results_first_posted_date    DATE,
    enrollment                   INTEGER,
    allocation                   TEXT,
    masking                      TEXT,
    primary_purpose              TEXT,
    api_fetched_at               TEXT,
    raw_json_path                TEXT
);

CREATE TABLE IF NOT EXISTS trial_outcomes (
    outcome_id               TEXT PRIMARY KEY,
    program_id               TEXT NOT NULL REFERENCES programs(program_id),
    nct_id                   TEXT REFERENCES clinical_trials(nct_id),
    outcome_level            TEXT NOT NULL CHECK (outcome_level IN (
        'PHASE2', 'PHASE3', 'REGULATORY'
    )),
    clinical_success         INTEGER CHECK (clinical_success IN (0, 1)),
    met_primary_endpoint     INTEGER CHECK (met_primary_endpoint IN (0, 1)),
    advanced_to_phase3       INTEGER CHECK (advanced_to_phase3 IN (0, 1)),
    regulatory_approval      INTEGER CHECK (regulatory_approval IN (0, 1)),
    technical_failure        INTEGER CHECK (technical_failure IN (0, 1)),
    safety_failure           INTEGER CHECK (safety_failure IN (0, 1)),
    commercial_discontinuation INTEGER CHECK (commercial_discontinuation IN (0, 1)),
    outcome_unknown          INTEGER CHECK (outcome_unknown IN (0, 1)),
    failure_reason_detail    TEXT,
    outcome_date             DATE,
    outcome_source_record_id TEXT REFERENCES source_records(source_record_id),
    labeling_rule_version    TEXT NOT NULL DEFAULT 'v1.0',
    adjudicated_by           TEXT,
    adjudicated_at           TEXT,
    notes                    TEXT
);

-- =============================================================================
-- LITERATURE & ANIMAL STUDIES
-- =============================================================================

CREATE TABLE IF NOT EXISTS publications (
    publication_id       TEXT PRIMARY KEY,
    source_record_id     TEXT NOT NULL REFERENCES source_records(source_record_id),
    pmid                 TEXT,
    pmcid                TEXT,
    doi                  TEXT,
    abstract             TEXT,
    study_type_inferred  TEXT
);

CREATE TABLE IF NOT EXISTS publication_program_links (
    link_id          TEXT PRIMARY KEY,
    publication_id   TEXT NOT NULL REFERENCES publications(publication_id),
    program_id       TEXT NOT NULL REFERENCES programs(program_id),
    relevance        TEXT,
    linked_by          TEXT CHECK (linked_by IN ('auto', 'manual'))
);

CREATE TABLE IF NOT EXISTS animal_studies (
    study_id                     TEXT PRIMARY KEY,
    program_id                   TEXT NOT NULL REFERENCES programs(program_id),
    publication_id               TEXT REFERENCES publications(publication_id),
    drug_name                    TEXT,
    indication_model             TEXT,
    species                      TEXT,
    strain                       TEXT,
    sex                          TEXT,
    age                          TEXT,
    disease_model                TEXT,
    model_induction_method       TEXT,
    sample_size_treatment        INTEGER,
    sample_size_control          INTEGER,
    control_type                 TEXT,
    is_humanized_model           INTEGER CHECK (is_humanized_model IN (0, 1)),
    is_pdx                       INTEGER CHECK (is_pdx IN (0, 1)),
    therapeutic_vs_prophylactic  TEXT,
    extracted_by                 TEXT CHECK (extracted_by IN ('manual', 'nlp', 'hybrid')),
    extraction_confidence        REAL,
    verification_status          TEXT DEFAULT 'pending' CHECK (verification_status IN (
        'pending', 'verified', 'rejected'
    ))
);

CREATE TABLE IF NOT EXISTS animal_study_features (
    study_id                     TEXT PRIMARY KEY REFERENCES animal_studies(study_id),
    -- Efficacy
    primary_endpoint             TEXT,
    effect_size                  REAL,
    effect_size_type             TEXT,  -- HR, OR, pct_change, etc.
    pct_improvement              REAL,
    p_value                      REAL,
    ci_lower                     REAL,
    ci_upper                     REAL,
    se                           REAL,
    sd                           REAL,
    dose_mg_kg                   REAL,
    dose_response                INTEGER CHECK (dose_response IN (0, 1)),
    survival_benefit             INTEGER CHECK (survival_benefit IN (0, 1)),
    -- Translational validity (ordinal 0/1/2 or NULL if not assessed)
    face_validity                INTEGER,
    construct_validity           INTEGER,
    predictive_validity          INTEGER,
    endpoint_clinical_similarity INTEGER,
    mechanism_similarity         INTEGER,
    pkpd_relevance               INTEGER,
    biomarker_overlap            INTEGER,
    human_target_validated       INTEGER CHECK (human_target_validated IN (0, 1)),
    -- Study quality / bias (ARRIVE 2.0 / Landis)
    randomization_reported       INTEGER CHECK (randomization_reported IN (0, 1)),
    blinding_reported            INTEGER CHECK (blinding_reported IN (0, 1)),
    allocation_concealment       INTEGER CHECK (allocation_concealment IN (0, 1)),
    sample_size_calculation      INTEGER CHECK (sample_size_calculation IN (0, 1)),
    exclusions_described         INTEGER CHECK (exclusions_described IN (0, 1)),
    preregistration              INTEGER CHECK (preregistration IN (0, 1)),
    conflict_of_interest_reported INTEGER CHECK (conflict_of_interest_reported IN (0, 1)),
    peer_reviewed                INTEGER CHECK (peer_reviewed IN (0, 1)),
    independent_lab_replication  INTEGER CHECK (independent_lab_replication IN (0, 1)),
    replicated_across_models     INTEGER CHECK (replicated_across_models IN (0, 1)),
    replicated_across_species    INTEGER CHECK (replicated_across_species IN (0, 1)),
    -- Provenance per extraction
    feature_extraction_method    TEXT,
    feature_source_sentence      TEXT,
    feature_page_ref             TEXT
);

CREATE TABLE IF NOT EXISTS program_preclinical_features (
    program_id                   TEXT PRIMARY KEY REFERENCES programs(program_id),
    n_animal_studies             INTEGER DEFAULT 0,
    n_species                    INTEGER,
    n_models                     INTEGER,
    best_effect_size             REAL,
    median_effect_size           REAL,
    any_dose_response            INTEGER CHECK (any_dose_response IN (0, 1)),
    pct_studies_randomized       REAL,
    pct_studies_blinded          REAL,
    any_independent_replication  INTEGER CHECK (any_independent_replication IN (0, 1)),
    any_humanized_or_pdx         INTEGER CHECK (any_humanized_or_pdx IN (0, 1)),
    pts_composite                REAL,
    pts_version                  TEXT,
    aggregation_rule_version     TEXT DEFAULT 'v1.0',
    computed_at                  TEXT DEFAULT (datetime('now'))
);

-- =============================================================================
-- BASELINES & MODELING
-- =============================================================================

CREATE TABLE IF NOT EXISTS benchmark_pos_rates (
    rate_id              TEXT PRIMARY KEY,
    source               TEXT NOT NULL,
    phase                TEXT,
    indication_group     TEXT,
    modality             TEXT,
    biomarker_enriched   INTEGER CHECK (biomarker_enriched IN (0, 1)),
    success_rate         REAL NOT NULL,
    n_programs           INTEGER,
    effective_year_range TEXT
);

CREATE TABLE IF NOT EXISTS model_predictions (
    prediction_id        TEXT PRIMARY KEY,
    program_id           TEXT NOT NULL REFERENCES programs(program_id),
    model_name           TEXT NOT NULL,
    model_version        TEXT,
    p_model              REAL NOT NULL CHECK (p_model >= 0 AND p_model <= 1),
    prediction_made_at   DATE,
    feature_set          TEXT,
    train_cohort         TEXT
);

-- =============================================================================
-- FINANCIAL / EVENT STUDY
-- =============================================================================

CREATE TABLE IF NOT EXISTS program_financial_events (
    event_id             TEXT PRIMARY KEY,
    program_id           TEXT NOT NULL REFERENCES programs(program_id),
    event_type           TEXT NOT NULL,
    event_date           DATE NOT NULL,
    event_date_source    TEXT,
    event_date_precision TEXT DEFAULT 'DAY',
    outcome_direction    TEXT,
    concurrent_event_flag INTEGER CHECK (concurrent_event_flag IN (0, 1))
);

CREATE TABLE IF NOT EXISTS market_data_daily (
    id                   TEXT PRIMARY KEY,
    ticker               TEXT NOT NULL,
    date                 DATE NOT NULL,
    adj_close            REAL,
    volume               REAL,
    source               TEXT,
    UNIQUE (ticker, date)
);

CREATE TABLE IF NOT EXISTS event_study_results (
    result_id            TEXT PRIMARY KEY,
    event_id             TEXT NOT NULL REFERENCES program_financial_events(event_id),
    window               TEXT NOT NULL,
    benchmark_model      TEXT NOT NULL,
    car                  REAL,
    ar_series_json       TEXT,
    estimated_at         TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS market_implied_probability (
    id                   TEXT PRIMARY KEY,
    program_id           TEXT NOT NULL REFERENCES programs(program_id),
    p_market             REAL CHECK (p_market >= 0 AND p_market <= 1),
    estimation_method    TEXT,
    as_of_date           DATE,
    confidence           TEXT
);

-- =============================================================================
-- QA & REVIEW
-- =============================================================================

CREATE TABLE IF NOT EXISTS leakage_audit_log (
    audit_id             TEXT PRIMARY KEY,
    program_id           TEXT NOT NULL REFERENCES programs(program_id),
    check_type           TEXT NOT NULL,
    passed               INTEGER NOT NULL CHECK (passed IN (0, 1)),
    violation_detail     TEXT,
    checked_at           TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS extraction_review_queue (
    queue_id             TEXT PRIMARY KEY,
    study_id             TEXT NOT NULL REFERENCES animal_studies(study_id),
    field_name           TEXT NOT NULL,
    extracted_value      TEXT,
    source_sentence      TEXT,
    confidence           REAL,
    reviewer             TEXT,
    status               TEXT DEFAULT 'pending',
    corrected_value      TEXT
);

-- =============================================================================
-- INDEXES
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_programs_company ON programs(company_id);
CREATE INDEX IF NOT EXISTS idx_trials_program ON clinical_trials(program_id);
CREATE INDEX IF NOT EXISTS idx_animal_studies_program ON animal_studies(program_id);
CREATE INDEX IF NOT EXISTS idx_source_pub_date ON source_records(publication_date);
CREATE INDEX IF NOT EXISTS idx_financial_events_date ON program_financial_events(event_date);
CREATE INDEX IF NOT EXISTS idx_market_data_ticker_date ON market_data_daily(ticker, date);

-- =============================================================================
-- ANALYSIS VIEWS
-- =============================================================================

CREATE VIEW IF NOT EXISTS v_programs_prospective AS
SELECT
    p.*,
    t0.t0_date,
    t0.t0_definition,
    o.clinical_success,
    o.outcome_date,
    pf.n_animal_studies,
    la.passed AS leakage_passed
FROM programs p
JOIN program_t0 t0 ON p.program_id = t0.program_id
LEFT JOIN trial_outcomes o ON p.program_id = o.program_id AND o.outcome_level = 'PHASE2'
LEFT JOIN program_preclinical_features pf ON p.program_id = pf.program_id
LEFT JOIN (
    SELECT program_id, MIN(passed) AS passed
    FROM leakage_audit_log
    GROUP BY program_id
) la ON p.program_id = la.program_id;
