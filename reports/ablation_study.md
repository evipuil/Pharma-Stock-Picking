# Ablation Study: Expected CAR Models

Compares market-only, market+preclinical, and Wong prior baselines.

                             model          split  n  correlation  mean_expected_car  mean_realized_car
                       market_only      in_sample 68     0.544133          -0.007420          -0.008240
                 market_plus_trial      in_sample 68     0.700016          -0.007746          -0.008240
           market_plus_preclinical      in_sample 68     0.569747          -0.007563          -0.008240
market_plus_trial_plus_preclinical      in_sample 68     0.715902          -0.007868          -0.008240
                        wong_prior      in_sample 68     0.187072          -0.012970          -0.008240
                       market_only locked_holdout  9     0.746785          -0.005015          -0.010552
                 market_plus_trial locked_holdout  9     0.736580          -0.005624          -0.010552
           market_plus_preclinical locked_holdout  9     0.742181          -0.005355          -0.010552
market_plus_trial_plus_preclinical locked_holdout  9     0.739076          -0.005457          -0.010552
                        wong_prior locked_holdout  9     0.431143          -0.008242          -0.010552
