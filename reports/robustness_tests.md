# Robustness Tests (Short Top 20% Strategy)

N trades: **14**

## Bootstrap

- n: 14
- observed_mean: 0.08160314628270433
- bootstrap_ci_95: (-0.001836314591065517, 0.18787940304891093)
- p_mean_positive: 0.9698
- permutation_p_value: 0.06
- t_stat: 1.5776113386017963
- ttest_p_value: 0.13866934850308188

## Winsorized / trimmed means

- cap_50pct: 0.0708
- cap_30pct: 0.0565
- cap_20pct: 0.0433
- trimmed_mean_10pct: 0.048369537955192395

## Leave-one-out (largest winner removed)

- Largest winner return: 0.6507
- Mean without: 0.0378
- Delta: -0.0438

### Full LOO table

 dropped_index                     label  dropped_return  mean_without  delta_mean
             0             larotrectinib        0.087201      0.081173   -0.000431
             1     sacituzumab govitecan        0.285280      0.065936   -0.015667
             2               epacadostat       -0.013534      0.088921    0.007318
             3 mirvetuximab soravtansine       -0.069606      0.093235    0.011631
             4                umbralisib        0.102340      0.080008   -0.001595
             5              lenalidomide        0.019841      0.086354    0.004751
             6              tazemetostat        0.013526      0.086840    0.005237
             7                enasidenib       -0.088736      0.094706    0.013103
             8     glembatumumab vedotin        0.650746      0.037823   -0.043780
             9                ivosidenib        0.000666      0.087829    0.006226
            10               quizartinib       -0.066663      0.093008    0.011405
            11               plitidepsin        0.193798      0.072973   -0.008630
            12                pelareorep        0.040096      0.084796    0.003193
            13                lenvatinib       -0.012510      0.088843    0.007239

## Slippage stress

 slippage_bps  n  mean_short_return                                         ci_95  win_rate
           25 14           0.081603 (-0.0013792287885237044, 0.19533202901052749)  0.642857
           50 14           0.076603  (-0.0063792287885236975, 0.1903320290105274)  0.571429
          100 14           0.066603    (-0.0163792287885237, 0.18033202901052742)  0.500000
          200 14           0.046603    (-0.0363792287885237, 0.16033202901052743)  0.428571

## Era splits

             era  n  mean_short_return                                        ci_95  win_rate
 early_2010_2016  7           0.060721 (-0.014372662402933082, 0.14111926178834427)  0.714286
middle_2017_2020  5           0.137962  (-0.062026664653783446, 0.3772481830531136)  0.600000
  late_2021_plus  2           0.013793      (-0.012509591379344, 0.040095714263386)  0.500000