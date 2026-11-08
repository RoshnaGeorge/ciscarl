"""Gate 40 - SCRE full alpha-path sensitivity.

Pre-registration: `results/gate40_PREREGISTRATION.md`.

One SCRE fit per replication; every alpha on the Coxnet path is evaluated on the
same assessment patients. The validation-concordance alpha is marked.

Usage
-----
    python -m ciscarl2.gate40 --reps 2 --start 960900   # smoke
    python -m ciscarl2.gate40 --reps 10 --jobs 6
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import argparse
import contextlib
import io
import sys

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from . import dgp
from .estimators import aipw, crossfit_nuisances
from .gate2 import pseudo_outcome
from .gate4 import scre_select_alpha
from .gate4d import TSTAR, _delta_for
from .gate20 import _capped_G
from .gate23 import E1, E2, _config23, _regions
from .gate26 import _calibrate_kind, _sim_kind

from .paths import data_path

DATA = data_path()

try:
    from .external.scre import SurvivalCausalRuleEnsemble
except Exception as exc:  # pragma: no cover
    SurvivalCausalRuleEnsemble = None
    print("SCRE import failed:", exc)

START = 960100
KINDS = ("single", "two")
N = 8000
N_ALPHA = 12


def _metrics(tau, truth, union):
    treated = tau > 0
    k = int(treated.sum())
    if k == 0:
        return dict(mae=float(np.abs(tau - truth).mean()), purity=np.nan,
                    capture=0.0, per_treated=np.nan, coverage=0.0)
    return dict(
        mae=float(np.abs(tau - truth).mean()),
        purity=float((treated & union).sum() / k),
        capture=float(truth[treated].sum() / truth.sum()),
        per_treated=float(truth[treated].mean()),
        coverage=float(treated.mean()),
    )


def run_rep(rep, kind, cfg, lam_c):
    if SurvivalCausalRuleEnsemble is None:
        return []
    seed = START + rep
    rng = np.random.RandomState(seed)
    pool = cfg[0]
    lam0 = cfg[5]
    X = pool[rng.choice(len(pool), N, replace=True)]
    R1, R2 = _regions(X, cfg)
    if kind == "single":
        R2 = np.zeros(len(X), bool)
    union = R1 | R2
    lp0 = X @ dgp.BETA
    s0 = np.exp(-lam0 * TSTAR * np.exp(lp0))
    e1 = np.where(R1, _delta_for(E1, s0), 0.0)
    e2 = np.where(R2, _delta_for(E2, s0), 0.0)
    A = rng.binomial(1, 0.5, len(X))
    sim = _sim_kind(X, A, lam_c, lam0, rng, e1, e2)
    T, E = sim["Tobs"], sim["E"]
    tau_i = sim["S1"] - sim["S0"]

    ii = np.arange(len(X))
    disc, hold = train_test_split(ii, test_size=0.5, random_state=seed,
                                  stratify=A)
    val, asm = train_test_split(hold, test_size=0.5, random_state=seed + 1,
                                stratify=A[hold])
    XD, AD, TD, ED = X[disc], A[disc], T[disc], E[disc]
    XV, AV, TV, EV = X[val], A[val], T[val], E[val]
    XA, AA, TA, EA = X[asm], A[asm], T[asm], E[asm]
    uniA, truth = union[asm], tau_i[asm]

    muD, GD, Gmarg, fid, fcaps, _ = crossfit_nuisances(
        XD, AD, TD, ED, TSTAR, seed=seed, return_folds=True)
    G = _capped_G(muD, GD, Gmarg, fid, fcaps, "conditional", TD)
    psi = pseudo_outcome(AD, TD, TSTAR, muD, G)

    s = SurvivalCausalRuleEnsemble(
        alpha=0.5, pred_n_estimators=100, progn_n_estimators=100,
        rule_min_support=20, max_rules=200, max_rule_conditions=3,
        max_selected_rules=10, random_state=42)
    with contextlib.redirect_stdout(io.StringIO()):
        s.fit(XD, psi, np.isfinite(psi),
              feature_names=[f"x{i}" for i in range(XD.shape[1])],
              time=TD, event=ED.astype(bool), treatment=AD)
        pick = scre_select_alpha(s, XV, AV, TV, EV.astype(bool), TSTAR)
    chosen_alpha = float(pick[1]) if pick is not None else float(s.alpha_final_)
    alphas = np.asarray(s.model_.alphas_, float)
    idx = np.unique(np.linspace(0, len(alphas) - 1, N_ALPHA).astype(int))
    p = XD.shape[1]
    n_rules_total = len(s.candidates_)
    start_rz = 2 * p + n_rules_total

    rows = []
    for i in idx:
        a = float(alphas[i])
        s.alpha_final_ = a
        with contextlib.redirect_stdout(io.StringIO()):
            tau = np.asarray(s.predict(XA), float)
        if not np.all(np.isfinite(tau)):
            continue
        m = _metrics(tau, truth, uniA)
        coef, _ = s.model_._get_coef(a)
        n_sel = int(np.sum(np.abs(coef[start_rz:start_rz + n_rules_total]) > 1e-6))
        rows.append(dict(rep=rep, kind=kind, alpha=a, n_rules=n_sel,
                         chosen=bool(abs(a - chosen_alpha) < 1e-12), **m))
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=10)
    ap.add_argument("--start", type=int, default=None)
    ap.add_argument("--jobs", type=int, default=6)
    args = ap.parse_args(argv)

    global START
    if args.start is not None:
        START = args.start
    cfg = _config23()
    lam = {k: _calibrate_kind(cfg, k) for k in KINDS}

    from joblib import Parallel, delayed
    jobs = [(rep, kind) for kind in KINDS for rep in range(args.reps)]
    out = Parallel(n_jobs=args.jobs, verbose=5)(
        delayed(run_rep)(rep, kind, cfg, lam[kind]) for rep, kind in jobs)

    raw = pd.DataFrame([r for ch in out for r in ch])
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw.to_csv(os.path.join(root, "results", "gate40_alpha_path.csv"), index=False)
    if raw.empty:
        print("No SCRE results; check SCRE_PATH.")
        return raw

    rows = []
    for (kind, rep), g in raw.groupby(["kind", "rep"]):
        # rule-bearing path only, so "no rules" constant models do not win
        rules = g[g.n_rules > 0].copy()
        if rules.empty:
            continue
        best = rules.loc[rules.mae.idxmin()]
        pick = g[g.chosen]
        rows.append(dict(
            kind=kind, rep=rep, n_alphas=len(g),
            best_alpha=best.alpha, best_mae=best.mae,
            best_purity=best.purity, best_capture=best.capture,
            chosen_alpha=(pick.alpha.iloc[0] if len(pick) else np.nan),
            chosen_mae=(pick.mae.iloc[0] if len(pick) else np.nan),
            chosen_purity=(pick.purity.iloc[0] if len(pick) else np.nan),
            chosen_capture=(pick.capture.iloc[0] if len(pick) else np.nan),
            path_mae_min=rules.mae.min(), path_mae_max=rules.mae.max(),
            path_purity_min=rules.purity.min(), path_purity_max=rules.purity.max(),
            path_capture_min=rules.capture.min(), path_capture_max=rules.capture.max(),
        ))
    per_rep = pd.DataFrame(rows)
    per_rep.to_csv(os.path.join(root, "results", "gate40_path_summary.csv"),
                   index=False)
    summ = (per_rep.groupby("kind")
            .agg(reps=("rep", "size"),
                 best_mae=("best_mae", "mean"),
                 chosen_mae=("chosen_mae", "mean"),
                 best_purity=("best_purity", "mean"),
                 chosen_purity=("chosen_purity", "mean"),
                 best_capture=("best_capture", "mean"),
                 chosen_capture=("chosen_capture", "mean"),
                 mae_min=("path_mae_min", "mean"),
                 mae_max=("path_mae_max", "mean"),
                 purity_min=("path_purity_min", "mean"),
                 purity_max=("path_purity_max", "mean"),
                 capture_min=("path_capture_min", "mean"),
                 capture_max=("path_capture_max", "mean"))
            .reset_index())
    summ.to_csv(os.path.join(root, "results", "gate40_summary.csv"), index=False)

    print(f"\n=== Gate 40, SCRE alpha path, {args.reps} reps ===")
    print(summ.round(4).to_string(index=False))
    return raw


if __name__ == "__main__":
    main()
