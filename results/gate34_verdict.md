# Gate 34 verdict — keep 5 cross-fitting folds

Pre-registration: `results/gate34_PREREGISTRATION.md`. 20 fresh seeds per DGP
(930100–930119), n = 8,000, identical data and partitions; only `n_splits`
changes.

## Result

| DGP | folds | bias | coverage | MAE | ESS | seconds | ΔMAE vs 5 [95% CI] |
|---|---|---|---|---|---|---|---|
| single | 3 | +0.0023 | 95% | 0.0522 | 2,798.7 | 6.7 | +0.0011 [+0.0008, +0.0013] |
| single | **5** | +0.0022 | 95% | **0.0511** | 2,798.9 | 12.4 | — |
| single | 10 | +0.0023 | 95% | 0.0506 | 2,799.0 | 28.2 | −0.0005 [−0.0006, −0.0004] |
| two | 3 | +0.0018 | 95% | 0.0586 | 2,834.8 | 8.8 | +0.0010 [+0.0007, +0.0013] |
| two | **5** | +0.0017 | 95% | **0.0576** | 2,834.9 | 15.6 | — |
| two | 10 | +0.0018 | 95% | 0.0571 | 2,835.0 | 32.8 | −0.0005 [−0.0006, −0.0004] |

## Decision

**Keep 5 folds.** The pre-registered threshold for changing the fold count was a
0.002 MAE improvement. Ten folds improves MAE by 0.0005 — real but one quarter of
the threshold — and costs 2.1–2.3× the time. Three folds is worse by 0.0010–0.0011
and saves time, but does not improve any target. Coverage is 95% in every cell.

The fold count is therefore a **tested design compromise**, not an unexamined
default. The report no longer says five folds is optimal; it says 3 and 10 were
run and five was retained on the pre-registered trade-off.

## What this does not establish

* One nuisance specification and two DGPs.
* The ATE coverage here is 95%; the 92.5% figure elsewhere is the coverage of
  the *selected-rule* effect, a different target.
