# Gate 32 verdict — no rule learner dominates regression CART

Pre-registration: `results/gate32_PREREGISTRATION.md`. 20 fresh seeds per DGP
(910100–910119), n = 8,000, identical discovery ψ and validation/assessment AIPW
contrasts for every learner.

## Result

| DGP | learner | purity | capture | Jaccard | commit | MAE | support | conditions | seconds |
|---|---|---|---|---|---|---|---|---|---|
| single | CART (frozen) | **0.889** | 0.531 | **0.487** | 80% | **0.0556** | 305 | 2.80 | **0.06** |
| single | pruned CART | 0.741 | **0.642** | 0.452 | 85% | 0.0562 | 635 | 2.35 | 2.94 |
| single | PRIM | 0.328 | 0.144 | 0.106 | 10% | 0.0760 | 211 | 4.60 | 0.06 |
| single | classification tree | 0.671 | 0.576 | 0.442 | 70% | 0.0603 | 511 | 2.80 | 0.05 |
| single | boosting distillation | 0.883 | 0.543 | 0.477 | 75% | 0.0621 | 338 | 2.70 | 105.1 |
| two | CART (frozen) | **0.811** | 0.379 | 0.296 | 65% | 0.0729 | 418 | 2.80 | **0.02** |
| two | pruned CART | 0.637 | **0.640** | **0.362** | 85% | 0.0762 | 999 | 1.85 | 1.62 |
| two | PRIM | 0.473 | 0.206 | 0.148 | 45% | 0.0842 | 346 | 4.75 | 0.03 |
| two | classification tree | 0.701 | 0.403 | 0.280 | 75% | 0.0737 | 525 | 2.90 | 0.02 |
| two | boosting distillation | 0.761 | 0.287 | 0.239 | 65% | **0.0699** | 287 | 2.75 | 25.1 |

## Paired contrasts vs CART

| DGP | learner | Δ capture [95% CI] | p (Holm) | Δ purity | Δ MAE |
|---|---|---|---|---|---|
| single | pruned | +0.111 [−0.057, +0.281] | 0.207 (0.622) | −0.149 | +0.0006 |
| single | classification | +0.045 [−0.081, +0.176] | 0.475 (0.950) | −0.219 | +0.0047 |
| single | boosting | +0.012 [−0.084, +0.097] | 0.738 (0.950) | −0.006 | +0.0065 |
| single | PRIM | −0.386 [−0.501, −0.270] | <0.001 (<0.001) | −0.561 | +0.0204 |
| two | pruned | +0.261 [+0.089, +0.429] | <0.001 (<0.001) | −0.173 | +0.0033 |
| two | classification | +0.024 [−0.046, +0.096] | 0.514 (0.514) | −0.110 | +0.0009 |
| two | boosting | −0.092 [−0.205, +0.025] | 0.116 (0.231) | −0.050 | −0.0029 |
| two | PRIM | −0.174 [−0.298, −0.041] | 0.008 (0.023) | −0.338 | +0.0113 |

## Decision

**Keep regression CART.** No alternative satisfies the pre-registered criteria:

* **Pruned CART** gains capture in the two-region DGP (+0.261) but loses 0.173
  purity. The allowed purity loss is 0.02; this is nearly nine times the bar.
  In the single-region DGP its capture gain is not significant and it still
  loses 0.149 purity.
* **Classification tree** loses 0.219 / 0.110 purity and does not improve capture
  significantly.
* **PRIM** loses both capture and purity; it also produces 4.6–4.8 conditions,
  above the three-condition interpretability limit.
* **Boosting distillation** is the only learner with a better MAE in the
  two-region DGP (−0.0029), but its capture is lower (−0.092), purity is lower
  (−0.050), and it costs 25–105 seconds per replication versus 0.02–0.06 for
  CART. It fails the 5× cost criterion by two orders of magnitude.

## What this establishes

At this sample size and ψ target, the frozen CART is on the purity–capture
frontier. More flexible learners buy capture by admitting patients outside the
true region, and the simpler tree is the only rule that stays within the purity
guardrail. This is a negative result for learner complexity, not a failure to
search: four alternatives were implemented and run on the same data.

## What it does not establish

* PRIM's peeling path was capped at six conditions; a different peeling fraction
  or paste-back step was not tested.
* The classification tree uses the leaf mean ψ for selection; a probability
  threshold could behave differently.
* One nuisance specification and two DGPs.
