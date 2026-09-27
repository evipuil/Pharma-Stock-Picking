# Preclinical Translation Modeling

Testing whether characteristics of preclinical animal evidence predict clinical translation, with a secondary analysis of model–market probability gaps.

**Start here:** [PROJECT_PLAN.md](PROJECT_PLAN.md)

Current release: **v1.0**. See the [changelog](CHANGELOG.md),
[release notes](docs/releases/v1.0.md), and [versioning guide](docs/versioning.md).

The original August 19, 2026 baseline is preserved under `baseline_2026_08_19`
and `v0.1`. The current reports describe a promising but unvalidated short edge;
the existing evaluation periods are legacy research periods. See the
[code and market-edge audit](reports/CODE_AND_EDGE_AUDIT.md) for limitations.

## Quick links

| Document | Contents |
|----------|----------|
| [docs/schema.md](docs/schema.md) | Relational database design |
| [docs/inclusion_exclusion_criteria.md](docs/inclusion_exclusion_criteria.md) | Cohort rules |
| [docs/outcome_labeling_rules.md](docs/outcome_labeling_rules.md) | Clinical success/failure definitions |
| [docs/leakage_prevention.md](docs/leakage_prevention.md) | Look-ahead bias controls |
| [docs/data_sources.md](docs/data_sources.md) | Public APIs and limitations |
| [docs/mvp_cohort.md](docs/mvp_cohort.md) | Initial 20–50 program list |
| [docs/statistical_analysis_plan.md](docs/statistical_analysis_plan.md) | Modeling & hypothesis tests |
| [docs/automation_vs_manual.md](docs/automation_vs_manual.md) | Field-level extraction strategy |

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

Run the tests with `python -m pytest -q`. Downloaded GitHub datasets are kept
locally and can be fetched with `python -m src.cli seed-github-data`.
The working database and ignored raw/intermediate data are also local; this
repository includes the previously tracked research snapshots and reports.

## Project principles

1. **Unit of observation:** drug × indication × development stage
2. **Information cutoff `t0`:** only pre-t0 data in features
3. **No survivorship bias:** include failed/discontinued programs
4. **Calibration over accuracy:** probability estimates matter for P_market
5. **Temporal validation:** train on older, test on newer programs

## Modeling

Train animal → clinical prediction:

```bash
python -m src.cli add-failures      # load failure programs (once)
python -m src.cli apply-extractions # manual feature extraction
python -m src.cli train-model       # fit logistic models + baselines
python -m src.cli predict           # P(clinical success) for all programs
```

Models saved to `data/processed/models/`. Predictions to `data/processed/predictions.csv`.
