# Evidence extension — implemented gates

This file records the experiments added after the first 30 gates. Each gate was
pre-registered before execution. Numbers here are the source for the report.

## Gate 32 — rule learners (20 seeds × 2 DGPs)

| DGP | learner | purity | capture | Jaccard | commit | MAE | cost (s) |
|---|---|---|---|---|---|---|---|
| single | CART | 0.889 | 0.531 | 0.487 | 80% | 0.0556 | 0.06 |
| single | pruned | 0.741 | 0.642 | 0.452 | 85% | 0.0562 | 2.94 |
| single | PRIM | 0.328 | 0.144 | 0.106 | 10% | 0.0760 | 0.06 |
| single | classification | 0.671 | 0.576 | 0.442 | 70% | 0.0603 | 0.05 |
| single | boosting distill | 0.883 | 0.543 | 0.477 | 75% | 0.0621 | 105.1 |
| two | CART | 0.811 | 0.379 | 0.296 | 65% | 0.0729 | 0.02 |
| two | pruned | 0.637 | 0.640 | 0.362 | 85% | 0.0762 | 1.62 |
| two | PRIM | 0.473 | 0.206 | 0.148 | 45% | 0.0842 | 0.03 |
| two | classification | 0.701 | 0.403 | 0.280 | 75% | 0.0737 | 0.02 |
| two | boosting distill | 0.761 | 0.287 | 0.239 | 65% | 0.0699 | 25.1 |

Decision: keep CART. Pruned CART gains capture but loses 0.149–0.173 purity
(allowed loss 0.02). Classification loses 0.110–0.219 purity. PRIM loses both.
Boosting distillation costs 400–1,700× CART and loses purity.

## Gate 34 — folds (20 seeds × 2 DGPs)

| DGP | folds | bias | coverage | MAE | cost (s) | ΔMAE vs 5 |
|---|---|---|---|---|---|---|
| single | 3 | +0.0023 | 95% | 0.0522 | 6.7 | +0.0011 |
| single | 5 | +0.0022 | 95% | 0.0511 | 12.4 | — |
| single | 10 | +0.0023 | 95% | 0.0506 | 28.2 | −0.0005 |
| two | 3 | +0.0018 | 95% | 0.0586 | 8.8 | +0.0010 |
| two | 5 | +0.0017 | 95% | 0.0576 | 15.6 | — |
| two | 10 | +0.0018 | 95% | 0.0571 | 32.8 | −0.0005 |

Decision: keep 5. Ten folds improves MAE by 0.0005, one quarter of the
pre-registered 0.002 threshold, at 2.1–2.3× cost.

## Gate 31 — outcome nuisance (20 seeds × 2 DGPs)

| DGP | nuisance | MAE | Brier | purity | capture | commit | cost (s) |
|---|---|---|---|---|---|---|---|
| single | Cox | 0.0517 | 0.0028 | 0.794 | 0.623 | 75% | 0.002 |
| single | RSF | 0.0542 | 0.0073 | 0.802 | 0.615 | 70% | 119.8 |
| single | GBM | 0.0528 | 0.0071 | 0.795 | 0.640 | 70% | 147.5 |
| single | stack | 0.0475 | 0.0044 | 0.793 | 0.623 | 75% | 260.4 |
| two | Cox | 0.0579 | 0.0033 | 0.833 | 0.424 | 80% | 0.001 |
| two | RSF | 0.0560 | 0.0075 | 0.820 | 0.445 | 80% | 77.2 |
| two | GBM | 0.0546 | 0.0075 | 0.797 | 0.401 | 75% | 61.0 |
| two | stack | 0.0504 | 0.0048 | 0.803 | 0.433 | 80% | 136.4 |

Cox retained. Stacking lowers MAE significantly (−0.0043 / −0.0075) but loses
0.030 purity in the two-region DGP and costs 136–260 s vs 0.002 s; GBM loses
0.036 purity; RSF is worse in the single-region DGP and below the 0.002
threshold in the two-region. Brier is worse for every flexible model.

## Gate 33 — calibration and intervals (20 seeds × 2 DGPs)

Main run plus 20-seed confirmation. Isotonic calibration is adopted for prediction;
the selection bootstrap was rejected at confirmation.

| DGP | calibration | MAE | ΔMAE vs none |
|---|---|---|---|
| single | none | 0.0531 | — |
| single | shrinkage | 0.0523 | −0.0009 |
| single | isotonic | 0.0455 | −0.0076 [−0.0121, −0.0034] |
| two | none | 0.0718 | — |
| two | shrinkage | 0.0720 | +0.0002 |
| two | isotonic | 0.0684 | −0.0034 [−0.0059, −0.0008] |

| DGP | interval | coverage | width |
|---|---|---|---|
| single | IF | 90% | 0.203 |
| single | selection bootstrap | 95% | 0.289 |
| single | split-conformal | 100% | 0.492 |
| two | IF | 90% | 0.205 |
| two | selection bootstrap | 100% | 0.274 |
| two | split-conformal | 100% | 0.490 |

Confirmation (20 fresh seeds, 921100–921119):

| DGP | calibration | MAE | ΔMAE vs none |
|---|---|---|---|
| single | none | 0.0522 | — |
| single | shrinkage | 0.0508 | −0.0014 [−0.0067, +0.0040] |
| single | isotonic | 0.0469 | −0.0053 [−0.0104, −0.0001] |
| two | none | 0.0727 | — |
| two | shrinkage | 0.0703 | −0.0024 [−0.0066, +0.0019] |
| two | isotonic | 0.0662 | −0.0065 [−0.0099, −0.0032] |

| DGP | interval | coverage | width |
|---|---|---|---|
| single | IF | 95% | 0.216 |
| single | selection bootstrap | 85% | 0.270 |
| single | split-conformal | 100% | 0.503 |
| two | IF | 95% | 0.228 |
| two | selection bootstrap | 95% | 0.270 |
| two | split-conformal | 100% | 0.531 |

Decision: isotonic calibration is **adopted for prediction only (C200-I)**. The
selection bootstrap is **rejected** (85% / 95% coverage; wider than IF); the IF
interval is retained. Split-conformal is rejected on width (2.33× IF).

## Gate 36 — AIPW vs fixed-horizon IPCW-TMLE (20 seeds × 2 DGPs)

| DGP | estimator | bias | coverage | MAE | Brier | purity | capture | assessment MAE |
|---|---|---|---|---|---|---|---|---|
| single | AIPW | −0.0014 | 95% | 0.0516 | 0.0026 | 0.869 | 0.582 | 0.0623 |
| single | TMLE | −0.0052 | 100% | 0.1408 | 0.0177 | 0.932 | 0.542 | 0.0523 |
| two | AIPW | −0.0019 | 95% | 0.0578 | 0.0031 | 0.836 | 0.390 | 0.0702 |
| two | TMLE | −0.0111 | 100% | 0.1374 | 0.0172 | 0.904 | 0.398 | 0.0656 |

AIPW retained; fixed-horizon IPCW-TMLE rejected. TMLE is purer and has better
assessment MAE, but patient-level MAE is 0.079–0.089 worse, Brier 0.014–0.015
worse, bias larger, and cost 4.5 s vs ~0. This is not longitudinal TMLE.

## Gate 37 — horizon selection

| Horizon | Events | At risk | Support | Val. LCB |
|---|---|---|---|---|
| 365 | 46 | 87.5% | 77 | +0.021 |
| 548 | 69 | 80.6% | 109 | +0.042 |
| 730 | 99 | 70.8% | 61 | −0.250 |
| 912 | 135 | 57.9% | 61 | −0.044 |
| 1,095 | 143 | 21.8% | 237 | −0.516 |

No horizon meets all criteria; 730 retained as the documented compromise.

## Gate 38 — feature selection

| Method | Features | Support | Val. SE | Rule |
|---|---|---|---|---|
| 12 | 12 | 61 | 0.222 | `cd40 ≤ 407.5 & wtkg > 71.0 & homo ≤ 0.5` |
| 16 | 16 | 61 | 0.223 | identical |
| lasso | 12 | 61 | 0.222 | identical |
| RFE | 11 | 79 | 0.180 | `cd80 > 805.5 & race > 0.5` |

12 retained. Lasso selects all 12; RFE changes the rule and falls below the
support floor.

## Gate 39 — learned stacking

| DGP | estimator | MAE | purity | capture |
|---|---|---|---|---|
| single | Cox | 0.0505 | 0.844 | 0.560 |
| single | learned | 0.0513 | 0.869 | 0.551 |
| two | Cox | 0.0573 | 0.817 | 0.413 |
| two | learned | 0.0573 | 0.817 | 0.413 |

Learned stack indistinguishable from Cox; equal weight lowers MAE but loses
0.036 capture in the single-region DGP. Cox retained.

## Gate 40 — SCRE alpha path

Chosen alpha within 0.0010–0.0017 MAE of the best path alpha; direction
unchanged. Path ranges: single MAE 0.056–0.079, purity 0.345–0.442, capture
0.911–0.976; two MAE 0.069–0.090, purity 0.477–0.605, capture 0.769–0.904.

## Gate 41 — selection-aware intervals

| DGP | method | coverage | width |
|---|---|---|---|
| single | IF | 95% | 0.298 |
| single | Bonferroni | 100% | 0.412 |
| single | sample-splitting | 100% | 0.298 |
| two | IF | 100% | 0.297 |
| two | Bonferroni | 100% | 0.412 |
| two | sample-splitting | 100% | 0.294 |

IF retained; Bonferroni and sample-splitting reported as sensitivities.

## Gate 35 — fairness, SHAP, internal transport

Main rule: `cd40 ≤ 407.5 & wtkg > 71.0 & homo ≤ 0.5`; support 61; validation
+0.116 (LCB −0.250) → INSUFFICIENT; assessment +0.401 [+0.102, +0.700], n = 38.

| group | n | rule n | effect | 95% CI | powered |
|---|---|---|---|---|---|
| white | 183 | 24 | +0.444 | [+0.081, +0.807] | no |
| non-white | 81 | 14 | +0.328 | [−0.191, +0.847] | no |
| male | 213 | 25 | +0.514 | [+0.147, +0.881] | no |
| female | 51 | 13 | +0.184 | [−0.318, +0.686] | no |

Calibration ECE: white 0.023, non-white 0.040, male 0.001, female 0.058.
SHAP top five: wtkg 0.048, cd40 0.046, cd80 0.042, str2 0.017, homo 0.011.
Transport: white-trained rule `cd40 ≤ 415.5 & homo ≤ 0.5`, support 74
(fallback); white assessment +0.236 [−0.053, +0.525], non-white +0.223
[+0.071, +0.375]. Descriptive, underpowered, not external validation.
