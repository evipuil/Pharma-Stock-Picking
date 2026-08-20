# Event Study Report

## Methodology
- Estimation window: [-250, -30] trading days
- Windows: [-5,+5], [-1,+1], [0,+1], [0,+5], [0,+20]
- Benchmarks: RAW, SPY, XBI, MARKET_MODEL, XBI_MODEL

## Success vs failure CAR (market model, [-1,+1])

 clinical_success  n  mean_car  median_car      std
                0 27 -0.104766   -0.008537 0.245388
                1 80 -0.002656    0.004521 0.051205

## Price coverage by catalyst

Total catalysts with prices: **107** / **112**
