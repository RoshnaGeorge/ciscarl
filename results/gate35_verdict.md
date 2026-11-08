# Gate 35 verdict — fairness, SHAP and internal transport are descriptive, not confirmatory

Pre-registration: `results/gate35_PREREGISTRATION.md`. Frozen C200 on the A×E
split (527/263/264, seeds 2024/2025). The main rule reproduces the canonical
result: `cd40 ≤ 407.5 & wtkg > 71.0 & homo ≤ 0.5`, discovery support 61,
validation +0.116 (LCB −0.250) → **INSUFFICIENT**, assessment +0.401
[+0.102, +0.700] on 38 patients.

## Group rule effects (assessment)

| group | n | rule n | rule prevalence | effect | 95% CI | positive LCB | powered |
|---|---|---|---|---|---|---|---|
| white | 183 | 24 | 13.1% | +0.444 | [+0.081, +0.807] | yes | **no** |
| non-white | 81 | 14 | 17.3% | +0.328 | [−0.191, +0.847] | no | **no** |
| male | 213 | 25 | 11.7% | +0.514 | [+0.147, +0.881] | yes | **no** |
| female | 51 | 13 | 25.5% | +0.184 | [−0.318, +0.686] | no | **no** |

Every group has fewer than 30 rule patients. The intervals overlap
substantially. **No claim of fairness or harm is made.** The female and
non-white estimates are consistent with the overall effect but too imprecise to
separate from zero.

## Group calibration at 730

| group | predicted S0 / observed | predicted S1 / observed | ECE |
|---|---|---|---|
| white | 0.724 / 0.744 | 0.861 / 0.835 | 0.023 |
| non-white | 0.764 / 0.711 | 0.903 / 0.929 | 0.040 |
| male | 0.713 / 0.712 | 0.863 / 0.864 | 0.001 |
| female | 0.830 / 0.808 | 0.918 / 0.824 | 0.058 |

Calibration is good overall; the female stratum is the worst (ECE 0.058, n = 51)
and is the one group where the treated-arm survival is over-predicted by 0.094.

## SHAP (surrogate, supplementary)

A RandomForestRegressor surrogate for ψ ranks `wtkg` (0.048), `cd40` (0.046),
`cd80` (0.042), `str2` (0.017) and `homo` (0.011) as the top five. The rule uses
`wtkg`, `cd40` and `homo`; the surrogate is consistent with the rule, not a
replacement for it. SHAP is not used to select or justify the rule.

## Internal transport (white → non-white)

| training | evaluation | n | support | effect | 95% CI |
|---|---|---|---|---|---|
| white | white assessment | 32 | 74 (fallback) | +0.236 | [−0.053, +0.525] |
| white | non-white rule | 128 | 74 (fallback) | +0.223 | [+0.071, +0.375] |

The transported rule is `cd40 ≤ 415.5 & homo ≤ 0.5`, not the full-cohort rule;
its discovery support is 74, below the 200 floor, so it is a fallback rule. The
direction is consistent (+0.22 to +0.24) but the training set is too small to
meet the support floor. This is a **feasibility signal**, not external
validation.

## Decision

No model change. The gate adds three limitations to the report:

1. Group effects are underpowered; fairness cannot be established from 1,054
   patients with 38 rule patients in assessment.
2. The female stratum is the worst-calibrated group (ECE 0.058).
3. Internal transport loses the support floor; a larger cohort is required.
