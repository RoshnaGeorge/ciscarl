# CISCaRL v2 — implementation status

Frozen specification: **CISCaRL v1.0** (architecture and estimator frozen; validation pending).

This directory contains **only what the frozen spec allows at this stage**: the
estimator and the validation gate. Nothing here discovers rules, produces a rule
list, or claims superiority over SCRE — those are Gates 2–4.

| Gate | Artifact | Status |
|---|---|---|
| 1. Estimator bias + coverage under four censoring mechanisms | `gate1.py` | implemented, run — **partial pass** |
| 1b. Weight stabilisation / truncation strategy | `gate1b.py` | implemented, run — **cap chosen** |
| 1-verify. Cap through the outer cross-fitting pipeline | `gate1_verify.py` | implemented, run — **6/6 PASS** |
| 1c. Non-PH (crossing hazards) gate | `gate1c.py` | implemented, run — **see verdict** |
| 2. Rule-level inference after selection | `gate2.py` | run — 88.3 % on 103 rules, **under-powered** |
| 2b. EIF-corrected intervals | `gate2b.py` | run — **93.1–93.4 % on 333 rules; EIF adds 0.3 pp** |
| 2c. Stability-threshold sweep | `gate2c.py` | run — **threshold frozen at 0.50** |
| 2d. Application-matched sample size (n = 589) | `gate2d.py` | run — 87 % abstention; TREAT precision 100 % **but artefactual** |
| 2e. Decision-layer diagnosis + threshold sweep | `gate2e.py` | run — **STOP: power-limited, not threshold-fixable** |
| 3. Delta sensitivity recovery under known MNAR | `gate3.py` | run — **specified μ-tilt fails; weight tilt works** |
| 4. CISCaRL vs SCRE, matched splits | `gate4.py` | run — model-class dependence, no universal winner |
| 4c. Crossing hazards vs **real** SCRE | `gate4c.py` | run — SCRE bias −77…−98 % of τ, persists across α |
| 4d. Piecewise-constant DGP | `gate4d.py` | run — rule-shaped advantage NOT supported at n≤2000 |
| 4e. Causal/variance-normalised split criterion | `gate4e.py` | run — **no improvement; criterion ruled out** |
| 4f. Large-n recoverability | `gate4f.py` | run — RF Jaccard 0.87, stability 47.5 % at n=8000 |
| 4g. Final validation, fair oracle | `gate4g.py` | run — **stability 62 % at n=12000, matches oracle** |
| 5. Subgroup-level MNAR sensitivity | `gate5.py` | run — verdicts stable over δ∈[−2,2]; **the cap confers it** |
| ACTG175 discontinuation semantics | `results/actg175_estimand.md` | **resolved — endpoint is a composite, estimand is on-treatment** |

Results: `results/gate1_verdict.md`, `results/gate1b_verdict.md`,
`results/gate1c_verdict.md`, `results/gate1_verify_summary.md`.

---

## Frozen decisions encoded in code

| Decision | Where |
|---|---|
| t\* = 730 days | `dgp.TSTAR`, `gate1 --t-star` |
| Known propensity e = 0.5 | hard-coded in `estimators.aipw` call sites |
| Per-arm survival model, cross-fitted | `estimators.crossfit_nuisances` |
| Conditional censoring model (per-arm Cox on X) | `crossfit_nuisances` → `G_cond` |
| Marginal KM censoring retained as **sensitivity row** | `G_marg` |
| AIPW subgroup estimator, not `mean(ψ)` | `estimators.aipw`, `aipw_subgroup` |
| Y_IPCW = 1{T̃ > t\*}/Ĝ(t\*|X) | `estimators.ipcw_outcome` |
| **Weight cap = min(99th pct of fold-training weights, 20)** | `gate1b.py` (amended after Gate 1b) |
| Intervals: conditional on the selected rule list | Gate 2 (not yet) |
| Selection uncertainty reported separately | Gate 2 (not yet) |

---

## What Gate 1 does

For each of four censoring mechanisms × three censoring intensities (10 %, 25 %,
50 % censoring before t\*), over 200 replications:

1. Resample n = 600 covariate vectors **from the real ACTG175 matrix**
   (preserves the observed correlation structure and marginals).
2. Randomise treatment A ~ Bernoulli(0.5).
3. Generate Cox event times with a known, analytic truth S_a(t\*|X).
4. Generate censoring under the mechanism.
5. Estimate τ = E[S_1(t\*) − S_0(t\*)] four ways and compare to the truth.

**Mechanisms**

| # | Name | What it tests |
|---|---|---|
| 1 | `independent` | baseline; must be unbiased |
| 2 | `covariate` | C depends on X — the ACTG175-like case |
| 3 | `event` | C depends on the **latent** event time |
| 4 | `frailty` | shared unmeasured Gamma frailty — the discontinuation analogue |

**Estimators**

| Name | Description |
|---|---|
| `aipw_cond` | **primary**: conditional per-arm Cox censoring model |
| `aipw_marg` | marginal KM censoring (sensitivity) |
| `aipw_oracle` | true G(t\*|X) — ceiling (not available for mechanism 3) |
| `cox_ph` | Cox T-learner (SCRE's estimator family, not SCRE) |

---

## Pre-registered criteria

- **PASS** if, under mechanisms 1–2 with `aipw_cond`: `|bias| < 0.01` **and**
  95 % coverage within [93 %, 97 %].
- Monotone bias growth under mechanisms 3–4 is a pre-declared *hypothesis*,
  not a theorem.
- Coverage is reported with its Monte Carlo SE (`sqrt(p(1-p)/R)`, ≈ 1.5 pp at
  R = 200); a single 92.5 % observation is not treated as definitive failure.

---

## Run

```bash
python -m ciscarl2.gate1 --reps 200          # full gate (~15 min, 20 workers)
python -m ciscarl2.gate1 --quick --reps 8    # smoke test
```

Outputs:

- `results/gate1_replications.csv` — one row per (mechanism, intensity, rep, estimator)
- `results/gate1_summary.csv` — aggregated metrics with MC SEs
- `results/gate1_summary.md` — readable table

---

## Deliberate implementation choices (and why)

**The nuisance survival model is Cox, not RSF, inside Gate 1.**
The simulation DGP is Cox, so a Cox nuisance is correctly specified. Gate 1
isolates the effect of the *censoring* model; letting outcome-model error in
would confound the comparison. The frozen RSF specification applies to the
ACTG175 application, not to this gate. `crossfit_nuisances(..., mu_model="rsf")`
is available for the realistic-learner check.

**`step_value`, not `np.interp`.**
Kaplan–Meier and Cox baseline survival are right-continuous step functions.
Linear interpolation between event times returns a value *below* S(t\*) and
biases every nuisance downward. All survival predictions go through
`step_value`.

**The Cox comparator's SE is bootstrapped, not delta-method.**
A delta method that conditions on the Breslow baseline understates the SE by
roughly 3× (measured: 0.0115 vs 0.0372 bootstrap) because the baseline, not the
coefficients, dominates a survival contrast at a fixed horizon. The comparator
is bootstrapped on the first 60 reps per cell; its point estimate is computed on
all 200. Coverage for `cox_ph` is therefore based on 60 reps and reported with
an explicit `cov_reps` count.

**Weight diagnostics are a result, not a nuisance.**
Max weight, 99th-percentile weight, ESS and the fraction above the cap of 10 are
recorded per replication. Under mechanisms 3–4 the weight tail is the mechanism
by which the estimator degrades; that is what the gate is meant to show.

---

## Known gaps in this artifact

- `delta = 0` reproduction and the arm-specific delta adjustment are **not**
  implemented (Gate 3).
- Rule discovery, stability selection, pruning, Holm correction and the
  three-way verdict are **not** implemented (Gates 2 and 4).
- The ACTG175 application is not run: the estimand interpretation depends on
  resolving the discontinuation/follow-up semantics of `days`, `cens`, `offtrt`.
