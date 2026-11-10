# CISCaRL — reproducible final project

Support-constrained interpretable survival subgroup discovery on ACTG175.

## What this is

The final model is **C200-I**:

- estimand: `tau(730 | x) = S1(730 | x) - S0(730 | x)`, composite progression-free endpoint,
  treatment-policy strategy;
- nuisances: per-arm Cox + conditional censoring Cox, 5-fold cross-fit;
- estimator: AIPW;
- learner: depth-3 CART, `min_samples_leaf=60`, squared error;
- selection: maximum discovery mean with support >= 200 (fallback flagged);
- commitment: validation one-sided 95% LCB > 0;
- prediction calibration: isotonic (Gate 33 confirmation);
- interval: influence function;
- horizon: 730 days (Gate 44 stability).

On ACTG175 the support floor cannot be met: the fallback rule is
`cd40 <= 407.5 & wtkg > 71.0 & homo <= 0.5` (support 61), validation
`+0.116` (SE 0.222, LCB `-0.250`), so the model **abstains**.

## Layout

```text
ACTG175.csv                 raw data at root (also data/ACTG175.csv)
data/ACTG175.csv            data used by ciscarl2.paths
ciscarl2/                   pipeline and gates 1-44
ciscarl2/external/scre.py   external SCRE comparator
notebooks/CISCaRL_31_steps.ipynb   31-step executable record
results/                    canonical results, claims, gate evidence
paper/                      engineering report, detailed IEEE paper, figures
run_all.py                  one-command re-run of the final evidence
```

## Install

```bash
python -m pip install -r requirements.txt
```

Python 3.11 is required. PDF export of the Word paper uses Microsoft Word COM on
Windows; the `.docx` sources are included if Word is not available.

## Run the notebook

```bash
jupyter nbconvert --to notebook --execute --inplace notebooks/CISCaRL_31_steps.ipynb
```

The notebook loads the saved evidence by default (`RUN_HEAVY = False`) and
executes in about 1-2 minutes.

## Re-run the final evidence

```bash
python run_all.py --dry-run     # list the commands
python run_all.py --quick       # smoke: 1 rep per gate, ~13 min
python run_all.py               # full: hours, rewrites results/
python run_all.py --only 33     # one gate group
python run_all.py --paper       # also rebuild the Word paper
```

The full run first copies `results/` to a timestamped folder in the system temp
directory, so the old evidence survives a crash. `--quick` runs in a temporary
sandbox and never touches `results/`.

`run_all.py` runs the notebook and the gates behind the final paper:

- Gate 23 (support), 28 (SCRE head-to-head), 30 (knob sweep), 31 (nuisance),
  32 (learners), 33 (calibration/intervals + confirmation), 34 (folds),
  35 (fairness/SHAP/transport), 36 (TMLE), 37 (horizon), 38 (features),
  39 (learned stacking), 40 (SCRE alpha path), 41 (selection-aware intervals),
  42-44 (horizon optimisation and stability), 45-47 (CART tuning and ensembles).

Gates 1-22 are historical evidence; run any of them directly, for example:

```bash
python -m ciscarl2.gate18 --reps 40
python -m ciscarl2.gate23 --reps 40
```

The 40-page engineering report is a delivered document, not a generated one;
its numbers are reproduced by the gates and checked against
`results/CANONICAL_RESULTS.md`. The detailed IEEE paper has a builder
(`paper/build_ieee_detailed.py`) and can be regenerated from the same evidence.

## Seeds

| Block | Seeds |
|---|---|
| split | 2024, 2025 |
| Gate 31 | 900100–900119 |
| Gate 32 | 910100–910119 |
| Gate 33 | 920100–920119; confirmation 921100–921119 |
| Gate 34 | 930100–930119 |
| Gate 36 | 940100–940119 |
| Gate 41 | 950100–950119 |
| Gate 40 | 960100–960109 |
| Gate 39 | 970100–970109 |
| Gate 44 | 2024–2043 |
| Gate 45 | ACTG175 discovery; split seeds 2024/2025 |
| Gate 46 | 980100–980119 |
| Gate 47 | 990100–990119 |
| policy | 700100 |
| SCRE head-to-head | 300100–300139 |
| Gate 30 tuning / confirmation | 310100–310139 / 320100–320139 |

## Key files

- `results/CANONICAL_RESULTS.md` — single source of truth for every reported number.
- `results/CLAIMS_v1.17.md` — defensible and withdrawn claims.
- `results/EVIDENCE_EXTENSION.md` — Gates 31-44 summary.
- `paper/CISCaRL_Engineering_Report_v2.docx` — 40-page engineering report.
- `paper/CISCaRL_IEEE_conference_detailed.docx` — 8-page IEEE-style paper.
- `paper/figs/` — all paper figures.
- `paper/make_paper_figures.py` — regenerate figures from `results/`.
- `paper/build_ieee_detailed.py` — rebuild the detailed Word paper.

## Known limits

- ACTG175 has no individual treatment-effect truth; purity/capture/MAE come from simulation.
- The rule is unstable: 20 distinct rules from 20 splits, Jaccard ~0.34.
- The IF interval conditions on the selected rule; coverage is 90-95%.
- Fairness is underpowered: every race/gender group has < 30 rule patients.
- PBC external validation is out of scope by the ACTG175-only protocol.
- Longitudinal TMLE was removed; fixed-horizon IPCW-TMLE was tested and rejected.
