# Gate 41 verdict — IF interval retained; selection-aware alternatives are validated sensitivities

Pre-registration: `results/gate41_PREREGISTRATION.md`. 20 seeds per DGP.

| DGP | Method | Coverage | Width | Width / IF |
|---|---|---|---|---|
| single | IF | 95% | 0.298 | 1.00 |
| single | Bonferroni | 100% | 0.412 | 1.38 |
| single | sample-splitting | 100% | 0.298 | 1.00 |
| two | IF | 100% | 0.297 | 1.00 |
| two | Bonferroni | 100% | 0.412 | 1.39 |
| two | sample-splitting | 100% | 0.294 | 0.99 |

Both selection-aware methods meet the pre-registered coverage and width
criteria. Bonferroni is conservative (1.38–1.39× width). Sample-splitting has the
same width but reports a rule selected on half of discovery, so it is a different
estimand from the full-discovery C200 rule.

**Decision:** keep the IF interval as the primary interval. It already reaches
95–100% coverage in this run and is narrower than Bonferroni. Report Bonferroni
and sample-splitting as validated selection-aware sensitivities. The IF interval
still conditions on the selected rule; the limitation is not removed, it is
quantified.
