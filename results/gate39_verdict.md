# Gate 39 verdict — learned stacking does not beat Cox; equal-weight stays a sensitivity

Pre-registration: `results/gate39_PREREGISTRATION.md`. 10 seeds per DGP; base
models Cox, 50-tree RSF, 30-estimator GBM; positive weights fitted on discovery
out-of-fold predictions.

## Result

| DGP | estimator | MAE | purity | capture | commit | assessment MAE |
|---|---|---|---|---|---|---|
| single | **Cox** | 0.0505 | 0.844 | 0.560 | 80% | **0.0524** |
| single | equal weight | **0.0467** | **0.885** | 0.524 | 80% | 0.0561 |
| single | learned | 0.0513 | 0.869 | 0.551 | 80% | 0.0539 |
| two | **Cox** | 0.0573 | 0.817 | 0.413 | 80% | 0.0692 |
| two | equal weight | **0.0509** | 0.817 | 0.413 | 90% | **0.0689** |
| two | learned | 0.0573 | 0.817 | 0.413 | 90% | 0.0695 |

Paired vs Cox:

| DGP | estimator | ΔMAE [95% CI] | p | Δpurity | Δcapture |
|---|---|---|---|---|---|
| single | equal | −0.0038 [−0.0048, −0.0027] | <0.001 | +0.041 | −0.036 |
| single | learned | +0.0007 [−0.0008, +0.0028] | 0.424 | +0.024 | −0.009 |
| two | equal | −0.0064 [−0.0074, −0.0054] | <0.001 | 0.000 | 0.000 |
| two | learned | +0.0001 [−0.0016, +0.0022] | 0.958 | 0.000 | 0.000 |

Mean weights: Cox 0.77, RSF 0.14, GBM 0.09 (single); Cox 0.76, RSF 0.23, GBM
0.02 (two). The meta-learner puts most weight on Cox, so the learned stack is
nearly identical to Cox and adds nothing.

**Decision:** keep Cox. Reject the learned stack: its MAE difference is not
distinguishable from zero, and it does not improve purity or capture. Equal-weight
stacking lowers MAE, but in the single-region DGP it loses 0.036 capture; its
purity gain (+0.041) is a different operating point, not a dominant one. It is
reported as a sensitivity, not adopted.

**Limitation:** 10 seeds; the meta-learner is positive linear on survival
probabilities. A different meta-learner or a contrast-level stack could behave
differently.
