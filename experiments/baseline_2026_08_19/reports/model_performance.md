# Model Performance Report

## Expected CAR framework

```
Expected CAR = P(success) × E(CAR|success) + (1 − P(success)) × E(CAR|failure)
```

## In-sample (107 catalysts with CAR + market features)

- N: 107
- Mean realized CAR [-1,+1]: -0.0284
- Mean expected CAR: -0.0419
- Corr(expected, realized): 0.6217269033859765

## Baseline comparison (in-sample)

- Wong prior corr(expected, realized): 0.0132
- Full model corr(expected, realized): 0.6217

## Walk-forward OOS

- n_oos: 69
- mean_realized_car_all: -0.035543438428991124
- mean_realized_car_long: -0.0289237597425633
- mean_realized_car_short: -0.030932056992916426
- correlation_expected_realized: 0.1131554028567953
- n_long_signals: 24
- n_short_signals: 13

## Conditional CAR by outcome (realized, descriptive)

                  count      mean    median
clinical_success                           
0                    27 -0.104766 -0.008537
1                    80 -0.002656  0.004521

## Notes

- Models B/C use Ridge on pre-catalyst market features only (Stage 5).
- P(success) uses logistic on same features (Model A provisional).
- Holdout years 2019–2021 reserved per config; see holdout_evaluation.md.
- Priced sample: 107/112 catalysts with event-study CAR.