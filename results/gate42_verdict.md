# Gate 42 verdict — 965 is the single-split validation optimum, not the stable one

Pre-registration: `results/gate42_PREREGISTRATION.md`. Dense grid 365–1,095 in
30-day steps; maximize validation LCB subject to ≥100 events, ≥30% at risk and
support ≥60.

## Single-split optimum

| Horizon | Events | At risk | Support | Val. effect | Val. LCB | Assessment |
|---|---|---|---|---|---|---|
| 845 | 122 | 64.5% | 79 | +0.114 | −0.200 | +0.498 |
| 935 | 135 | 56.2% | 61 | +0.374 | −0.029 | +0.321 |
| **965** | 138 | 52.6% | 61 | +0.427 | **−0.000** | +0.200 |
| 730 | 99 | 70.8% | 61 | +0.116 | −0.250 | +0.401 |

On this one split, 965 has the highest validation LCB. Its assessment effect is
+0.200, still positive but smaller than 730's +0.401. The LCB is essentially
zero, so the commitment rule still abstains.

**Decision:** 965 is the single-split validation optimum, not yet the final
choice. Gate 43 (discovery-only) and Gate 44 (20-split stability) are the
tie-breakers.
