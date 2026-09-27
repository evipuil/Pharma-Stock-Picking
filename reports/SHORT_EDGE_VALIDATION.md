# Short Edge Validation Report

**Verdict: PROMISING BUT UNVALIDATED EDGE**

Generated from 59 development walk-forward OOS predictions; the legacy holdout beginning 2022-01-01 is quarantined and excluded.

## Core hypothesis

> High P(failure) × high company exposure → asymmetric downside before binary catalysts

## Point-in-time provenance

- Market feature rows verified at cutoff: 59/59
- Company feature rows verified at cutoff: 58/59
- Historical trial snapshots verified at cutoff: 0/59
- Unversioned ClinicalTrials.gov fields are excluded from strict model features; phase-stratified baselines are therefore unavailable.

## Predefined success criteria

- min_oos_short_trades: FAIL
- positive_mean: PASS
- ci_above_zero: PASS
- multi_era_positive: PASS
- beats_short_all: PASS
- beats_dependency_heuristic: PASS
- survives_100bps_slippage: PASS
- survives_remove_largest_winner: PASS

**Score: 7/8 criteria met**

## Key OOS metrics (primary strategy: each test year's top 20%)

- N short trades: 15
- Mean net short return: 0.1766
- Bootstrap 95% CI: (0.04006762850001127, 0.3363245463240053)
- Year-block bootstrap 95% CI: (0.001361493540141781, 0.3847449373009536)
- P(mean > 0): 0.9974
- Permutation p-value: 0.0185

## Event study asymmetry (descriptive, N=110)

- Failure mean CAR: -0.12021562305670959
- Success mean CAR: -0.0010230302407607786
- Welch difference p-value: 0.02762908738580355

## Model vs baselines

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

## Company dependency analysis

- Failure CAR vs enhanced dependency: {'n_failures': 18, 'correlation': -0.5352692855970222, 'p_value': 0.02207185457316241, 'interpretation': 'Higher dependency associated with more negative failure CAR'}

## Portfolio simulation (2% max per catalyst, 20% max short exposure)

- n_trades: 15
- starting_capital: 100000.0
- ending_capital: 105299.14243763145
- total_return: 0.05299142437631454
- mean_exposure: 0.02
- max_exposure: 0.02
- volatility_approx: 0.0057772717595917745
- trades_per_year: 2.378962223187147
- sharpe_approx: 0.9250216439129767
- sortino_approx: 8.243020664038601
- max_drawdown: -0.0017903247454185839

## Stratification diagnostics

               stratification            bucket  n  failure_rate  success_mean_car  failure_mean_car  short_all_mean_return                                 short_all_ci_95
       small_cap_vs_large_cap      large_or_mid 34      0.235294          0.009440         -0.000525              -0.012095  (-0.020431921382741844, -0.004249621137105596)
       small_cap_vs_large_cap         small_cap 25      0.400000         -0.015658         -0.284796               0.118313     (0.023226977716656046, 0.22983696926717534)
          lead_vs_diversified   high_dependency 25      0.400000         -0.015658         -0.284796               0.118313     (0.023226977716656046, 0.22983696926717534)
          lead_vs_diversified    low_dependency 34      0.235294          0.009440         -0.000525              -0.012095  (-0.020431921382741844, -0.004249621137105596)
           phase_2_vs_phase_3             other 59      0.305085          0.000258         -0.158453               0.043163     (0.000440507229585728, 0.09383569596409469)
momentum_positive_vs_negative  negative_or_flat 46      0.347826          0.005714         -0.135764               0.038496    (-0.007715843771244729, 0.09304114797121195)
momentum_positive_vs_negative positive_momentum 13      0.153846         -0.014623         -0.339969               0.059677    (-0.028607603325861014, 0.19225547545241972)
       high_vs_low_volatility          high_vol 32      0.375000         -0.003709         -0.235830               0.085754     (0.001616209838545895, 0.18014679849018633)
       high_vs_low_volatility           low_vol 27      0.222222          0.004035         -0.003699              -0.007317 (-0.014171513436330035, -0.0006684655159381273)
            oncology_vs_other     oncology_like 41      0.243902          0.000838         -0.130188               0.026120    (-0.011873755531203732, 0.07618932731957813)
            oncology_vs_other             other 18      0.444444         -0.001541         -0.193785               0.081982    (-0.011040027724731482, 0.21981889005459632)

## Critical finding: model vs naive heuristics

The year-local model top-20% strategy (+17.7% mean, n=15) **beats**
shorting high-dependency small-cap biotech (+11.8% mean, n=25).
The point-in-time-safe model demonstrates incremental development-sample value over this heuristic, pending a genuinely new prospective holdout.

## Sample size requirements before live stock selection

- Current development OOS short candidates: **15** (year-local top 20% of 59 OOS rows) — far below target of **≥100**
- Need **≥100 OOS short trades** (preferably ≥200) before strong claims
- Expand catalyst universe independently of outcome (oncology Ph2/3, neurology, immunology, rare disease)
- Complete 5 missing CAR observations via Polygon/EODHD/CRSP
- The legacy 2022+ holdout appeared in earlier artifacts; keep it quarantined and establish a new prospective holdout for final claims

## What was NOT done (by design)

- No threshold tuning on test-year outcomes
- No LONG signals produced
- No live stock picker until validation passes
- No retroactive optimization of baseline expected-CAR model