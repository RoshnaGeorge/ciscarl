# Gate 34 pre-registration — number of cross-fitting folds

Frozen before execution. The frozen pipeline uses 5-fold cross-fitting. This gate
tests whether 3 or 10 folds changes the AIPW estimate, its coverage or the
patient-level nuisance error.

## Design

| item | value |
|---|---|
| n | 8,000 |
| partitions | 4,000 discovery / 2,000 validation / 2,000 assessment |
| replications | 20 fresh seeds per DGP, 930100–930119 |
| DGPs | single-region and two-region effects |
| folds | 3, 5, 10 |
| nuisance | per-arm Cox + conditional censoring Cox |
| target | AIPW ψ, e = 0.5, cap min(Q0.99, 20) |

## Outcomes

1. AIPW bias against the true ATE.
2. 95% influence-function coverage.
3. Patient-level MAE of the nuisance contrast.
4. Effective sample size of the IPCW weights.
5. Wall-clock seconds.

## Decision rule

Keep 5 folds unless 3 or 10 improves patient-level MAE by at least 0.002 with a
paired 95% bootstrap CI entirely below zero, or improves coverage materially
without a width increase. A difference smaller than the Monte Carlo error is
reported as a tie.

## Scope

Two DGPs, one sample size, one censoring mechanism. This tests the fold count,
not the estimator or the learner.
