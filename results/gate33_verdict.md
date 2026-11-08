# Gate 33 verdict — isotonic calibration is confirmed; the selection bootstrap is rejected

Pre-registration: `results/gate33_PREREGISTRATION.md`. Main run: 20 seeds per
DGP (920100–920119). Confirmation: 20 fresh seeds per DGP (921100–921119).
Both runs use n = 8,000 and the frozen C200 rule.

## Calibration

| DGP | method | MAE | ΔMAE vs none [95% CI] | p | policy |
|---|---|---|---|---|---|
| single | none | 0.0522 | — | — | 80% commit |
| single | shrinkage | 0.0508 | −0.0014 [−0.0067, +0.0040] | 0.615 | unchanged |
| single | **isotonic** | **0.0469** | **−0.0053 [−0.0104, −0.0001]** | **0.046** | unchanged |
| two | none | 0.0727 | — | — | 60% commit |
| two | shrinkage | 0.0703 | −0.0024 [−0.0066, +0.0019] | 0.264 | unchanged |
| two | **isotonic** | **0.0662** | **−0.0065 [−0.0099, −0.0032]** | **<0.001** | unchanged |

Isotonic calibration replicates in both DGPs: MAE improves by 0.0053 and 0.0065,
the paired CI excludes zero in both, and purity, capture and commitment are
identical. The main run showed the same direction. **Adopt isotonic calibration
for prediction (C200-I).** The rule, support floor and commitment decision are
unchanged.

Shrinkage is not retained as the prediction calibration: it is directionally
positive but not significant in either confirmation cell, and isotonic is
significantly better in both.

## Intervals

| DGP | method | coverage | width | width / IF |
|---|---|---|---|---|
| single | **IF (frozen)** | **95%** | **0.216** | **1.00** |
| single | validation bootstrap | 95% | 0.253 | 1.17 |
| single | selection bootstrap | 85% | 0.270 | 1.25 |
| single | split-conformal | 100% | 0.503 | 2.33 |
| two | **IF (frozen)** | **95%** | **0.228** | **1.00** |
| two | validation bootstrap | 100% | 0.264 | 1.16 |
| two | selection bootstrap | 95% | 0.270 | 1.18 |
| two | split-conformal | 100% | 0.531 | 2.33 |

The confirmation reverses the main-run result for the selection bootstrap. In
the single-region DGP it covers **85%**, below the frozen IF interval's 95%; in
the two-region DGP it covers 95% but is wider than IF. It does not meet the
pre-registered criterion (coverage at least 92.5%, closer to 95%, width ≤2× IF)
in both DGPs. **Reject the selection bootstrap as the primary interval.** Keep
the IF interval and report its measured coverage honestly.

The split-conformal interval covers 100% in both DGPs but is 2.33× wider than
IF, above the 2× cap. It is reported as a sensitivity analysis, not adopted.

## Decision

- **Adopt:** isotonic calibration for prediction only (C200-I). The policy is
  unchanged.
- **Reject:** selection bootstrap as the primary interval; split-conformal
  (too wide).
- **Keep:** influence-function interval, with 95% coverage in this confirmation
  block and 90–92.5% in the earlier audits.

## What this establishes

The calibration layer is now experimentally settled: isotonic beats both no
calibration and shrinkage on fresh seeds without changing who is treated. The
inference layer is not settled in favour of a more complex procedure: the
selection bootstrap's apparent gain in the main run did not replicate.

## What it does not establish

* The selection bootstrap was tested on two DGPs and one sample size; a
  different selection regime could behave differently.
* The IF interval is conditional on the selected rule; its coverage is measured,
  not guaranteed.
* The SCRE head-to-head was run with C200-S, not C200-I. A fresh SCRE comparison
  with isotonic calibration is not part of this gate.
