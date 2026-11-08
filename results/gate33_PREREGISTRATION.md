# Gate 33 pre-registration — calibration and interval comparison

Frozen before execution. The frozen model uses empirical-Bayes shrinkage for
prediction and an influence-function interval for the selected rule. This gate
tests whether isotonic calibration or a selection-aware/bootstrap/conformal
interval is better.

## Calibration methods

| id | method |
|---|---|
| `none` | validation leaf effects, no calibration |
| `shrink` | empirical-Bayes shrinkage toward the marginal (frozen C200-S) |
| `isotonic` | 5-fold out-of-fold isotonic regression of validation φ on the discovery leaf score |

## Interval methods

| id | method |
|---|---|
| `if` | influence-function interval, conditional on the selected rule (frozen) |
| `boot` | validation bootstrap percentile interval, conditional on the rule |
| `select` | selection bootstrap: resample discovery, refit CART, reselect a rule, evaluate on validation |
| `conformal` | repeated split-half conformal-style interval on validation |

## Design

| item | value |
|---|---|
| n | 8,000 |
| partitions | 4,000 discovery / 2,000 validation / 2,000 assessment |
| replications | 20 fresh seeds per DGP, 920100–920119 |
| DGPs | single-region and two-region effects |
| nuisance | frozen Cox + conditional censoring Cox, seed per replication |
| learner | frozen C200 |
| bootstrap reps | 500 for `boot`, 200 for `select` and `conformal` |

## Outcomes

1. Assessment MAE of the calibrated prediction.
2. Purity and capture of the selected rule.
3. Interval coverage of the true selected-rule effect on assessment.
4. Interval width.
5. Commitment rate.

## Decision rule (fixed)

**Calibration.** Isotonic replaces shrinkage only if assessment MAE improves by
at least 0.002 with a paired 95% bootstrap CI entirely below zero, and purity
and commitment are unchanged.

**Inference.** An interval replaces the influence-function interval only if
coverage is at least the measured 92.5% of the frozen interval, is closer to
95%, and its width is no more than 2× the frozen width. Otherwise the frozen
interval is retained and the alternative is reported as a sensitivity analysis.

## Failure interpretation

| result | interpretation |
|---|---|
| isotonic improves MAE but changes the policy | reject; calibration must not change who is treated |
| selection bootstrap is much wider | selection uncertainty is real; report it, do not hide it |
| conformal undercovers | the exchangeability assumption is not met after selection |
| no method beats the frozen interval | keep it and report the measured coverage |

## Scope

Two DGPs and one sample size. This gate does not solve selective inference in
general; it measures whether a practical correction is adequate here.
