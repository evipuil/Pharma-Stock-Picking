# GitHub Events Validation Report

Source: [ejeej/EventsStockPrices](https://github.com/ejeej/EventsStockPrices)

## Registry date validation (112 catalysts)

- Matched to GitHub clinical event: **22** / **112**

### Match quality

- NO_MATCH: 90
- EXACT: 13
- LARGE_DRIFT: 7
- MODERATE_DRIFT: 1
- CLOSE: 1

## Inferred/legacy sources with GitHub match

- Count: 9
- Suggested date corrections (≥30d drift, drug_score≥0.7): **0**

Suggestions file: `configs\github_events_date_suggestions.yaml`

## Cohort expansion candidates

- New Phase 2/3 events (2010–2020, not in registry): **200**
- CSV: `data\processed\github_events_candidates.csv`
- YAML: `configs\github_events_candidates.yaml`

## Largest date drifts (matched, |delta| ≥ 90 days)

catalyst_id ticker              drug_name registry_date github_date  date_delta_days   match_status    announcement_source
   CAT-F044   GILD             simtuzumab    2020-07-01  2021-06-28            362.0    LARGE_DRIFT INFERRED_CTGOV_RESULTS
   CAT-F008   TGTX             umbralisib    2016-05-25  2017-04-28            338.0    LARGE_DRIFT        LEGACY_UNTAGGED
   CAT-F028   SGEN denintuzumab mafodotin    2019-01-08  2019-08-23            227.0    LARGE_DRIFT INFERRED_CTGOV_RESULTS
   CAT-C077   EPZM           tazemetostat    2016-12-03  2017-06-14            193.0    LARGE_DRIFT          PRESS_RELEASE
   CAT-F027  RHHBY    pinatuzumab vedotin    2018-04-19  2018-10-15            179.0    LARGE_DRIFT INFERRED_CTGOV_RESULTS
   CAT-C063    PFE             lorlatinib    2018-05-29  2018-10-04            128.0    LARGE_DRIFT INFERRED_CTGOV_RESULTS
   CAT-C051   AMGN           blinatumomab    2017-02-08  2017-05-22            103.0    LARGE_DRIFT INFERRED_CTGOV_RESULTS
   CAT-C043    PFE               axitinib    2021-05-24  2021-04-08            -46.0 MODERATE_DRIFT INFERRED_CTGOV_RESULTS

## Sample new candidates (first 15)

candidate_id ticker                            drug_name                                                                                                  indication announcement_date    stage                                                                                                                                                                                                                                                                                                   event_desc                  source cohort_phase        announcement_source
      GH0001   NKTR Etirinotecan pegol NKTR-102 (BEACON)                                                                           Cancer - Metastatic Breast Cancer        2015-03-17  Phase 3                                                                                                                                                                                                                                      Phase 3 topline data mid March 17, 2015 did not reach primary endpoint. ejeej/EventsStockPrices      phase_b GITHUB_EVENTS_STOCK_PRICES
      GH0002   NYMX      Fexapotide Triflutate (NX-1207)                                                                                                         BPH        2015-07-27  Phase 3                                                                                                                                                                                                                                                          Phase 3 endpoints met in extension trial July 2015. ejeej/EventsStockPrices      phase_b GITHUB_EVENTS_STOCK_PRICES
      GH0003   NBIX                  ORILISSA (Elagolix)                                                                                               Endometriosis        2015-08-01  Phase 3                                                                                                                                                                                                                                         First Phase 3 trial met both co-primary endpoints - January 8, 2015. ejeej/EventsStockPrices      phase_b GITHUB_EVENTS_STOCK_PRICES
      GH0004   ABBV                  ORILISSA (Elagolix)                                                                                               Endometriosis        2015-08-01  Phase 3                                                                                                                                                                                                                                         First Phase 3 trial met both co-primary endpoints - January 8, 2015. ejeej/EventsStockPrices      phase_b GITHUB_EVENTS_STOCK_PRICES
      GH0005   AMGN   Omecamtiv mecarbil - (GALACTIC-HF)                                                                                         Acute heart failure        2015-10-27  Phase 2 Phase 2 trial data released October 27, 2015. The Phase 2 trial met the objectives related to safety, tolerability, pharmacokinetics and pharmacodynamics in a population of chronic heart failure patients. The trial showed statistically significant improvements in several measures of cardiac function ejeej/EventsStockPrices      phase_b GITHUB_EVENTS_STOCK_PRICES
      GH0006   CYTK   Omecamtiv mecarbil - (GALACTIC-HF)                                                                                         Acute heart failure        2015-10-27  Phase 2 Phase 2 trial data released October 27, 2015. The Phase 2 trial met the objectives related to safety, tolerability, pharmacokinetics and pharmacodynamics in a population of chronic heart failure patients. The trial showed statistically significant improvements in several measures of cardiac function ejeej/EventsStockPrices      phase_b GITHUB_EVENTS_STOCK_PRICES
      GH0007   ADMS                 GOCOVRI (amantadine) Levodopa-Induced Dyskinesia + Parkinson's disease patients receiving levodopa and experiencing OFF episodes        2015-12-23  Phase 3                                                                                                                                                                                                                                                                     Phase 3 data released December 23, 2015. ejeej/EventsStockPrices      phase_b GITHUB_EVENTS_STOCK_PRICES
      GH0008   IONS                SPINRAZA (Nusinersen)                                                                               Spinal muscular atrophy (SMA)        2016-01-08  Phase 3                                                                                                                                                                                                                                                    Phase 3 ENDEAR trial met primary endpoint August 1, 2016. ejeej/EventsStockPrices      phase_b GITHUB_EVENTS_STOCK_PRICES
      GH0009   JAZZ              EPIDIOLEX (cannabidiol)                                                                 Dravet Syndrome and Lennox-Gastaut syndrome        2016-03-14  Phase 3                                                                                                                                                                                                                                          Top line Phase 3 data released March 14, 2016 met primary endpoint. ejeej/EventsStockPrices      phase_b GITHUB_EVENTS_STOCK_PRICES
      GH0010    AZN                 BEVYXXA (betrixaban)                                                                     Venous thromboembolism (VTE) Prevention        2016-03-24  Phase 3                                                                                                                                                                                                                                          Phase 3 data released March 24, 2016 did not meet primary endpoint. ejeej/EventsStockPrices      phase_b GITHUB_EVENTS_STOCK_PRICES
      GH0011   TENX                         Levosimendan                                                                                                Septic shock        2016-05-10 Phase 2b                                                                                                                                                                                                                                                                Phase 2b trial did not meet primary endpoint. ejeej/EventsStockPrices      phase_b GITHUB_EVENTS_STOCK_PRICES
      GH0012   OCUL                             DEXTENZA                                                                                     Allergic conjunctivitis        2016-06-06  Phase 3                                                                                                                                                                                                                                                  Phase 3 trial did not meet primary endpoint - June 6, 2016. ejeej/EventsStockPrices      phase_b GITHUB_EVENTS_STOCK_PRICES
      GH0013   KPTI                   XPOVIO (selinexor)                                                                       Quadruple Refractory Multiple Myeloma        2016-06-09  Phase 2                                                                                                                                                                                                                                                    Phase 2 positive top-line data released September 6, 2016 ejeej/EventsStockPrices      phase_b GITHUB_EVENTS_STOCK_PRICES
      GH0014   TNXP                  Tonmya (TNX-102 SL)                                                                                                Fibromyalgia        2016-06-09  Phase 3                                                                                                                                                                                                                      Phase 3 data released September 6, 2016. Primary endpoint not met. Program discontinued ejeej/EventsStockPrices      phase_b GITHUB_EVENTS_STOCK_PRICES
      GH0015   RVNC                         DAXI (RT002)                                                                         Lateral Canthal (Crow’s Feet) Lines        2016-06-13  Phase 3                                                                                                                                                                                                                                                                     Phase 3 endpoints not met June 13, 2016. ejeej/EventsStockPrices      phase_b GITHUB_EVENTS_STOCK_PRICES