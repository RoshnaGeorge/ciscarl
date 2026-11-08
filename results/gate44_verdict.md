# Gate 44 verdict — 730 is the stable horizon across 20 splits

Pre-registration: `results/gate44_PREREGISTRATION.md`. Candidates 730, 845, 965;
20 random 50/25/25 A×E splits, seeds 2024–2043.

## Result

| Horizon | Mean validation LCB | SD | Mean effect | Mean assessment | Mean support | Commit |
|---|---|---|---|---|---|---|
| **730** | **−0.142** | **0.114** | 0.151 | +0.206 | 129 | 5% |
| 845 | −0.167 | 0.185 | 0.194 | +0.251 | 99 | 15% |
| 965 | −0.206 | 0.191 | 0.173 | +0.220 | 134 | 10% |

730 has the highest mean validation LCB and the smallest split-to-split SD.
845 has a higher mean assessment effect (+0.251 vs +0.206) but a worse validation
LCB and more than 1.6× the variability. 965 is the worst on both mean LCB and SD.

**Decision:** keep 730 days. This is not a defence of the old value; it is the
result of the 20-split stability comparison. The single-split 965 and
discovery-only 845 advantages do not reproduce. 845 remains a sensitivity with a
higher assessment mean, but it is less stable and does not meet the validation
criterion as often.

No horizon meets the commitment threshold on average; the model abstains across
all three. The horizon choice does not change the practical decision.
