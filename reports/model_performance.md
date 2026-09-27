# Model Performance Report

## Expected CAR framework

```
Expected CAR = P(success) × E(CAR|success) + (1 − P(success)) × E(CAR|failure)
```

## In-sample (111 catalysts with CAR + market features)

- N: 111
- Mean realized CAR [-1,+1]: -0.0312
- Mean expected CAR: -0.0443
- Corr(expected, realized): 0.6388332936804804

## Baseline comparison (in-sample)

- Wong prior corr(expected, realized): 0.0306
- Full model corr(expected, realized): 0.6388

## Walk-forward OOS

- n_oos: 73
- mean_realized_car_all: -0.039419936942594
- mean_realized_car_long: -0.023719114406583797
- mean_realized_car_short: -0.07144241203609795
- correlation_expected_realized: 0.3315850193135733
- n_long_signals: 24
- n_short_signals: 13

## Conditional CAR by outcome (realized, descriptive)

                  count      mean    median
clinical_success                           
0                    28 -0.120216 -0.009097
1                    83 -0.001208  0.004204

## Notes

- Models B/C use Ridge on pre-catalyst market features only (Stage 5).
- P(success) uses logistic on same features (Model A provisional).
- The 2019–2021 period is a legacy evaluation, not a pristine holdout; see holdout_evaluation.md.
- Priced sample: 111/112 catalysts with event-study CAR.