# Gate 37 pre-registration — horizon selection

Frozen before execution. The frozen pipeline uses 730 days. This gate tests
whether 365, 548, 730, 912 or 1,095 days is the defensible horizon on ACTG175,
using discovery/validation evidence only. The assessment partition is not used
to choose the horizon.

## Question

At which horizon does the rule have enough events, enough patients still at
risk, an estimable support, and acceptable validation precision?

## Design

| item | value |
|---|---|
| cohort | ACTG175 arms 0/1, n = 1,054 |
| split | 527 / 263 / 264, A×E strata, seeds 2024/2025 |
| horizons | 365, 548, 730, 912, 1,095 days |
| nuisances | per-arm Cox + conditional censoring Cox, 5-fold, discovery only |
| target | AIPW ψ at each horizon |
| learner | depth-3 CART, leaf 60 |
| selection | max discovery mean with support ≥ 200; fallback flagged |
| commitment | validation one-sided 95% LCB > 0 |

## Outcomes

1. Events observed by the horizon and fraction still at risk.
2. Discovery support of the selected rule.
3. Validation effect, SE and LCB.
4. Assessment effect (descriptive only; not used to select).
5. Rule text and number of conditions.

## Decision rule

Retain 730 unless another horizon satisfies **all** of:

1. at least 150 events by the horizon;
2. at least 30% of the cohort still at risk;
3. validation SE no worse than the 730-day SE + 0.02;
4. support ≥ 200, or a documented fallback with support ≥ 60.

If no horizon satisfies all four, 730 is retained on clinical relevance (two
years) and the limitations are reported.

## Scope

One dataset, one split, one learner. This selects a horizon for this estimand;
it does not claim 730 is optimal for other diseases or endpoints.
