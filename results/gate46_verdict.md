# Gate 46 — ensemble methods versus CART for rule discovery

Question: can a random forest, extremely randomised trees, gradient boosting,
histogram gradient boosting or a ridge stack produce a better **rule** than the
frozen CART?

Protocol: every ensemble is distilled into a depth-3 CART fitted to its
out-of-fold effect predictions on discovery. The same support floor (200),
validation lower-bound commitment and assessment metrics are then applied.
20 replications × 2 DGPs, 8,000 patients, 4,000/2,000/2,000 split.

## Result (mean over 20 replications)

| DGP | learner | purity | capture | Jaccard | commit % | MAE assessment | seconds |
|---|---|---|---|---|---|---|---|
| single | **CART 3/60/squared** | 0.776 | 0.570 | 0.521 | 80 | 0.0557 | 0.07 |
| single | CART 5/30 (Gate 45 best) | 0.686 | 0.345 | 0.323 | 55 | 0.0661 | 0.09 |
| single | random forest | 0.846 | 0.614 | 0.562 | 85 | 0.0524 | 33.0 |
| single | extra trees | 0.795 | 0.486 | 0.415 | 80 | 0.0603 | 19.1 |
| single | gradient boosting | 0.780 | 0.611 | 0.527 | 95 | 0.0542 | 10.1 |
| single | histogram GB | 0.793 | 0.597 | 0.518 | 100 | 0.0536 | 6.0 |
| single | ridge stack | 0.734 | 0.594 | 0.487 | 90 | 0.0542 | 64.6 |
| two | **CART 3/60/squared** | 0.783 | 0.429 | 0.337 | 90 | 0.0690 | 0.07 |
| two | CART 5/30 (Gate 45 best) | 0.714 | 0.298 | 0.245 | 55 | 0.0778 | 0.09 |
| two | random forest | 0.829 | 0.420 | 0.347 | 90 | 0.0666 | 32.4 |
| two | extra trees | 0.817 | 0.383 | 0.311 | 65 | 0.0676 | 18.8 |
| two | gradient boosting | 0.837 | 0.462 | 0.383 | 80 | 0.0674 | 9.7 |
| two | histogram GB | 0.829 | 0.460 | 0.362 | 90 | 0.0649 | 4.8 |
| two | ridge stack | 0.826 | 0.447 | 0.366 | 85 | 0.0674 | 65.9 |

Paired against frozen CART, **no ensemble has a capture gain whose 95% interval
excludes zero** (all p ≥ 0.40 except the tuned CART, which is significantly
worse). Some ensembles lower MAE by 0.0015–0.0041 and raise purity, but they
cost 4.8–65.9 s per replication against 0.07 s for CART.

Decision checks (purity loss ≤ 0.02, capture gain with CI above zero, MAE not
worse by more than 0.002, cost ≤ 5×):

* random forest — fails capture and cost;
* extra trees — fails capture, MAE and cost;
* gradient boosting — fails capture and cost;
* histogram GB — fails capture and cost;
* ridge stack — fails purity in the single-region design and fails cost;
* CART 5/30 — significantly worse capture and purity.

## Decision

**Keep regression CART (depth 3, leaf 60, squared error).** No ensemble is
adopted. The tuned CART is also rejected: the Gate 45 winner was selected on
pseudo-outcome error, and it loses purity and capture when the target is the
subgroup.

## Limitation

One distillation depth (3) and one support floor (200). A different distillation
or a leaf-rule extraction from the forest could behave differently; those were
not tested.
