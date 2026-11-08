# Gate 35 pre-registration — fairness, SHAP and internal transport

Frozen before execution. This gate is descriptive: ACTG175 has no known
individual treatment-effect truth, so no method can be declared fair or
transportable from this dataset alone. The purpose is to measure whether the
selected rule and its effect differ across race and gender, and whether a rule
learned on one race transports to the other.

## Analyses

| id | analysis | data |
|---|---|---|
| F1 | rule effect by race (white / non-white) | assessment partition |
| F2 | rule effect by gender (female / male) | assessment partition |
| F3 | predicted vs observed S(730) by group | assessment partition |
| F4 | rule prevalence and commitment by group | assessment partition |
| S1 | SHAP importance of a surrogate model on ψ | discovery → assessment |
| T1 | rule learned on white patients, evaluated on non-white | internal transport |

## Design

| item | value |
|---|---|
| cohort | ACTG175 arms 0/1, n = 1,054 |
| split | 527 / 263 / 264, seeds 2024/2025, A×E strata |
| model | frozen C200 (Cox nuisances, depth-3 CART, support 200) |
| rule effect | AIPW contrast on assessment |
| intervals | influence-function 95% CI |
| SHAP | TreeExplainer on a RandomForestRegressor surrogate for ψ |

## Reporting rules

1. A group with fewer than 30 rule patients is reported as **underpowered**;
   its interval is shown, but it is not interpreted as evidence of fairness or
   harm.
2. SHAP is **supplementary**: the rule is the explanation; SHAP describes a
   surrogate, not the policy.
3. Transport is **descriptive**: a change in effect is a signal for a larger
   validation study, not proof of non-transportability.
4. No model selection is performed in this gate. Nothing is tuned on these
   results.

## Decision rule

No adoption decision. If a group effect changes sign or the transported effect
loses its sign, that is recorded as a limitation and a target for future work.
