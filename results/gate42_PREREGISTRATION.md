# Gate 42 pre-registration — horizon optimisation

Frozen before execution. Gate 37 compared five horizons and retained 730 as a
compromise. This gate searches a dense grid and defines the optimum explicitly.

## Objective

Maximise the **validation one-sided 95% lower confidence bound (LCB)** of the
selected rule, subject to:

1. at least 100 events by the horizon;
2. at least 30% of the discovery cohort still at risk;
3. selected support ≥ 60 (the documented fallback minimum).

The validation partition is the designated operating-point partition; the
assessment partition is not used for selection.

## Grid

365 to 1,095 days in 30-day steps (25 horizons).

## Design

| item | value |
|---|---|
| cohort | ACTG175 arms 0/1, n = 1,054 |
| split | 527 / 263 / 264, A×E, seeds 2024/2025 |
| nuisance | per-arm Cox + conditional censoring Cox, 5-fold, discovery |
| learner | depth-3 CART, leaf 60 |
| selection | max discovery mean with support ≥ 200; fallback flagged |
| commitment | validation one-sided 95% LCB |

## Decision rule

If at least one grid point meets the three constraints, select the one with the
highest validation LCB. If none does, retain 730 and report that no feasible
optimum exists.

The assessment effect of the selected horizon is descriptive only. Changing the
horizon is a new model, not a silent edit of the frozen 730-day result.
