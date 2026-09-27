# Robustness Tests (Short Top 20% Strategy)

N trades: **15**

## Bootstrap

- n: 15
- observed_mean: 0.17663808125438257
- bootstrap_ci_95: (0.04006762850001127, 0.3363245463240053)
- p_mean_positive: 0.9974
- permutation_p_value: 0.0185
- t_stat: 2.2435771288914306
- ttest_p_value: 0.0415539379878902

## Year-block bootstrap

- n_years: 7
- n_obs: 15
- block_bootstrap_ci_95: (0.001361493540141781, 0.3847449373009536)
- p_mean_positive: 0.978

## Winsorized / trimmed means

- cap_50pct: 0.1304
- cap_30pct: 0.0904
- cap_20pct: 0.0648
- trimmed_mean_10pct: 0.1457268979291128

## Leave-one-out (largest winner removed)

- Largest winner return: 0.8439
- Mean without: 0.1290
- Delta: -0.0477

### Full LOO table

 dropped_index                 label  dropped_return  mean_without  delta_mean
             0         larotrectinib        0.087200      0.183026    0.006388
             1          cabozantinib        0.080116      0.183533    0.006894
             2   ORILISSA (Elagolix)        0.007862      0.188694    0.012055
             3 sacituzumab govitecan        0.285280      0.168878   -0.007760
             4            pacritinib        0.843858      0.128979   -0.047659
             5                Ampion        0.698348      0.139373   -0.037265
             6            enasidenib       -0.088737      0.195593    0.018955
             7          blinatumomab       -0.004365      0.189567    0.012929
             8 glembatumumab vedotin        0.650746      0.142773   -0.033865
             9            ivosidenib        0.000666      0.189208    0.012569
            10           quizartinib       -0.066663      0.194017    0.017379
            11             tepotinib       -0.003234      0.189486    0.012848
            12           plitidepsin        0.193798      0.175412   -0.001226
            13            pelareorep       -0.032571      0.191582    0.014944
            14          cabozantinib       -0.002734      0.189450    0.012812

## Slippage stress

 slippage_bps  n  mean_short_return                                       ci_95  win_rate
           25 15           0.176638  (0.03972859437984539, 0.33847625460690456)  0.600000
           50 15           0.171638   (0.0347285943798454, 0.33347625460690455)  0.533333
          100 15           0.161638 (0.024728594379845384, 0.32347625460690455)  0.466667
          200 15           0.141638 (0.0047285943798453765, 0.3034762546069046)  0.466667

## Era splits

             era  n  mean_short_return                                         ci_95  win_rate
 early_2010_2016  6           0.333777     (0.09196689131426432, 0.5812647204003968)  1.000000
middle_2017_2020  7           0.097459   (-0.03968850968216179, 0.29337149782936484)  0.428571
  late_2021_plus  2          -0.017653 (-0.03257113529393225, -0.002734242587007974)  0.000000