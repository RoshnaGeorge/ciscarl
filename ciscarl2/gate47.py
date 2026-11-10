"""Gate 47 - CART hyperparameter selection on simulated subgroup performance.

Gate 45 tuned by pseudo-outcome prediction error. That is not the same as
finding a good subgroup: a deeper tree can predict psi better yet select a
smaller, less pure leaf. This gate fits one nuisance model per replication and
then evaluates a grid of CART configurations on the identical validation and
assessment patients.

Selection rule, fixed before the run:
    maximise mean validation LCB over 20 splits, subject to
    mean purity >= 0.75, mean capture >= 0.20, mean conditions <= 3.
    Ties within 0.01 LCB go to the simpler tree (smaller depth, larger leaf).

Run:
    python -m ciscarl2.gate47 --reps 20 --jobs 8
Writes:
    results/gate47_replications.csv
    results/gate47_summary.csv
"""
from __future__ import annotations

import argparse
import itertools
import os
import time

import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeRegressor

from . import dgp
from .estimators import aipw, crossfit_nuisances, phi_on_holdout
from .gate2 import pseudo_outcome
from .gate4d import TSTAR, _delta_for
from .gate20 import _capped_G
from .gate23 import E1, E2, _config23, _regions
from .gate26 import _calibrate_kind, _sim_kind
from .gate32 import _as_leaves, _evaluate, _select
from .rules import eval_rule

from .paths import data_path

DATA = data_path()
START = 990100
KINDS = ("single", "two")
N = 8000
SUP = 200
Z95 = float(norm.ppf(0.95))

CONFIGS = list(itertools.product((2, 3, 4, 5), (20, 30, 40, 60, 80, 100),
                                 ("squared_error", "absolute_error")))


def _fit(psi, X, depth, leaf, crit):
    t = DecisionTreeRegressor(max_depth=depth, min_samples_leaf=leaf,
                              criterion=crit, random_state=0).fit(X, psi)
    return _as_leaves(t, X, leaf)


def run_rep(rep, kind, cfg, lam_c):
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
    const = float(aipw(XD, AD, TD, TSTAR, muD, G)[0])
    p1v, p0v = phi_on_holdout(XD, AD, TD, ED, XV, AV, TV, TSTAR, seed=seed)
    p1a, p0a = phi_on_holdout(XD, AD, TD, ED, XA, AA, TA, TSTAR, seed=seed)
    dphi_v, dphi_a = p1v - p0v, p1a - p0a

    rows = []
    for depth, leaf, crit in CONFIGS:
        t0 = time.time()
        leaves = _fit(psi, XD, depth, leaf, crit)
        j, means, sup, fallback = _select(psi, leaves)
        down = _evaluate(leaves, j, psi, XV, XA, dphi_v, const, truth, uniA)

        cond = leaves[j]["cond"]
        mv = eval_rule(cond, XV)
        k = int(mv.sum())
        eff = float(dphi_v[mv].mean()) if k else np.nan
        se = (float(np.sqrt(((dphi_v[mv] - eff) ** 2).sum()) / k)
              if k else np.nan)
        lcb = eff - Z95 * se if np.isfinite(eff) and np.isfinite(se) else np.nan

        rows.append(dict(
            rep=rep, kind=kind, depth=depth, leaf=leaf, criterion=crit,
            purity=down["purity_rule"], capture=down["capture_rule"],
            jaccard=down["jaccard"], mae_assessment=down["mae_assessment"],
            commit=down["committed"], support=down["support"],
            conditions=down["conditions"], fallback=fallback,
            val_eff=eff, val_se=se, val_lcb=lcb,
            seconds=time.time() - t0,
        ))
    return rows


def summarise(raw):
    keys = ["kind", "depth", "leaf", "criterion"]
    return (raw.groupby(keys)
            .agg(reps=("rep", "nunique"),
                 purity=("purity", "mean"),
                 capture=("capture", "mean"),
                 jaccard=("jaccard", "mean"),
                 commit=("commit", "mean"),
                 mae_assessment=("mae_assessment", "mean"),
                 support=("support", "mean"),
                 conditions=("conditions", "mean"),
                 val_lcb=("val_lcb", "mean"),
                 val_eff=("val_eff", "mean"),
                 seconds=("seconds", "mean"))
            .reset_index())


def main(argv=None):
    global START
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=20)
    ap.add_argument("--start", type=int, default=None)
    ap.add_argument("--jobs", type=int, default=8)
    args = ap.parse_args(argv)
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
    raw.to_csv(os.path.join(root, "results", "gate47_replications.csv"),
               index=False)
    res = summarise(raw)
    res.to_csv(os.path.join(root, "results", "gate47_summary.csv"), index=False)

    print(f"\n=== Gate 47, CART tuning on subgroup performance, {args.reps} reps ===")
    cols = ["kind", "depth", "leaf", "criterion", "purity", "capture",
            "jaccard", "commit", "mae_assessment", "val_lcb", "support",
            "conditions", "seconds"]
    print(res.sort_values(["kind", "val_lcb"], ascending=[True, False])
          [cols].head(20).round(4).to_string(index=False))

    print("\nEligible (purity>=0.75, capture>=0.20, conditions<=3), best LCB:")
    for kind in KINDS:
        g = res[(res.kind == kind) & (res.purity >= 0.75) &
                (res.capture >= 0.20) & (res.conditions <= 3)]
        if len(g):
            b = g.sort_values(["val_lcb", "depth", "leaf"],
                              ascending=[False, True, False]).iloc[0]
            print(f"  {kind:>6}: depth={int(b.depth)} leaf={int(b.leaf)} "
                  f"criterion={b.criterion} LCB={b.val_lcb:+.4f} "
                  f"purity={b.purity:.3f} capture={b.capture:.3f}")
        else:
            print(f"  {kind:>6}: no eligible configuration")
    return raw, res


if __name__ == "__main__":
    main()
