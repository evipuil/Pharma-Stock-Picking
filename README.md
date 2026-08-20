# StockPicking: Preclinical Translation & Biotech Mispricing Research

Research pipeline testing whether **preclinical animal evidence characteristics** prospectively predict **clinical trial success** and whether model–market probability gaps identify **mispricing** in biotech/pharma stocks.

**Start here:** [PROJECT_PLAN.md](PROJECT_PLAN.md)

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
