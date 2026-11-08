# Gate 31 pre-registration — outcome-nuisance comparison for AIPW

Frozen before execution. This gate closes the largest remaining evidence gap:
Cox has never been compared with flexible survival nuisances on identical folds,
judged by the downstream causal target rather than by survival fit alone.

## Question

Does replacing the per-arm Cox outcome model with a flexible survival model
improve the AIPW patient-level contrast, its uncertainty, and the downstream
C200 subgroup, on the same data and folds?

## Models

| id | outcome nuisance | specification |
|---|---|---|
| `cox` | per-arm Cox PH | frozen; lifelines, penaliser searched over 0.01–10 |
| `rsf` | random survival forest | sksurv, 100 trees, max_depth 5, min_samples_leaf 10 |
| `gbm` | survival gradient boosting | sksurv, 60 estimators, learning_rate 0.1, max_depth 2 |
| `stack` | equal-weight stacking | mean of the Cox, RSF and GBM survival probabilities |

The censoring model is held fixed at the conditional Cox used by the frozen
pipeline. Only the outcome nuisance changes, so any difference is attributable
to that layer.

## Design

| item | value |
|---|---|
| n | 8,000 |
| partitions | 4,000 discovery / 2,000 validation / 2,000 assessment |
| replications | 5 fresh seeds per DGP, 900100–900104 (screening) |
| DGPs | single-region and two-region treatment effects |
| folds | 5, identical fold assignment for every model |
| target | AIPW ψ, e = 0.5, cap min(Q0.99, 20) |
| learner | frozen C200: depth 3, min_leaf 60, support ≥ 200 |
| commitment | one-sided 95% LCB > 0 |

## Outcomes (paired within replication)

1. **AIPW bias**: τ̂ − true ATE on discovery.
2. **AIPW coverage**: 95% influence-function interval contains the true ATE.
3. **Patient-level MAE**: mean |μ̂₁ − μ̂₀ − τ_true| on discovery.
4. **Survival Brier at 730**: mean squared error of μ̂_a against the true
   S_a(730 | X), both arms.
5. **Downstream C200**: purity, capture, Jaccard, commitment, assessment MAE.
6. **Cost**: wall-clock seconds per replication.

## Decision rule (fixed)

A flexible model replaces Cox only if **all** of the following hold:

1. patient-level MAE improves by at least 0.002 with a paired 95% bootstrap CI
   entirely below zero, **or** absolute AIPW bias falls by at least 50% and
   coverage moves closer to 95%;
2. C200 purity does not fall by more than 0.02;
3. C200 capture does not fall by more than 0.02;
4. wall-clock cost is at most 5× the Cox arm.

Otherwise Cox is retained. The comparison is Holm-adjusted across the three
alternatives on the primary metric (patient-level MAE).

## Failure interpretation

| result | interpretation |
|---|---|
| flexible model wins on MAE and not on downstream C200 | nuisance accuracy is not the binding constraint; keep the simpler model |
| flexible model wins on AIPW bias but loses calibration | do not trade calibration for a nominal bias gain |
| no model beats Cox | the linear predictor is adequate for this DGP; report the negative result |
| only stacking wins at high cost | document the cost–benefit; do not adopt automatically |

## Compute note

An early 20-seed attempt was throttled by the machine and produced no usable
result. A 2-seed pilot was run to check the interface. The **full pre-registered
20-seed run with 100-tree RSF and 60-estimator GBM was subsequently completed**;
the full result is the one reported in `gate31_verdict.md`.

## Design as executed

| item | value |
|---|---|
| replications | 20 seeds per DGP, 900100–900119 |
| RSF | 100 trees, max_depth 5, min_samples_leaf 10 |
| GBM | 60 estimators, learning_rate 0.1, max_depth 2 |
| cost | measured as discovery cross-fit seconds |

## Scope

Two DGPs, one sample size, one censoring mechanism. This gate does not test
transportability, unmeasured confounding or non-Cox censoring.
