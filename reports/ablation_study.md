# Ablation Study: Expected CAR Models

Compares market-only, market+preclinical, and Wong prior baselines.

                             model          split   n  correlation  mean_expected_car  mean_realized_car
                       market_only      in_sample 111     0.638833          -0.044295          -0.031228
                 market_plus_trial      in_sample 111     0.638833          -0.044295          -0.031228
           market_plus_preclinical      in_sample 111     0.645549          -0.043911          -0.031228
market_plus_trial_plus_preclinical      in_sample 111     0.645549          -0.043911          -0.031228
                        wong_prior      in_sample 111     0.030617          -0.086207          -0.031228
                       market_only locked_holdout  15     0.109451          -0.039850           0.001899
                 market_plus_trial locked_holdout  15     0.109451          -0.039850           0.001899
           market_plus_preclinical locked_holdout  15     0.117513          -0.041237           0.001899
market_plus_trial_plus_preclinical locked_holdout  15     0.117513          -0.041237           0.001899
                        wong_prior locked_holdout  15     0.067813          -0.047263           0.001899
