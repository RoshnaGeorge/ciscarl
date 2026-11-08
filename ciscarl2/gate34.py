"""Gate 34 - number of cross-fitting folds.

Pre-registration: `results/gate34_PREREGISTRATION.md`.

Compares 3, 5 and 10 folds on the same simulated data. The nuisance models,
target and partitions are held fixed; only `n_splits` changes.

Usage
-----
    python -m ciscarl2.gate34 --reps 1 --start 930900   # smoke
    python -m ciscarl2.gate34 --reps 20 --jobs 8
"""
from __future__ import annotations

import argparse
import os
import time

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from . import dgp
from .estimators import aipw, crossfit_nuisances
from .gate2 import pseudo_outcome
from .gate4d import TSTAR, _delta_for
from .gate20 import _capped_G
from .gate23 import E1, E2, _boot, _config23, _regions
from .gate26 import _calibrate_kind, _sim_kind

from .paths import data_path

DATA = data_path()
START = 930100
KINDS = ("single", "two")
FOLDS = (3, 5, 10)
N = 8000


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
    disc, _ = train_test_split(ii, test_size=0.5, random_state=seed,
                               stratify=A)
    XD, AD, TD, ED = X[disc], A[disc], T[disc], E[disc]
    tau_d = tau_i[disc]

    rows = []
    for k in FOLDS:
        t0 = time.time()
        mu, GD, Gmarg, fid, fcaps, _ = crossfit_nuisances(
            XD, AD, TD, ED, TSTAR, n_splits=k, seed=seed,
            return_folds=True)
        G = _capped_G(mu, GD, Gmarg, fid, fcaps, "conditional", TD)
        psi = pseudo_outcome(AD, TD, TSTAR, mu, G)
        tau, se, _, _ = aipw(XD, AD, TD, TSTAR, mu, G)
        elapsed = time.time() - t0

        mae = float(np.abs((mu[:, 1] - mu[:, 0]) - tau_d).mean())
        lo, hi = tau - 1.96 * se, tau + 1.96 * se
        covered = bool(lo <= tau_d.mean() <= hi)
        w = np.where(TD > TSTAR, 1.0, 0.0) / G
        ess = float((w.sum() ** 2) / (w ** 2).sum()) if (w ** 2).sum() else 0.0
        rows.append(dict(rep=rep, kind=kind, folds=k, n=N,
                         tau=tau, tau_true=float(tau_d.mean()),
                         bias=tau - float(tau_d.mean()), se=se,
                         covered=covered, mae=mae, ess=ess,
                         seconds=elapsed))
    return rows


def summarise(raw):
    out = []
    for kind in sorted(raw.kind.unique()):
        g = raw[raw.kind == kind]
        base = g[g.folds == 5].set_index("rep")
        for k in FOLDS:
            d = g[g.folds == k].set_index("rep")
            common = sorted(set(base.index) & set(d.index))
            diff = (d.loc[common, "mae"] - base.loc[common, "mae"]).to_numpy()
            lo, hi, p = _boot(diff, seed=3)
            out.append(dict(
                kind=kind, folds=k, reps=len(d),
                bias=d.bias.mean(), abs_bias=d.bias.abs().mean(),
                coverage=100 * d.covered.mean(), mae=d.mae.mean(),
                ess=d.ess.mean(), seconds=d.seconds.mean(),
                d_mae=float(diff.mean()), lo=lo, hi=hi, p=p))
    return pd.DataFrame(out)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=20)
    ap.add_argument("--start", type=int, default=None)
    ap.add_argument("--jobs", type=int, default=8)
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
    raw.to_csv(os.path.join(root, "results", "gate34_replications.csv"),
               index=False)
    res = summarise(raw)
    res.to_csv(os.path.join(root, "results", "gate34_summary.csv"), index=False)

    print(f"\n=== Gate 34, folds, {args.reps} reps ===")
    print(res.round(4).to_string(index=False))
    return raw, res


if __name__ == "__main__":
    main()
