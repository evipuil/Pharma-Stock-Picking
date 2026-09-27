# Short Strategy Baselines

OOS predictions: **59** catalysts
Primary model strategy: short each OOS year's top 20% by net expected short return (**15** trades)

## All baselines vs model strategies

                  baseline  n_trades  mean_short_return  median_short_return  win_rate  hit_rate_car_below_10pct  hit_rate_car_below_20pct             strategy                 score_col  precision_major_drop
       short_all_catalysts        59           0.043163            -0.009204  0.423729                  0.118644                  0.084746                  NaN                       NaN                   NaN
             short_phase_2         0                NaN                  NaN       NaN                       NaN                       NaN                  NaN                       NaN                   NaN
             short_phase_3         0                NaN                  NaN       NaN                       NaN                       NaN                  NaN                       NaN                   NaN
           short_small_cap        25           0.118313             0.007862  0.560000                  0.280000                  0.200000                  NaN                       NaN                   NaN
     short_high_dependency        25           0.118313             0.007862  0.560000                  0.280000                  0.200000                  NaN                       NaN                   NaN
     short_high_volatility        32           0.085754            -0.007797  0.468750                  0.218750                  0.156250                  NaN                       NaN                   NaN
   short_negative_momentum        20           0.098943             0.002464  0.550000                  0.200000                  0.150000                  NaN                       NaN                   NaN
              random_short        11           0.042668            -0.014457  0.181818                  0.090909                  0.090909                  NaN                       NaN                   NaN
     model_short_top_10pct         9           0.204150             0.087200  0.666667                  0.444444                  0.333333      short_top_10pct net_expected_short_return              0.333333
     model_short_top_20pct        15           0.176638             0.007862  0.600000                  0.333333                  0.266667      short_top_20pct net_expected_short_return              0.266667
       model_min_esr_10pct        12           0.153227             0.017608  0.583333                  0.333333                  0.250000        min_esr_10pct net_expected_short_return              0.250000
       model_min_esr_20pct         1           0.698348             0.698348  1.000000                  1.000000                  1.000000        min_esr_20pct net_expected_short_return              1.000000
model_major_drop_threshold         8           0.253431             0.148069  0.750000                  0.625000                  0.375000 major_drop_threshold net_expected_short_return              0.375000

## Interpretation

Model must beat `short_all_catalysts` and `short_high_dependency` to claim incremental value.