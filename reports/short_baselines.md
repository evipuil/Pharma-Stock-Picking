# Short Strategy Baselines

OOS predictions: **69** catalysts
Primary model strategy: short top 20% by net expected short return (**14** trades)

## All baselines vs model strategies

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

## Interpretation

Model must beat `short_all_catalysts` and `short_high_dependency` to claim incremental value.