# Gate 32 pre-registration — rule-learner comparison

Frozen before execution. The frozen pipeline uses a depth-3 regression CART on
the AIPW pseudo-outcome. This gate tests whether a different rule learner
dominates it on the frozen selection protocol.

## Learners

| id | learner | specification |
|---|---|---|
| `cart` | regression CART | depth 3, min_samples_leaf 60, squared error (frozen) |
| `pruned` | cost-complexity pruned CART | depth 5 / leaf 20 base; `ccp_alpha` chosen by 5-fold CV on ψ |
| `prim` | patient rule induction | peeling box, 5% peel, support ≥ 200, max 6 conditions |
| `class` | classification tree | depth 3, leaf 60 on `1{ψ > 0}`; leaf mean ψ used for selection |
| `boost` | boosting distillation | 5-fold HistGradientBoosting on ψ, distilled to depth-3 CART, leaf 60 |

All learners receive the same discovery ψ, the same validation/assessment AIPW
contrasts, the same support floor 200, and the same one-sided LCB commitment.

## Design

| item | value |
|---|---|
| n | 8,000 |
| partitions | 4,000 discovery / 2,000 validation / 2,000 assessment |
| replications | 20 fresh seeds per DGP, 910100–910119 |
| DGPs | single-region and two-region effects |
| nuisance | frozen Cox + conditional censoring Cox, 5-fold, seed per replication |
| target | AIPW ψ, e = 0.5, cap min(Q0.99, 20) |
| selection | max mean ψ among rules with support ≥ 200; fallback flagged |
| commitment | validation one-sided 95% LCB > 0 |

## Outcomes (paired within replication)

1. Purity of the selected rule.
2. Captured benefit of the selected rule.
3. Jaccard with the true region.
4. Assessment MAE of the resulting rule model.
5. Commitment rate and support.
6. Rule complexity (number of conditions).
7. Wall-clock seconds per replication.

## Decision rule (fixed)

An alternative replaces regression CART only if **all** hold:

1. purity falls by no more than 0.02;
2. capture or Jaccard improves with a paired 95% bootstrap CI excluding zero;
3. assessment MAE does not worsen by more than 0.002;
4. the selected rule has at most 3 conditions;
5. cost is at most 5× CART.

Holm adjustment across the four alternatives on the primary metric
(captured benefit).

## Failure interpretation

| result | interpretation |
|---|---|
| PRIM is purer but much narrower | it is a different operating point, not a dominant learner |
| pruned CART matches CART | pruning is unnecessary at this depth |
| classification tree loses capture | binarising ψ discards effect magnitude |
| boosting distillation wins only at high cost | keep the simpler learner |

## Scope

One nuisance specification and two DGPs. This gate tests the learner, not the
target or the support rule.
