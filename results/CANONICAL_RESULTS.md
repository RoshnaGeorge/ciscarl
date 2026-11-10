# Canonical results record (v2, A×E split)

Single source of truth for the paper, notebook and repository. If a number in any
artefact disagrees with this file, this file wins.

## Configuration

| item | value |
|---|---|
| dataset | ACTG175, arms 0/1, n = 1054 |
| covariates | 12 baseline (cd40, cd80, age, wtkg, karnof, hemo, homo, race, gender, drugs, str2, symptom) |
| horizon | 730 days |
| split | 527 / 263 / 264, stratified by treatment × event |
| split seeds | 2024 (discovery vs holdout), 2025 (validation vs assessment) |
| nuisance | per-arm Cox + conditional censoring Cox, 5-fold cross-fit, cap min(Q0.99, 20) |
| target | AIPW psi, e = 0.5 |
| learner | depth-3 CART, min_samples_leaf 60, squared_error |
| selection | max discovery mean psi with support ≥ 200; fallback flagged |
| commitment | validation one-sided 95% LCB > 0 |
| calibration | isotonic for prediction only (C200-I), confirmed in Gate 33; C200-S (shrinkage) is the version used in the Gate 28/30 SCRE head-to-head |
| seed blocks | 300100 head-to-head, 310100 tuning, 320100 confirmation, 700100 policy |

## ACTG175 (A×E split)

| quantity | value |
|---|---|
| overall τ(730) | **+0.124**, 95% CI [−0.002, +0.250], one-sided LCB +0.018 |
| largest leaf | 173 → support ≥ 200 not met |
| selected rule | `cd40 ≤ 407.5 & wtkg > 71.0 & homo ≤ 0.5` |
| discovery support | 61 (11.6%) |
| validation effect | +0.116, SE 0.222, n = 31, LCB **−0.250** |
| decision | **INSUFFICIENT** |
| assessment, rule | +0.401 [+0.033, +0.770], n = 38 |
| KM check, rule (all 1054) | S1 0.892, S0 0.550, **+0.341 [+0.177, +0.501]**, n = 130 |
| KM check, marginal | +0.133 [+0.085, +0.179] |
| δ-tilt | +0.401 to +0.456 over δ ∈ [−2, 2] |

## Simulation head-to-head (80 paired reps, two seed blocks)

| design | method | MAE | vs SCRE | purity | capture | per-treated | coverage |
|---|---|---|---|---|---|---|---|
| single | C200 | 0.0576 | +0.0062 [+0.0031, +0.0094] | 0.890 | 0.465 | +0.174 | 0.133 |
| single | C200-S | 0.0525 | +0.0011 [−0.0019, +0.0042] | 0.890 | 0.465 | +0.174 | 0.133 |
| single | SCRE | 0.0514 | — | 0.437 | 0.954 | +0.085 | 0.548 |
| two | C200 | 0.0707 | +0.0031 [+0.0001, +0.0059] | 0.858 | 0.277 | +0.165 | 0.117 |
| two | C200-S | 0.0680 | +0.0004 [−0.0025, +0.0033] | 0.858 | 0.277 | +0.165 | 0.117 |
| two | SCRE | 0.0676 | — | 0.599 | 0.823 | +0.101 | 0.563 |

## 1000-replication sweeps

| design | method | purity (sd) | median / p10 | ≥0.80 committed | coverage | capture | per-treated | commit | MAE |
|---|---|---|---|---|---|---|---|---|---|
| two | C200 | 0.856 (0.166) | 0.925 / 0.603 | 68.7% | 0.135 | 0.304 | 0.164 | 72.5% | 0.0701 |
| two | SCRE | 0.597 (0.053) | 0.604 / 0.527 | 0% | 0.559 | 0.810 | 0.100 | 100% | 0.0682 |
| stress | C200 | 0.844 (0.180) | 0.915 / 0.579 | 65.5% | 0.136 | 0.294 | 0.159 | 68.2% | 0.0701 |
| stress | SCRE | 0.476 (0.054) | 0.474 / 0.407 | 0% | 0.512 | 0.547 | 0.074 | 100% | 0.0821 |

## Nuisance diagnostics

| check | result |
|---|---|
| PH global (Fisher, rank) | p = 0.235 (arm 0), 0.368 (arm 1) — no global violation |
| PH per covariate | cd40 0.021 / 0.023; str2 0.022 (arm 0); wtkg 0.048 (arm 1) |
| Efron vs Breslow | max coefficient difference 0.0014 |
| calibration at 730 | overall gap −0.006 / −0.013; ECE 0.032 |
| weight cap | binds only at 1.2 (9.9% of weights); ≥1.5 never binds |

## Nested-refit tuning

| config | nested MAE |
|---|---|
| depth 4 / leaf 60 / squared | 0.8633 |
| depth 3 / leaf 60 / squared (frozen) | 0.8638 |
| depth 3 / leaf 60 / absolute | 0.8711 |

No configuration beats the frozen one; the earlier absolute-error advantage
(0.824 vs 0.871) was optimism from tuning on a precomputed psi and is withdrawn.

## Policy value (40 paired reps)

| design | none | C200 | SCRE | treat all |
|---|---|---|---|---|
| single | 0.7659 | 0.7870 | 0.7926 | 0.8145 |
| two | 0.7659 | 0.7855 | 0.8044 | 0.8345 |

Net benefit U = V − λ·treat_rate: C200 leads from λ ≈ 0.05 (single) and
λ ≈ 0.10 (two). Influence-function interval coverage of the true rule effect:
**92.5%** in the policy audit and **90%** in Gate 33; the selection bootstrap
failed confirmation (85% single, 95% two; wider than IF) and was rejected.
IF coverage is 95% in the confirmation block and 90–92.5% in earlier audits.

## Split-ratio study

| ratio | real: median val SE | real: commit | sim: purity | sim: capture |
|---|---|---|---|---|
| 40/30/30 | 0.147 | 30% | 0.868 | 0.378 |
| 50/25/25 | 0.157 | 25% | 0.941 | 0.479 |
| 60/20/20 | 0.126 | 5% | 0.940 | 0.432 |
| 70/15/15 | 0.142 | 30% | 0.965 | 0.463 |

Every ratio produced 20 distinct rules from 20 splits.

## Evidence extension (Gates 31–35)

Full tables and decisions: `results/EVIDENCE_EXTENSION.md`, `gate31_*`,
`gate32_verdict.md`, `gate33_verdict.md`, `gate34_verdict.md`,
`gate35_verdict.md`.

* Gate 31 (nuisance): full 20-seed run. Cox remains frozen. Stacking lowers
  patient-level MAE (−0.0043 / −0.0075) but loses 0.030 purity in the two-region
  DGP and costs 136–260 s vs 0.002 s for Cox; GBM loses 0.036 purity; RSF is
  worse in the single-region DGP. Brier is worse for every flexible model.
* Gate 32 (rule learners): CART retained; pruned CART, PRIM, classification and
  boosting distillation all fail the purity or cost guardrail.
* Gate 33 (calibration/intervals): isotonic calibration replicated on fresh seeds
  (−0.0053 / −0.0065 MAE, both CIs below zero) and is **adopted for prediction
  only (C200-I)**. The selection bootstrap failed confirmation (85% single,
  95% two; wider than IF) and is **rejected**. The IF interval is retained:
  95% coverage in confirmation, 90–92.5% in earlier audits.
* Gate 34 (folds): 5 retained; 10 folds gains 0.0005 MAE, below the 0.002 bar.
* Gate 35 (fairness/SHAP/transport): descriptive and underpowered; no fairness or
  transport claim. The canonical ACTG175 rule and abstention are unchanged.
* Gate 36 (AIPW vs fixed-horizon IPCW-TMLE): AIPW retained. TMLE patient-level
  MAE is 0.079–0.089 worse, Brier 0.014–0.015 worse, bias larger, and cost
  4.5 s vs ~0. TMLE is purer (0.932 / 0.904 vs 0.869 / 0.836) and has better
  assessment MAE (0.0523 / 0.0656 vs 0.0623 / 0.0702), but fails the
  pre-registered MAE/bias/capture/cost criteria.
* Gate 39 (learned stacking): Cox retained. Learned weights are ~0.77 Cox,
  0.14 RSF, 0.09 GBM; the learned stack is indistinguishable from Cox
  (+0.0007 / +0.0001 MAE, ns). Equal-weight stacking lowers MAE (−0.0038 /
  −0.0064) but loses 0.036 capture in the single-region DGP; it is a
  sensitivity, not adopted.
* Gate 37 (horizon): no horizon meets all criteria; 730 retained as the
  documented compromise (99 events, 71% at risk, fallback support 61).
* Gate 38 (features): 12 retained. Lasso selects all 12; RFE drops `age`,
  changes the rule and falls to support 79.
* Gate 40 (SCRE alpha path): chosen alpha within 0.0010–0.0017 MAE of the best
  path alpha; direction unchanged.
* Gate 41 (selection-aware intervals): IF retained (95–100% coverage); Bonferroni
  100% at 1.38× width; sample-splitting 100% at the same width but a different
  rule. Both reported as sensitivities.
* Gates 42–44 (horizon): one split favours 965 on validation (LCB −0.000) and 845
  on discovery-only inner CV (+0.014). Across 20 splits, 730 has the best mean
  validation LCB (−0.142) and lowest SD (0.114); 845 has a higher mean assessment
  effect (+0.251) but worse LCB (−0.167) and 1.6× the variability; 965 is worst
  (−0.206). 730 retained on stability, not convention.

## CART tuning and ensembles (Gates 45–47)

* Gate 45: 540-configuration nested tuning on ACTG175 discovery selected
  depth 5 / leaf 30 / squared error (nested MAE 0.85982 vs 0.86379 for the
  frozen tree, rank 54 of 540). It was not adopted on pseudo-outcome error
  alone.
* Gate 46: no ensemble (random forest, extra trees, gradient boosting,
  histogram GB, ridge stack) produced a capture gain with a 95% interval above
  zero; costs were 4.8–65.9 s vs 0.07 s for CART. CART retained.
* Gate 47: tuning on simulated subgroup performance selected depth 2 /
  absolute error (validation LCB +0.0605/+0.0731). On the canonical ACTG175
  split it selects 122 patients, validation LCB −0.210, assessment +0.282 and
  abstains; the frozen tree selects 61, LCB −0.250, assessment +0.401. No
  alternative produced a certifiable subgroup, so the frozen CART
  (3 / 60 / squared error) remains.
