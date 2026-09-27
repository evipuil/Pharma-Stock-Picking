# Event Study Report

## Methodology
- Estimation window: [-250, -30] trading days
- Windows: [-5,+5], [-1,+1], [0,+1], [0,+5], [0,+20]
- Benchmarks: RAW, SPY, XBI, MARKET_MODEL, XBI_MODEL

## Success vs failure CAR (market model, [-1,+1])

 clinical_success  n  mean_car  median_car      std
              0.0 28 -0.120216   -0.009098 0.269563
              1.0 83 -0.002202    0.004347 0.050713

## Price coverage by catalyst

Total catalysts with prices: **115** / **122**
