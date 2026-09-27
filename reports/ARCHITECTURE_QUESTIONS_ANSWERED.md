# Architecture Questions Answered

Date: 2026-08-21

## 1. Why does `project_root()` cross so many communities?

It is the repository-wide path service. Data loaders, model trainers, reports, adapters, and
validators call it to locate configuration, SQLite, cached prices, models, and outputs. The graph
contains 78 inferred call edges from 41 files across 24 communities. All 78 resolve to real source
call sites. This is broad utility coupling, not hidden financial data flow.

No refactor was made: replacing one stable path helper with dependency plumbing throughout the
repository would add churn without improving model validity. The higher-value orchestrators now
accept or propagate explicit dates and source provenance where time matters.

## 2. Why does CLI `main()` connect nearly every workflow?

`src/cli.py::main` is the command router. It declares every subcommand and lazily imports the
corresponding handler. Its 59 inferred call edges span 23 communities, and all 59 resolve to real
calls inside the command branches. The degree is expected for a CLI composition root; it is not a
single execution path in which every handler runs.

## 3. Why does `run_short_edge_validation()` bridge several communities?

It is a deliberate short-research orchestration boundary:

1. freeze the baseline;
2. attempt delisted-price recovery;
3. load the short modeling frame;
4. compute and persist company dependency;
5. run expanding-window short models;
6. export predictions and generate validation reports.

Its 11 call edges cross six communities and all are genuine. The function does not fetch PubMed or
train the general expected-CAR model.

## 4. Are the 78 inferred `project_root()` relationships correct?

Yes. Automated source-line verification found 78/78 target calls at the graph-recorded files and
locations.

## 5. Are the 59 inferred CLI `main()` relationships correct?

Yes. Automated source-line verification found 59/59. They represent alternative CLI branches,
not calls made together during every invocation.

## 6. Are the 30 inferred `run_stock_picking_pipeline()` relationships correct?

Yes. Automated source-line verification found 30/30. The function is a monolithic research
orchestrator spanning date curation, feature construction, event studies, fitting, walk-forward
evaluation, backtesting, reporting, and ranking. Its breadth is real.

The material improvement was to insert a point-in-time audit before model fitting and to make
ranking prospective by default. Research evaluation and current candidate ranking now have
explicitly different date semantics.

## 7. Are the 22 inferred `load_yaml()` relationships correct?

Yes. Automated source-line verification found 22/22. They load shared cohort, data-source,
market, exposure, validation, and trading configuration. This is configuration coupling, not
evidence that the modules share outcome data.

## 8. Are the five PubMed connections real?

Yes. Cohort expansion, failure-cohort loading, Wave 1 curation, and missing-publication-date repair
instantiate `PubMedClient` to find animal literature restricted by the program's t0 date. These are
cohort/evidence acquisition paths, not runtime ranking calls.

## 9. Where do time-cutoff assumptions enter, and what reaches the models?

1. Announcement overrides or backfills establish `announcement_date` and a conservative entry
   cutoff.
2. Event study day zero is the first market session on or after the announcement.
3. Market features use prices strictly before the cutoff and record the final price date actually
   used.
4. SEC features accept only observations whose filing and period-end dates are on/before cutoff;
   exposure availability is the later of filing date and price date.
5. Preclinical publications are filtered at program t0 and checked by the leakage audit.
6. Clinical trial design came from current CT.gov records. Every historical record was fetched in
   2026, so the repository cannot prove those values existed unchanged at historical cutoffs.
7. Strict model frames now null market, exposure, or clinical feature families whose observation
   date is after—or cannot be verified by—the cutoff.
8. Walk-forward models train only on earlier catalyst years. Conditional-return fallbacks are now
   frozen from the training fold rather than derived from test outcomes.
9. Live ranking defaults to catalysts on or after today's date, requires a model trained under the
   strict provenance policy, and exports source-date verification fields.

## Remaining evidence gap

The code now stores immutable timestamped CT.gov snapshots for future fetches, but historical
snapshots do not exist in this repository. Consequently, trial-design features are excluded from
strict historical modeling. Recovering dated AACT/CT.gov histories is a data-acquisition task, not
something the current record can reconstruct safely.
