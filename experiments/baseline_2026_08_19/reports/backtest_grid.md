# Backtest Grid Report

## Bootstrap significance (walk-forward OOS, default slippage)

- observed_mean: 0.011188783289537072
- p_value: 0.346
- significant_05: False
- ci_95: (-0.0404531253639186, 0.06612902318535725)

## Slippage sensitivity

 n_trades  win_rate  mean_return_per_trade                           mean_return_ci_95  median_return_per_trade  total_return_equal_weight  sharpe_approx  long_mean  short_mean              strategy  slippage_bps
       45  0.533333               0.016189   (-0.0355252346390011, 0.0689724742585822)                 0.003029                   0.728495       0.092723  -0.028924    0.067746 walkforward_threshold             0
       45  0.466667               0.011189 (-0.040525234639001095, 0.0639724742585822)                -0.001971                   0.503495       0.064085  -0.033924    0.062746 walkforward_threshold            25
       45  0.377778               0.006189  (-0.04552523463900109, 0.0589724742585822)                -0.006971                   0.278495       0.035447  -0.038924    0.057746 walkforward_threshold            50
       45  0.355556               0.001189  (-0.05052523463900109, 0.0539724742585822)                -0.011971                   0.053495       0.006809  -0.043924    0.052746 walkforward_threshold            75
       45  0.288889              -0.003811 (-0.055525234639001095, 0.0489724742585822)                -0.016971                  -0.171505      -0.021829  -0.048924    0.047746 walkforward_threshold           100

## Strategy variants

 n_trades  win_rate  mean_return_per_trade                             mean_return_ci_95  median_return_per_trade  total_return_equal_weight  sharpe_approx  long_mean  short_mean              strategy   param
       45  0.466667               0.011189   (-0.040525234639001095, 0.0639724742585822)                -0.001971                   0.503495       0.064085  -0.033924    0.062746 walkforward_threshold default
       22  0.590909              -0.024085   (-0.10452477646969262, 0.02441209141667375)                 0.002790                  -0.529870      -0.155857  -0.063890    0.015720            long_top_k     k=1
       50  0.380000               0.002456  (-0.037009151276700014, 0.04220923213090479)                -0.005423                   0.122777       0.017392  -0.045567    0.031889            long_top_k     k=3
       66  0.348485              -0.001847 (-0.029432685177656716, 0.026846693838494945)                -0.008642                  -0.121883      -0.014907  -0.037387    0.015924            long_top_k     k=5
       14  0.714286               0.098845 (-5.716846363259197e-05, 0.22771092156074102)                 0.029969                   1.383835       0.413172  -0.123042    0.115914             threshold  min=5%
        8  0.875000               0.081663    (0.01880143944261172, 0.16098470295784506)                 0.063648                   0.653302       0.718978        NaN    0.081663             threshold min=10%
        5  0.800000               0.066441  (-0.024870686182306468, 0.17771475554716598)                 0.013526                   0.332207       0.485821        NaN    0.066441             threshold min=15%