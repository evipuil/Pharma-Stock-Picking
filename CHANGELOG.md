# Changelog

## v1.0 - 2026-09-27

First numbered GitHub release of the current StockPicking research pipeline.

- Add point-in-time audits for market, company, filing, and trial data; retain
  timestamped ClinicalTrials.gov snapshots for future fetches.
- Correct event-session alignment, year-local short selection, training-only
  fallback estimates, signal execution, and company-exposure scaling.
- Quarantine the legacy holdout in routine short-edge evaluation, add year-block
  uncertainty estimates, and require prospective ranking provenance.
- Add GitHub catalyst discovery and date validation, a pilot import path,
  Stooq price recovery, public-data probes, and short-edge ablation reporting.
- Preserve the updated research reports, predictions, price snapshots, and
  original frozen baseline.
- Add package version 1.0.0, this changelog, and release/versioning documentation.

Validation for publication: 71 tests passed on 2026-09-27. The empirical studies
were not rerun for this release. The saved reports still classify the short edge
as promising but unvalidated and require a new prospective holdout.

## v0.1 - 2026-08-19

Original local baseline, commit `2958acc9b3d58e6718d19b811da2deedf9d935b6`.
The `v0.1` tag was assigned retrospectively for GitHub publication; the existing
`baseline_2026_08_19` tag is preserved.

- Freeze baseline configurations, database, predictions, model, and reports in
  `experiments/baseline_2026_08_19/`.
- Include the initial clinical translation, catalyst event-study, expected-return,
  walk-forward, ranking, and short-edge validation framework.

This baseline predates the corrections documented in v1.0. Its saved performance
reports should be interpreted alongside the current audit.
