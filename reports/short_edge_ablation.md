# Short-Edge Feature Ablation

Compares OOS short strategy performance across predefined feature sets.
No hyperparameter tuning on test outcomes.

## OOS short returns by feature set

              feature_set        strategy  n_trades  mean_short_return  win_rate  hit_rate_car_below_10pct
            clinical_only short_top_10pct         8           0.024581  0.625000                  0.250000
            clinical_only short_top_20pct        15           0.084853  0.600000                  0.266667
     clinical_plus_market short_top_10pct         8           0.040022  0.625000                  0.250000
     clinical_plus_market short_top_20pct        15           0.069472  0.600000                  0.266667
             company_only short_top_10pct         8           0.115624  0.500000                  0.250000
             company_only short_top_20pct        15           0.126987  0.666667                  0.266667
               everything short_top_10pct         8           0.059898  0.750000                  0.375000
               everything short_top_20pct        15           0.075990  0.600000                  0.266667
everything_no_preclinical short_top_10pct         8           0.031602  0.625000                  0.250000
everything_no_preclinical short_top_20pct        15           0.075990  0.600000                  0.266667
              market_only short_top_10pct         8           0.159109  0.750000                  0.375000
              market_only short_top_20pct        15           0.126746  0.600000                  0.333333
      market_plus_company short_top_10pct         8           0.137616  0.625000                  0.250000
      market_plus_company short_top_20pct        15           0.133150  0.666667                  0.333333
         preclinical_only short_top_10pct         8           0.124408  0.625000                  0.250000
         preclinical_only short_top_20pct        15           0.129138  0.666667                  0.333333