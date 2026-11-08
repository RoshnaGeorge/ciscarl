# Gate 39 pre-registration — learned stacking meta-learner

Frozen before execution. Gate 31 tested equal-weight stacking. This gate tests a
learned stack: positive weights on Cox, RSF and GBM, fitted on discovery
out-of-fold predictions against the IPCW outcome.

## Design

| item | value |
|---|---|
| n | 8,000 |
| partitions | 4,000 / 2,000 / 2,000 |
| replications | 10 fresh seeds per DGP, 970100–970109 |
| DGPs | single-region and two-region |
| base models | Cox, 50-tree RSF, 30-estimator GBM |
| meta-learner | positive linear weights, normalized to sum 1 |
| target | AIPW at the stacked nuisances |
| learner | C200 |

## Outcomes

1. Patient-level MAE.
2. C200 purity, capture and commitment.
3. Assessment MAE.
4. Learned weights.

## Decision rule

Adopt the learned stack over Cox only if patient-level MAE improves by at least
0.002 with a paired CI below zero and purity/capture do not fall by more than
0.02. Adopt it over equal-weight stacking only if it improves MAE or purity
without a capture loss. Otherwise keep Cox / equal-weight and report the weights
as a sensitivity.

## Scope

Two DGPs and 10 seeds. This is a screening comparison of the meta-learner, not a
new production model.
