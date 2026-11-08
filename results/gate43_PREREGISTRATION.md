# Gate 43 pre-registration — discovery-only horizon selection

Frozen before execution. Gate 42 selects the horizon on validation. This gate
selects it without touching validation or assessment, using inner cross-validation
inside discovery.

## Objective

For each horizon, fit the full pipeline inside 5 discovery folds and compute the
mean one-sided 95% lower confidence bound of the selected rule on the held-out
fold. Choose the horizon with the highest mean LCB subject to:

1. at least 100 events by the horizon;
2. at least 30% of discovery still at risk;
3. selected support ≥ 60.

## Grid

365 to 1,095 days in 30-day steps (25 horizons).

## Design

| item | value |
|---|---|
| discovery | 527 patients |
| folds | 5, stratified by treatment, seed 2024 |
| nuisance | per-arm Cox + conditional censoring Cox, fitted inside each fold |
| learner | depth-3 CART, leaf 60 |
| selection | max mean with support ≥ 200; fallback flagged |
| interval | one-sided 95% LCB on the held-out fold |

Validation and assessment are not used to choose the horizon. After selection,
the chosen horizon is evaluated once on validation and once on assessment.

## Decision rule

Adopt the inner-CV optimum only if its mean LCB exceeds the 730-day mean LCB by at
least 0.02 and it satisfies the three constraints. Otherwise retain 730 and report
that the data do not support a material improvement. Assessment is descriptive.
