# Gate 40 pre-registration — SCRE full alpha path

Frozen before execution. The head-to-head uses one SCRE alpha path chosen by
validation concordance. This gate measures whether the comparator conclusion is
sensitive to that choice.

## Design

| item | value |
|---|---|
| n | 8,000 |
| partitions | 4,000 discovery / 2,000 validation / 2,000 assessment |
| replications | 10 fresh seeds per DGP, 960100–960109 |
| DGPs | single-region and two-region |
| comparator | SCRE fitted on discovery, alpha path from the Coxnet solution |
| alpha grid | 12 quantiles of the fitted path |
| metrics | MAE, purity, capture, per-treated benefit, coverage, number of rules |

For each replication the SCRE model is fitted once; every alpha on the path is
then evaluated on the same assessment patients. The validation-concordance alpha
is marked so the selected operating point can be compared with the path.

## Decision rule

No model change. If the validation-concordance alpha is far from the best-MAE
alpha, or the path spans materially different purity/capture values, the
head-to-head is reported as path-sensitive and the limitation is added.

## Scope

One SCRE implementation, two DGPs, one assessment partition per replication.
This is a sensitivity analysis of the comparator, not a new method.
