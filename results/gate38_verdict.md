# Gate 38 verdict — keep the 12 published covariates

Pre-registration: `results/gate38_PREREGISTRATION.md`. ACTG175, feature selection
fitted on discovery only.

| Method | Features | Support | Fallback | Val. effect | Val. SE | Val. LCB | Rule |
|---|---|---|---|---|---|---|---|
| 12 | 12 | 61 | yes | +0.116 | 0.222 | −0.250 | `cd40 ≤ 407.5 & wtkg > 71.0 & homo ≤ 0.5` |
| 16 | 16 | 61 | yes | +0.110 | 0.223 | −0.256 | identical |
| lasso | 12 | 61 | yes | +0.116 | 0.222 | −0.250 | identical |
| RFE | 11 | 79 | yes | +0.148 | 0.180 | −0.148 | `cd80 > 805.5 & race > 0.5` |

Lasso selects all 12 features, so it changes nothing. RFE drops `age`, replaces
the rule and falls to support 79 (<200, fallback). Its validation SE is smaller,
but the rule is a different subgroup below the support floor.

**Decision:** keep the 12 published covariates for comparability and
interpretability. Report RFE as a sensitivity, not an adopted feature set.
