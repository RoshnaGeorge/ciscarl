# ACTG175 nuisance diagnostics

## Proportional hazards (Schoenfeld, rank transform)

 arm                        test  statistic  p_value  flag_p<0.05
   0 global (Fisher combination)    28.6103   0.2351        False
   0                        cd40        NaN   0.0210         True
   0                        cd80        NaN   0.7063        False
   0                         age        NaN   0.8938        False
   0                        wtkg        NaN   0.5146        False
   0                      karnof        NaN   0.6108        False
   0                        hemo        NaN   0.5599        False
   0                        homo        NaN   0.2887        False
   0                        race        NaN   0.4195        False
   0                      gender        NaN   0.3923        False
   0                       drugs        NaN   0.4804        False
   0                        str2        NaN   0.0220         True
   0                     symptom        NaN   0.5225        False
   1 global (Fisher combination)    25.7094   0.3681        False
   1                        cd40        NaN   0.0227         True
   1                        cd80        NaN   0.8516        False
   1                         age        NaN   0.8833        False
   1                        wtkg        NaN   0.0480         True
   1                      karnof        NaN   0.5450        False
   1                        hemo        NaN   0.7433        False
   1                        homo        NaN   0.5200        False
   1                        race        NaN   0.5311        False
   1                      gender        NaN   0.2744        False
   1                       drugs        NaN   0.1905        False
   1                        str2        NaN   0.6057        False
   1                     symptom        NaN   0.8993        False


## Cox tie handling: Efron vs Breslow

 arm  max_abs_coef_diff  mean_abs_coef_diff  corr
   0             0.0005              0.0001   1.0
   1             0.0014              0.0004   1.0


## Survival calibration at 730 days (assessment, predicted-risk bins)

 arm  bin   n  predicted  observed_km    gap
   0    0 133      0.738        0.732 -0.006
   0    1  45      0.552        0.572  0.020
   0    2  44      0.775        0.695 -0.080
   0    3  44      0.891        0.929  0.038
   1    0 131      0.872        0.859 -0.013
   1    1  44      0.773        0.689 -0.084
   1    2  43      0.893        0.974  0.081
   1    3  44      0.951        0.923 -0.028

weighted mean |gap| (ECE-like): 0.032

## Weight-cap sensitivity

 cap  pct_capped  selected_leaf  support  mean_psi  fallback  max_weight_raw     ess
 1.2       9.867              6       71     0.485      True           1.402 526.338
 1.5       0.000              2       61     0.556      True           1.402 525.975
 2.0       0.000              2       61     0.556      True           1.402 525.975
 5.0       0.000              2       61     0.556      True           1.402 525.975
20.0       0.000              2       61     0.556      True           1.402 525.975
