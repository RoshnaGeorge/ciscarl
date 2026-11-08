# CISCaRL — final claims after v1.17 (A×E split, diagnostics, policy value)

**Status:** the canonical results are those of the A×E split
(`results/CANONICAL_RESULTS.md`). v1.16's head-to-head numbers remain valid; the
ACTG175 numbers change because the split changed.

Supersedes the earlier claim files v1.3–v1.16 (removed from the release).

---

## 1. The model

| layer | specification |
|---|---|
| Estimand | τ(730\|X) = S₁(730\|X) − S₀(730\|X), composite endpoint, treatment-policy strategy |
| Estimation | per-arm Cox + conditional censoring Cox, 5-fold cross-fit, cap min(Q₀.₉₉, 20), AIPW |
| Discovery | depth-3 CART on ψ, min_samples_leaf 60, squared_error |
| Selection | max discovery mean ψ among leaves with ≥ 200 discovery patients |
| Commitment | validation one-sided 95 % LCB > 0 |
| Prediction | validation leaf effects; empirical-Bayes shrinkage for prediction only (C200-S) |
| Fallbacks | discovery marginal ATE; no treatment |

## 2. ACTG175 (A×E split, 527/263/264)

- Overall τ(730) = **+0.124**, 95 % CI [−0.002, +0.250], one-sided LCB +0.018.
- Largest leaf 173 → support ≥ 200 **not met**; fallback to
  `cd40 ≤ 407.5 & wtkg > 71.0 & homo ≤ 0.5`, support 61.
- Validation +0.116 (SE 0.222), LCB **−0.250** → **INSUFFICIENT**.
- Assessment +0.401 [+0.033, +0.770] on 38 patients (descriptive).
- KM check +0.341 [+0.177, +0.501]; marginal KM +0.133 vs AIPW +0.124.
- δ-tilt +0.401 to +0.456.

## 3. Simulation (unchanged from v1.16)

Pooled 80 reps: C200 is worse than SCRE on MAE (+0.0062, p < 0.001; +0.0031,
p = 0.044); C200-S ties (+0.0011, p = 0.48; +0.0004, p = 0.76). Purity 0.890 /
0.858 vs 0.437 / 0.599; per-treated +0.174 / +0.165 vs +0.085 / +0.101;
coverage 0.133 / 0.117 vs 0.548 / 0.563.

1,000-rep sweeps: purity 0.856 / 0.844 vs 0.597 / 0.476; capture 0.304 / 0.294 vs
0.810 / 0.547; null rate 0 % in both methods.

## 4. New evidence added in v1.17

| finding | result |
|---|---|
| Nested-refit tuning | best config 0.8633 vs frozen 0.8638; **no gain**; absolute-error "win" withdrawn |
| PH diagnostics | global p = 0.235 / 0.368; `cd40` violates in both arms (0.021 / 0.023) |
| Efron vs Breslow | max coefficient difference 0.0014 — immaterial |
| Survival calibration | overall gap −0.006 / −0.013; ECE 0.032 |
| Weight-cap sensitivity | binds only at 1.2 (9.9 %); every cap ≥ 1.5 leaves the rule unchanged |
| Policy value | C200 0.787 / 0.786; SCRE 0.793 / 0.804; treat-all 0.815 / 0.835; none 0.766 |
| Net benefit | C200 leads from λ ≈ 0.05 (single) and λ ≈ 0.10 (two) |
| Interval coverage | **92.5 %** of replications cover the true rule effect, mean width 0.27 |
| Split-ratio study | 50/25/25 retained; 20 distinct rules from 20 splits at every ratio |

## 5. Claims we can defend

> Under two simulation DGPs at n = 8000 with disjoint roles, C200 with shrinkage
> ties SCRE on patient-level MAE while being substantially purer and delivering
> about twice the benefit per treated patient. Its policy value is lower than
> treat-all when treatment is free and higher than both SCRE and treat-all once
> one treated patient costs more than ≈ 0.05 survival-probability units. On
> ACTG175 the average contrast is +0.124 and the support constraint cannot be
> met; the model abstains rather than reporting a 61-patient subgroup.

## 6. Claims we cannot make

- ❌ "CISCaRL beats SCRE on accuracy." Tied after calibration, worse before it.
- ❌ "The absolute-error tree is better." Withdrawn: nested refitting removes the gap.
- ❌ "Support 200 is optimal." Proportional is better at small n.
- ❌ "95 % intervals." IF coverage is 90–92.5 % in the policy audit and 95 % in
  the Gate 33 confirmation; the intervals condition on the selected rule.
- ❌ "Validated on ACTG175." The model abstains.
- ❌ "Conformal intervals." No conformal procedure is implemented.
- ❌ "Stable rule." Jaccard ≈ 0.34; 20/20 distinct rules across splits.

## 7. Evidence extension (Gates 31–35)

- **Rule learners (Gate 32).** CART is retained against four implemented
  alternatives. Pruned CART gains capture but loses 0.149–0.173 purity; PRIM
  loses capture and purity; the classification tree loses 0.110–0.219 purity;
  boosting distillation costs 400–1,700× and loses purity. This is a tested
  negative result, not an unexamined default.
- **Folds (Gate 34).** 3, 5 and 10 folds were run. 10 folds improves MAE by
  0.0005, below the 0.002 threshold, at 2.1–2.3× cost. 5 retained.
- **Calibration (Gate 33).** Isotonic improves MAE by 0.0053 / 0.0065 on fresh
  seeds, with both CIs below zero and the policy unchanged. **Adopted for
  prediction only (C200-I).** Shrinkage (C200-S) remains the version used in the
  SCRE head-to-head; a fresh SCRE comparison with C200-I is not done.
- **Intervals (Gate 33).** The selection bootstrap failed confirmation (85%
  single, 95% two; wider than IF) and is **rejected** as the primary interval.
  Split-conformal covers 100% but is 2.33× wider and is rejected. The IF
  interval is retained (95% in confirmation, 90–92.5% in earlier audits).
- **Fairness/transport (Gate 35).** Every race/gender group has fewer than 30
  rule patients; fairness is not established. Female calibration is worst
  (ECE 0.058). White→non-white transport has support 74 (<200) and is a
  feasibility signal, not external validation.
- **TMLE (Gate 36).** Fixed-horizon IPCW-TMLE is rejected. Patient-level MAE is
  0.079–0.089 worse, Brier 0.014–0.015 worse, bias larger, and cost 4.5 s vs
  ~0. It is purer and has better assessment MAE, but fails the pre-registered
  criteria. AIPW is retained. This is not longitudinal TMLE.
- **Learned stacking (Gate 39).** Cox retained. The learned weights are ~0.77
  Cox, 0.14 RSF, 0.09 GBM; the learned stack is indistinguishable from Cox
  (+0.0007 / +0.0001 MAE, ns). Equal-weight stacking lowers MAE but loses 0.036
  capture in the single-region DGP; it is a sensitivity, not adopted.
- **Horizon (Gates 37, 42–44).** One split favours 965 on validation (LCB
  −0.000) and 845 on discovery-only inner CV (+0.014). Across 20 splits, 730 has
  the best mean validation LCB (−0.142) and lowest SD (0.114); 845 has a higher
  mean assessment effect (+0.251) but worse LCB (−0.167) and 1.6× the
  variability; 965 is worst (−0.206). 730 retained on stability, not convention.
- **Feature selection (Gate 38).** 12 retained. Lasso selects all 12; RFE drops
  `age`, changes the rule and falls to support 79.
- **SCRE alpha path (Gate 40).** Chosen alpha within 0.0010–0.0017 MAE of the
  best path alpha; the direction is unchanged, the exact purity/capture numbers
  are path-sensitive.
- **Selection-aware intervals (Gate 41).** IF retained (95–100% coverage);
  Bonferroni 100% at 1.38× width; sample-splitting 100% at the same width but a
  different rule. Both are sensitivities.
- **Nuisance (Gate 31).** Full 20-seed comparison completed. Cox is retained:
  stacking lowers patient-level MAE (−0.0043 / −0.0075) but loses 0.030 purity
  in the two-region DGP and costs 136–260 s vs 0.002 s; GBM loses 0.036 purity;
  RSF is worse in the single-region DGP. Brier is worse for every flexible
  model. Cox remains frozen.

## 8. Remaining

- General selective inference beyond the bootstrap.
- External validation on PBC: out of scope for this ACTG175-only project.
- Learned stacking meta-learner (only equal-weight stacking was tested).
- Longitudinal TMLE (fixed-horizon IPCW-TMLE was tested and rejected).
