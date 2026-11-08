# Gate 40 verdict — the SCRE alpha path does not overturn the head-to-head

Pre-registration: `results/gate40_PREREGISTRATION.md`. 10 seeds per DGP; one SCRE
fit per replication; 12 alpha points evaluated on the same assessment patients.

| DGP | Best MAE | Chosen-alpha MAE | Gap | Best purity | Chosen purity | Best capture | Chosen capture |
|---|---|---|---|---|---|---|---|
| single | 0.0558 | 0.0568 | +0.0010 | 0.421 | 0.410 | 0.968 | 0.983 |
| two | 0.0687 | 0.0704 | +0.0017 | 0.554 | 0.600 | 0.842 | 0.806 |

Path ranges across the 12 alpha points:

- single: MAE 0.0558–0.0792; purity 0.345–0.442; capture 0.911–0.976.
- two: MAE 0.0687–0.0904; purity 0.477–0.605; capture 0.769–0.904.

The validation-concordance alpha is close to the best-MAE alpha (gap 0.0010–
0.0017). The path does not overturn the head-to-head conclusion: SCRE remains the
more accurate patient-level predictor, and its purity/capture trade-off moves
within the ranges already reported. The exact numbers are path-sensitive; the
direction is not.

**Decision:** keep the validation-concordance alpha and report the path range as
a sensitivity. Do not select the best-MAE alpha post hoc — that would use the
assessment partition.
