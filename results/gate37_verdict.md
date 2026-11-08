# Gate 37 verdict — 730 days is retained as a documented compromise

Pre-registration: `results/gate37_PREREGISTRATION.md`. ACTG175, discovery and
validation only; assessment is descriptive.

| Horizon | Events | At risk | Support | Val. effect | Val. SE | Val. LCB | Assessment |
|---|---|---|---|---|---|---|---|
| 365 | 46 | 87.5% | 77 | +0.171 | 0.091 | +0.021 | +0.017 |
| 548 | 69 | 80.6% | 109 | +0.219 | 0.108 | +0.042 | +0.083 |
| **730** | 99 | 70.8% | 61 | +0.116 | 0.222 | −0.250 | +0.401 |
| 912 | 135 | 57.9% | 61 | +0.348 | 0.239 | −0.044 | +0.319 |
| 1,095 | 143 | 21.8% | 237 | −0.162 | 0.215 | −0.516 | +0.575 |

No horizon satisfies all four pre-registered criteria: ≥150 events, ≥30% at
risk, validation SE within 0.02 of 730, and support ≥200 or a documented
fallback ≥60.

- 365 and 548 have positive LCBs but only 46 and 69 events.
- 1,095 has 51% censored and only 22% at risk.
- 912 has 135 events but its LCB is −0.044.
- 730 has 99 events, 71% at risk, and a fallback rule at support 61.

**Decision:** keep 730 days as a documented compromise, not an experimentally
demonstrated optimum. The horizon remains a design choice with an explicit
limitation.
