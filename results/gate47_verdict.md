# Gate 47 — CART tuning on simulated subgroup performance

Question: which CART configuration gives the best **subgroup**, not the best
pseudo-outcome fit?

Grid: depth 2–5 × leaf 20, 30, 40, 60, 80, 100 × squared_error, absolute_error =
**48 configurations**, 20 replications × 2 DGPs. Nuisances are fitted once per
replication; every configuration is evaluated on the same validation and
assessment patients.

Selection rule, fixed before the run: maximise mean validation LCB subject to
mean purity ≥ 0.75, mean capture ≥ 0.20 and mean conditions ≤ 3. Ties within
0.01 LCB go to the simpler tree.

## Result

| DGP | configuration | purity | capture | Jaccard | LCB | MAE |
|---|---|---|---|---|---|---|
| single | depth 2 / absolute_error | 0.816 | 0.770 | 0.644 | **+0.0605** | 0.0540 |
| single | depth 3 / leaf 60 / absolute_error | 0.865 | 0.556 | 0.523 | +0.0509 | 0.0588 |
| single | **frozen 3 / 60 / squared_error** | 0.856 | 0.517 | 0.484 | +0.0300 | 0.0589 |
| two | depth 2 / absolute_error (leaf 40) | 0.831 | 0.515 | 0.404 | **+0.0731** | 0.0697 |
| two | depth 3 / leaf 60 / absolute_error | 0.817 | 0.330 | 0.274 | +0.0535 | 0.0751 |
| two | **frozen 3 / 60 / squared_error** | 0.786 | 0.386 | 0.301 | +0.0204 | 0.0748 |

Paired against the frozen configuration:

* depth 2 / absolute_error: capture **+0.253 [+0.116, +0.390]** in one region and
  **+0.128 [+0.021, +0.230]** in two; LCB **+0.031 [−0.007, +0.070]** and
  **+0.052 [+0.025, +0.076]**; purity −0.040 in one region (CI includes zero)
  and +0.044 in two.
* depth 3 / leaf 60 / absolute_error: LCB +0.021 [−0.016, +0.057] and
  **+0.033 [+0.009, +0.060]**; capture +0.039 [−0.117, +0.188] and
  **−0.056 [−0.147, +0.028]**.

The depth-2 / absolute-error tree is the best configuration under the
pre-registered simulation rule.

## Real-data check

The same canonical split (527 / 263 / 264) and pipeline were run for the leading
configurations (`results/gate47_actg175.csv`):

| configuration | support | validation | LCB | assessment | decision |
|---|---|---|---|---|---|
| **frozen 3/60/squared** | 61 | +0.116 | −0.250 | +0.401 | INSUFFICIENT |
| 3/60/absolute | 62 | −0.097 | −0.408 | +0.137 | INSUFFICIENT |
| 3/80/absolute | 122 | +0.039 | −0.210 | +0.282 | INSUFFICIENT |
| 2/60/absolute | 122 | +0.039 | −0.210 | +0.282 | INSUFFICIENT |
| 2/40/absolute | 122 | +0.039 | −0.210 | +0.282 | INSUFFICIENT |
| 4/30/absolute | 35 | +0.523 | +0.175 | +0.092 | fallback, support 35 |

The simulation winner does not transfer into a better deployable subgroup:
on ACTG175 it selects 122 patients, its validation bound is −0.210 and the model
still abstains. The only configuration that commits is a 35-patient fallback leaf
with assessment effect +0.092, which is below the support floor by design.

## Decision

**Keep the frozen CART (depth 3, leaf 60, squared error).** The simulation result
is reported as evidence that average LCB and capture favour a simpler tree, but
that tree does not produce a certifiable subgroup on the real trial. The project
does not adopt a model that cannot meet its own support and commitment rules.

## Limitation

The real-data check is one split and descriptive; the simulation result is the
formal comparison. A broader real-data split study could change the read-out.
