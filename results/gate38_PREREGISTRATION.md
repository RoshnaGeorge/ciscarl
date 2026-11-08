# Gate 38 pre-registration — feature-selection alternatives

Frozen before execution. The primary model uses the 12 published baseline
covariates for comparability with SCRE. This gate tests whether lasso or RFE
selects a feature set that improves the rule without losing interpretability.

## Alternatives

| id | feature set |
|---|---|
| `12` | the published 12 baseline covariates (primary) |
| `16` | the 12 plus `oprior`, `z30`, `preanti`, `strat` |
| `lasso` | nonzero coefficients from `LassoCV` on discovery ψ |
| `rfe` | features retained by `RFECV` on discovery ψ |

Feature selection is fitted on discovery only. The target ψ and the Cox
nuisances are then refitted on the selected columns, so the comparison is not
contaminated by using the full-data ψ.

## Design

| item | value |
|---|---|
| cohort | ACTG175 arms 0/1, n = 1,054 |
| split | 527 / 263 / 264, A×E, seeds 2024/2025 |
| nuisance | per-arm Cox + conditional censoring Cox, 5-fold |
| learner | depth-3 CART, leaf 60 |
| selection | max discovery mean with support ≥ 200; fallback flagged |
| commitment | validation LCB > 0 |

## Outcomes

1. Selected features and resulting rule.
2. Discovery support.
3. Validation effect, SE and LCB.
4. Assessment effect (descriptive).
5. Number of conditions.

## Decision rule

Adopt an alternative only if **all** hold:

1. validation SE improves by at least 0.02, or support reaches ≥ 200 without a
   fallback;
2. the rule has at most three conditions;
3. the selected features remain clinically interpretable.

Otherwise keep the 12 covariates for comparability. Assessment is not used to
choose the feature set.
