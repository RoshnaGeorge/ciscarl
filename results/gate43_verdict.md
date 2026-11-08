# Gate 43 verdict — discovery-only inner CV selects 845, conflicting with validation

Pre-registration: `results/gate43_PREREGISTRATION.md`. 5-fold inner CV inside
discovery; mean held-out one-sided LCB.

## Result

| Horizon | Events | At risk | Inner LCB | Inner SD | Support |
|---|---|---|---|---|---|
| 725 | 96 | 71.7% | −0.118 | 0.161 | 98 |
| 755 | 105 | 69.3% | −0.097 | 0.158 | 76 |
| 815 | 113 | 66.8% | −0.110 | 0.219 | 65 |
| **845** | 122 | 64.5% | **+0.014** | 0.172 | 65 |
| 875 | 124 | 63.0% | +0.007 | 0.396 | 65 |
| 905 | 133 | 59.0% | −0.188 | 0.189 | 71 |
| 965 | 138 | 52.6% | −0.265 | 0.372 | 77 |

Discovery-only inner CV selects **845 days** (+0.014), not 965 (−0.265). This
conflicts with the single-split validation optimum.

On the full split, 845 gives validation LCB −0.200 and assessment effect +0.498
(from the Gate 42 grid). It does not meet the commitment threshold.

**Decision:** 845 is the discovery-only optimum, not the final choice. The
conflict between 845 and 965 is exactly why Gate 44 repeats the comparison over
20 splits.
