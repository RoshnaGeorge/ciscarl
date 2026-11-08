# Gate 36 pre-registration — fixed-horizon IPCW-TMLE vs AIPW

Frozen before execution. This gate implements the one estimator alternative still
listed as proposed. It is a **fixed-horizon IPCW-TMLE**, not the longitudinal
TMLE over the whole survival curve: the target is S(730 | X, A), the outcome is
the binary event-free indicator at 730, and the clever covariate uses the
censoring weight at 730.

## Question

Does a targeted update of the initial Cox nuisances improve the AIPW contrast on
bias, coverage, patient-level MAE, or the downstream C200 subgroup?

## Estimators

| id | estimator |
|---|---|
| `aipw` | cross-fitted AIPW with the initial Cox nuisances (frozen) |
| `tmle` | same initial nuisances, targeted by a logistic fluctuation |

## TMLE construction

For arm $a$ with $e_a=P(A=a)$:

- initial $\mu_a(X)=P(T>730\mid X,A=a)$;
- binary outcome $Y=\mathbf{1}\{T_{\text{obs}}>730\}$;
- censoring weight $G(X)=P(C>730\mid X)$;
- clever covariate $H_a=\mathbf{1}\{A=a\}/e_a \cdot Y/G$;
- fluctuation $\mu_a^*(X)=\operatorname{expit}(\operatorname{logit}(\mu_a(X))+\epsilon_a H_a)$;
- $\epsilon_a$ solves $\sum_i H_{a,i}(Y_i-\mu_{a,i}^*)=0$;
- $\hat\psi_a=\frac1n\sum_i \mu_a^*(X_i)$ and $\hat\tau_{\text{TMLE}}=\hat\psi_1-\hat\psi_0$.

The patient-level target for the C200 tree is the AIPW pseudo-outcome evaluated
at the targeted nuisances:
$\psi_i=\mu_1^*-\mu_0^*+A/e(Y_{\text{IPCW}}-\mu_1^*)-(1-A)/(1-e)(Y_{\text{IPCW}}-\mu_0^*)$.

## Design

| item | value |
|---|---|
| n | 8,000 |
| partitions | 4,000 discovery / 2,000 validation / 2,000 assessment |
| replications | 20 fresh seeds per DGP, 940100–940119 |
| DGPs | single-region and two-region effects |
| nuisances | per-arm Cox + conditional censoring Cox, 5-fold cross-fit |
| learner | frozen C200 |
| commitment | one-sided 95% LCB > 0 |

## Outcomes

1. AIPW/TMLE bias against the true ATE.
2. 95% influence-function coverage at the targeted nuisances.
3. Patient-level MAE of the contrast.
4. Downstream C200 purity, capture, Jaccard, commitment and assessment MAE.
5. Wall-clock seconds.

## Decision rule

TMLE replaces AIPW only if **all** hold:

1. patient-level MAE improves by at least 0.002 with a paired 95% CI below zero,
   or absolute bias falls by at least 50% with coverage closer to 95%;
2. C200 purity and capture do not fall by more than 0.02;
3. cost is at most 2× AIPW.

Otherwise AIPW is retained. The comparison is paired within replication.

## Failure interpretation

| result | interpretation |
|---|---|
| TMLE is numerically identical to AIPW | the targeting step adds nothing at this horizon; keep AIPW |
| TMLE improves bias but loses purity | do not trade subgroup quality for a bias gain |
| TMLE improves both but costs more | document the cost; do not adopt automatically |
| TMLE fails under two-region truth | the targeting is not the bottleneck |

## Scope

One horizon, two DGPs, one censoring mechanism. This is not a claim about
longitudinal TMLE or about survival curves beyond 730 days.
