# Gate 31 verdict — Cox is retained; stacking lowers MAE but fails purity and cost

Pre-registration: `results/gate31_PREREGISTRATION.md`. Full run: 20 fresh seeds
per DGP (900100–900119), n = 8,000, 100-tree RSF, 60-estimator GBM, 5-fold
cross-fitting. The censoring model, partitions and C200 learner are held fixed.

## Result

| DGP | nuisance | bias | coverage | MAE | Brier | purity | capture | commit | MAE (assessment) | cost (s) |
|---|---|---|---|---|---|---|---|---|---|---|
| single | **Cox** | −0.0039 | 90% | 0.0517 | **0.0028** | 0.794 | 0.623 | 75% | 0.0555 | **0.0015** |
| single | RSF | −0.0036 | 85% | 0.0542 | 0.0073 | 0.802 | 0.615 | 70% | 0.0566 | 119.8 |
| single | GBM | −0.0038 | 85% | 0.0528 | 0.0071 | 0.795 | 0.640 | 70% | 0.0559 | 147.5 |
| single | stack | −0.0037 | 90% | **0.0475** | 0.0044 | 0.793 | 0.623 | 75% | **0.0550** | 260.4 |
| two | **Cox** | −0.0040 | 85% | 0.0579 | **0.0033** | **0.833** | 0.424 | 80% | 0.0657 | **0.0007** |
| two | RSF | −0.0037 | 85% | 0.0560 | 0.0075 | 0.820 | 0.445 | 80% | 0.0654 | 77.2 |
| two | GBM | −0.0038 | 85% | 0.0546 | 0.0075 | 0.797 | 0.401 | 75% | 0.0676 | 61.0 |
| two | stack | −0.0038 | 85% | **0.0504** | 0.0048 | 0.803 | 0.433 | 80% | 0.0654 | 136.4 |

## Paired contrasts vs Cox

| DGP | nuisance | ΔMAE [95% CI] | p (Holm) | ΔBrier | Δpurity | Δcapture |
|---|---|---|---|---|---|---|
| single | RSF | +0.0025 [+0.0010, +0.0040] | 0.001 | +0.0046 | +0.008 | −0.008 |
| single | GBM | +0.0011 [−0.0005, +0.0027] | 0.189 | +0.0043 | +0.000 | +0.017 |
| single | stack | **−0.0043 [−0.0055, −0.0030]** | **<0.001** | +0.0017 | −0.001 | −0.0002 |
| two | RSF | **−0.0019 [−0.0035, −0.0004]** | 0.012 | +0.0042 | −0.013 | +0.021 |
| two | GBM | **−0.0033 [−0.0048, −0.0017]** | 0.001 | +0.0042 | **−0.036** | −0.023 |
| two | stack | **−0.0075 [−0.0087, −0.0063]** | **<0.001** | +0.0015 | **−0.030** | +0.009 |

## Decision

**Cox is retained.** No flexible model satisfies the pre-registered joint
criteria:

* **Stacking** is the only model with a significant MAE gain in both DGPs
  (−0.0043 single, −0.0075 two). It fails on purity in the two-region DGP
  (−0.030, above the allowed 0.02 loss), and its discovery cross-fit costs
  136–260 s per replication versus 0.001–0.002 s for Cox. It is rejected on the
  purity and cost guardrails.
* **GBM** lowers MAE in the two-region DGP (−0.0033) but loses 0.036 purity and
  does not improve the single-region MAE. Rejected.
* **RSF** is worse in the single-region DGP (+0.0025) and its two-region gain
  (−0.0019) is below the 0.002 threshold. Rejected.
* **Brier score is worse for every flexible model** (0.0044–0.0075 vs
  0.0028–0.0033 for Cox), so the gain in patient-level MAE does not come from a
  better survival model; it comes from a different bias–variance trade-off in
  the contrast.
* Coverage does not improve: Cox is 90% / 85%, the flexible models 85–90%.

## What this establishes

The linear predictor is adequate for the causal target on these DGPs. A flexible
nuisance can reduce the patient-level MAE, but it does so by changing the
subgroup and losing purity, and it is orders of magnitude more expensive. This
is a negative result for nuisance complexity, not a failure to search.

## What it does not establish

* Two DGPs, one sample size, one censoring mechanism. The result does not rule
  out a flexible nuisance under stronger non-proportional hazards or a different
  covariate distribution.
* The equal-weight stack is one stacking rule; a learned meta-learner was not
  tested.
* Cost is measured on this machine; the ratio to Cox is large regardless of
  hardware.
