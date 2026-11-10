# Gate 48 — SHAP and LIME explainability audit

The final CART is a depth-3 rule: `cd40 <= 407.5 & wtkg > 71.0 & homo <= 0.5`. Discovery support is
61 (fallback True). Explanations are descriptive: they do not
change the rule, support floor, validation decision or assessment result.

## SHAP (exact TreeSHAP on the final CART)

Top features by mean absolute SHAP on the assessment partition:

| rank | feature | mean abs SHAP |
|---|---|---|
| 1 | cd40 | 0.1283 |
| 2 | homo | 0.0931 |
| 3 | cd80 | 0.0567 |
| 4 | wtkg | 0.0349 |
| 5 | age | 0.0000 |
| 6 | karnof | 0.0000 |
| 7 | hemo | 0.0000 |
| 8 | race | 0.0000 |

The top three are **cd40, homo, cd80**. `wtkg` ranks fourth globally, but it is
part of the selected rule; the SHAP rank is an average over assessment patients
and does not override the rule.

## LIME (local explanations)

40 assessment patients were explained (20
inside the rule, 20 outside), with
5 seeds per patient.

| group | mean SHAP–LIME top-5 Jaccard | mean LIME seed stability |
|---|---|---|
| inside rule | 0.767 | 0.703 |
| outside rule | 0.700 | 0.712 |

## Group-wise SHAP

Mean absolute SHAP by race and gender is saved in
`results/gate48_groups.csv`. The group sizes are small, so this is descriptive
only and cannot support a fairness claim.

## Interpretation

* SHAP confirms which features the tree uses globally; it does not prove a
  causal effect.
* LIME stability is 0.70 inside the rule and 0.71 outside. A top-5 overlap
  around 0.70 is **moderate, not high**: roughly two or three of five features
  recur across seeds. LIME is a local aid, not a definitive attribution.
* SHAP and LIME need not agree. The rule remains the primary explanation; the
  two post-hoc methods are audits, not replacements.

## Decision

No model change. SHAP and LIME are reported as secondary explainability
evidence. The final explanation remains the readable rule
`cd40 <= 407.5 & wtkg > 71.0 & homo <= 0.5` and the validation/abstention decision.
