# Gate 44 pre-registration — horizon stability across splits

Frozen before execution. Gates 42 and 43 disagree: validation LCB favours 965,
discovery-only inner CV favours 845, and 730 is the clinical default. One split
cannot choose between them. This gate repeats the comparison over 20 random A×E
splits.

## Candidates

730 (clinical), 845 (discovery-inner-CV optimum), 965 (validation-LCB optimum).

## Design

| item | value |
|---|---|
| splits | 20 random 50/25/25 A×E splits, seeds 2024–2043 |
| cohort | ACTG175 arms 0/1, n = 1,054 |
| nuisance | per-arm Cox + conditional censoring Cox, 5-fold |
| learner | depth-3 CART, leaf 60 |
| selection | max discovery mean with support ≥ 200; fallback flagged |
| metric | validation one-sided 95% LCB; assessment descriptive |

## Decision rule

Replace 730 only if a candidate has a higher **mean validation LCB** by at least
0.02 across the 20 splits and its mean assessment effect remains positive.
Otherwise keep 730 and report the candidate difference as within split
variability.

This is a stability check, not a new model. No assessment value is used to
select the horizon.
