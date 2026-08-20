# Short Edge Validation Report

**Verdict: WEAK / INCONCLUSIVE EDGE**

Generated from 69 walk-forward OOS predictions (107 priced catalysts universe).

## Core hypothesis

> High P(failure) × high company exposure → asymmetric downside before binary catalysts

## Predefined success criteria

- min_oos_short_trades: FAIL
- positive_mean: PASS
- ci_above_zero: FAIL
- multi_era_positive: PASS
- beats_short_all: PASS
- beats_dependency_heuristic: FAIL
- survives_100bps_slippage: PASS
- survives_remove_largest_winner: PASS

**Score: 5/8 criteria met**

## Key OOS metrics (primary strategy: short top 20%)

- N short trades: 14
- Mean net short return: 0.0816
- Bootstrap 95% CI: (-0.001836314591065517, 0.18787940304891093)
- P(mean > 0): 0.9698
- Permutation p-value: 0.06

## Event study asymmetry (descriptive, N=107)

- Failure mean CAR: ~-10.5%
- Success mean CAR: ~-0.27%
- Difference p ≈ 0.041

## Model vs baselines

                  baseline  n_trades  mean_short_return  median_short_return  win_rate  hit_rate_car_below_10pct  hit_rate_car_below_20pct             strategy                 score_col  precision_major_drop
       short_all_catalysts        69           0.030543            -0.008029  0.391304                  0.101449                  0.057971                  NaN                       NaN                   NaN
             short_phase_2        49           0.029645            -0.012510  0.408163                  0.102041                  0.040816                  NaN                       NaN                   NaN
             short_phase_3         3           0.015992            -0.008563  0.333333                  0.000000                  0.000000                  NaN                       NaN                   NaN
           short_small_cap        22           0.119508             0.016683  0.636364                  0.318182                  0.181818                  NaN                       NaN                   NaN
     short_high_dependency        22           0.119508             0.016683  0.636364                  0.318182                  0.181818                  NaN                       NaN                   NaN
     short_high_volatility        31           0.076470            -0.007926  0.451613                  0.225806                  0.129032                  NaN                       NaN                   NaN
   short_negative_momentum        23           0.085888            -0.002004  0.434783                  0.217391                  0.130435                  NaN                       NaN                   NaN
              random_short        13           0.082554            -0.006480  0.384615                  0.153846                  0.153846                  NaN                       NaN                   NaN
     model_short_top_10pct         7           0.071253             0.040096  0.714286                  0.428571                  0.142857      short_top_10pct net_expected_short_return              0.142857
     model_short_top_20pct        14           0.081603             0.016683  0.642857                  0.285714                  0.142857      short_top_20pct net_expected_short_return              0.142857
       model_min_esr_10pct         8           0.064826             0.029968  0.750000                  0.375000                  0.125000        min_esr_10pct net_expected_short_return              0.125000
       model_min_esr_20pct         4          -0.005101            -0.026569  0.500000                  0.250000                  0.000000        min_esr_20pct net_expected_short_return              0.000000
model_major_drop_threshold         6           0.188832             0.029968  0.833333                  0.333333                  0.333333 major_drop_threshold net_expected_short_return              0.333333

## Company dependency analysis

- Failure CAR vs enhanced dependency: {'n_failures': 17, 'correlation': -0.5141289730123771, 'p_value': 0.03474547436008576, 'interpretation': 'Higher dependency associated with more negative failure CAR'}

## Portfolio simulation (2% max per catalyst, 20% max short exposure)

- n_trades: 14
- starting_capital: 100000.0
- ending_capital: 102284.88809591572
- total_return: 0.02284888095915725
- mean_exposure: 0.019999999999999997
- max_exposure: 0.02
- volatility_approx: 0.0037299976358213124
- sharpe_approx: 6.945901386886686
- sortino_approx: 41.39016998366543
- max_drawdown: -0.001759928821501652

## Stratification diagnostics

               stratification            bucket  n  failure_rate  success_mean_car  failure_mean_car  short_all_mean_return                                 short_all_ci_95
       small_cap_vs_large_cap      large_or_mid 47      0.170213          0.007226          0.000605              -0.011099 (-0.018615032550126767, -0.0029304269663977755)
       small_cap_vs_large_cap         small_cap 22      0.409091         -0.032272         -0.257737               0.119508     (0.027247510967909755, 0.23009294390156396)
          lead_vs_diversified   high_dependency 22      0.409091         -0.032272         -0.257737               0.119508     (0.027247510967909755, 0.23009294390156396)
          lead_vs_diversified    low_dependency 47      0.170213          0.007226          0.000605              -0.011099 (-0.018615032550126767, -0.0029304269663977755)
           phase_2_vs_phase_3             other 17      0.176471         -0.011417         -0.177367               0.035702    (-0.022302083269255556, 0.12314986090665202)
           phase_2_vs_phase_3           phase_2 49      0.265306          0.002601         -0.137787               0.029645    (-0.006562448155647513, 0.08211966273781397)
           phase_2_vs_phase_3           phase_3  3      0.333333         -0.035755          0.008534               0.015992    (-0.013533820253623902, 0.07007309447329159)
momentum_positive_vs_negative  negative_or_flat 53      0.283019          0.003102         -0.152874               0.036042   (-0.0035571403129461034, 0.08418140969243827)
momentum_positive_vs_negative positive_momentum 16      0.125000         -0.018255         -0.010843               0.012328   (-0.021684755253337473, 0.060466910859507374)
       high_vs_low_volatility          high_vol 31      0.387097         -0.011628         -0.192053               0.076470      (0.00913068339055442, 0.16153752501137023)
       high_vs_low_volatility           low_vol 38      0.131579          0.002522         -0.002032              -0.006923  (-0.014267792510467368, 0.0004726729139889935)
            oncology_vs_other     oncology_like 50      0.200000          0.000023         -0.130188               0.021019     (-0.008467159970322066, 0.0657335299085836)
            oncology_vs_other             other 19      0.368421         -0.011553         -0.144702               0.055608   (-0.0034396046913005504, 0.15219857678289314)

## Sample size requirements before live stock selection

- Current OOS short candidates: **~14** (top 20% of 69 OOS rows) — far below target of **≥100**
- Need **≥100 OOS short trades** (preferably ≥200) before strong claims
- Expand catalyst universe independently of outcome (oncology Ph2/3, neurology, immunology, rare disease)
- Complete 5 missing CAR observations via Polygon/EODHD/CRSP
- Locked final holdout (2022+) must remain untouched until methodology frozen

## What was NOT done (by design)

- No threshold tuning on test-year outcomes
- No LONG signals produced
- No live stock picker until validation passes
- No retroactive optimization of baseline expected-CAR model