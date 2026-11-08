# Gate 36 verdict — AIPW is retained; fixed-horizon IPCW-TMLE is rejected

Pre-registration: `results/gate36_PREREGISTRATION.md`. Full run: 20 fresh seeds
per DGP (940100–940119), n = 8,000. Both estimators use the same cross-fitted Cox
nuisances, folds, partitions and C200 learner. The only difference is the
targeting step.

## Result

| DGP | estimator | bias | coverage | MAE | Brier | purity | capture | commit | MAE (assessment) | cost (s) |
|---|---|---|---|---|---|---|---|---|---|---|
| single | **AIPW** | **−0.0014** | 95% | **0.0516** | **0.0026** | 0.869 | **0.582** | 70% | 0.0623 | **0.0** |
| single | TMLE | −0.0052 | 100% | 0.1408 | 0.0177 | **0.932** | 0.542 | 85% | **0.0523** | 4.55 |
| two | **AIPW** | **−0.0019** | 95% | **0.0578** | **0.0031** | 0.836 | 0.390 | 80% | 0.0702 | **0.0** |
| two | TMLE | −0.0111 | 100% | 0.1374 | 0.0172 | **0.904** | 0.398 | 90% | **0.0656** | 4.67 |

## Paired contrasts vs AIPW

| DGP | ΔMAE [95% CI] | p | ΔBrier | Δpurity | Δcapture |
|---|---|---|---|---|---|
| single | +0.0892 [+0.0876, +0.0907] | <0.001 | +0.0151 | +0.064 | −0.039 |
| two | +0.0795 [+0.0778, +0.0812] | <0.001 | +0.0140 | +0.068 | +0.008 |

## Decision

**AIPW is retained; TMLE is rejected.** The pre-registered criteria were:

1. MAE improves by at least 0.002 with a paired CI below zero, **or** absolute
   bias falls by at least 50% with coverage closer to 95%;
2. purity and capture do not fall by more than 0.02;
3. cost is at most 2× AIPW.

TMLE fails all three:

* patient-level MAE is **0.089–0.080 worse** (both CIs above zero) and Brier is
  **0.014–0.015 worse**;
* absolute bias is **larger**, not smaller (−0.0052 vs −0.0014; −0.0111 vs
  −0.0019);
* capture falls by 0.039 in the single-region DGP;
* cost is 4.5–4.7 s versus effectively zero for AIPW.

The targeting step does improve purity (+0.064 / +0.068) and assessment MAE
(−0.010 / −0.005), so it is not a useless estimator. It is a different operating
point: narrower and purer, but much worse at patient-level prediction and
marginal bias. Under the pre-registered criteria, that is a rejection.

## What this establishes

The fixed-horizon IPCW-TMLE with a logistic fluctuation does not dominate AIPW
on this target. The targeted update moves the marginal estimate away from the
truth and distorts the patient-level contrast, even though it produces a purer
subgroup. AIPW remains the estimator of record.

## What it does not establish

* This is **fixed-horizon IPCW-TMLE**, not the longitudinal TMLE over the whole
  survival curve. A longitudinal TMLE, or a TMLE with a bounded outcome and a
  different fluctuation, could behave differently.
* Two DGPs, one horizon, one censoring mechanism.
* The targeting step used a global epsilon on cross-fitted initial nuisances; a
  fold-specific targeting step was not tested.
