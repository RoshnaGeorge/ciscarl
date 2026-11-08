# Gate 41 pre-registration — selection-aware intervals

Frozen before execution. The IF interval conditions on the selected rule. This
gate tests two practical selection-aware alternatives:

1. **Bonferroni over candidate leaves**: adjust the interval for the number of
   leaves considered.
2. **Sample-splitting**: select the rule on one half of discovery and estimate
   its effect on the other half.

## Design

| item | value |
|---|---|
| n | 8,000 |
| partitions | 4,000 discovery / 2,000 validation / 2,000 assessment |
| replications | 20 fresh seeds per DGP, 950100–950119 |
| DGPs | single-region and two-region |
| learner | C200 |
| methods | IF, Bonferroni, sample-splitting |

## Outcomes

1. Coverage of the true effect of the rule being reported.
2. Interval width.
3. Commitment rate.

## Decision rule

Adopt a selection-aware method only if coverage is at least 95% in both DGPs and
width is at most 2× the IF interval. Otherwise retain IF and report the measured
coverage.

## Scope

Bonferroni is conservative and does not model the CART search; sample-splitting
is honest but lower-powered. This gate measures whether either is adequate here,
not a general solution to selective inference.
