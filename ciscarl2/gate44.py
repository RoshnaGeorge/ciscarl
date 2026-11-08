"""Gate 44 - horizon stability across 20 splits.

Pre-registration: `results/gate44_PREREGISTRATION.md`.

Candidates: 730, 845, 965. For each split and horizon, fit the frozen pipeline
and record the validation LCB and assessment effect.

Usage
-----
    python -m ciscarl2.gate44 --jobs 6
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import argparse

import numpy as np
import pandas as pd
from scipy.stats import norm, t as tdist
from sklearn.model_selection import train_test_split

from . import dgp
from .estimators import aipw, crossfit_nuisances, phi_on_holdout
from .gate2 import pseudo_outcome
from .gate11 import _cart
from .gate20 import _capped_G
from .gate22 import _stats
from .rules import eval_rule

from .paths import data_path

DATA = data_path()
SUP = 200
HORIZONS = (730, 845, 965)
SEEDS = tuple(range(2024, 2044))
Z95 = float(norm.ppf(0.95))


def _ci(dphi, mask):
    m = dphi[mask]
    n = len(m)
    if n < 5:
        return np.nan, np.nan, np.nan
    eff = float(m.mean())
    se = float(np.sqrt(((m - eff) ** 2).sum()) / n)
    q = float(tdist.ppf(0.975, n - 1))
    return eff, eff - q * se, eff + q * se


def run_one(seed, h):
    raw = pd.read_csv(DATA)
    raw = raw[raw.arms.isin([0, 1])].reset_index(drop=True)
    Xr = raw[dgp.COVARIATES].to_numpy(float)
    A = (raw.arms == 1).to_numpy(int)
    T = raw.days.to_numpy(float)
    E = raw.cens.to_numpy(int)
    idx = np.arange(len(Xr))
    strat = A * 2 + E
    disc, hold = train_test_split(idx, test_size=0.5, random_state=seed,
                                  stratify=strat)
    val, asm = train_test_split(hold, test_size=0.5, random_state=seed + 1000,
                                stratify=strat[hold])
    mu, sd = Xr[disc].mean(0), Xr[disc].std(0)
    sd[sd == 0] = 1.0
    X = (Xr - mu) / sd
    XD, AD, TD, ED = X[disc], A[disc], T[disc], E[disc]
    XV, AV, TV, EV = X[val], A[val], T[val], E[val]
    XA, AA, TA, EA = X[asm], A[asm], T[asm], E[asm]

    muD, GD, Gmarg, fid, fcaps, _ = crossfit_nuisances(
        XD, AD, TD, ED, float(h), seed=seed, return_folds=True)
    G = _capped_G(muD, GD, Gmarg, fid, fcaps, "conditional", TD)
    psi = pseudo_outcome(AD, TD, float(h), muD, G)
    leaves = _cart(psi, XD, 3)[1]
    means, ses, sup = _stats(psi, leaves)
    ok = sup >= SUP
    fallback = not bool(ok.any())
    j = (int(np.nanargmax(np.where(ok, means, -np.inf))) if ok.any()
         else int(np.nanargmax(means)))
    cond = leaves[j]["cond"]

    p1v, p0v = phi_on_holdout(XD, AD, TD, ED, XV, AV, TV, float(h), seed=seed)
    p1a, p0a = phi_on_holdout(XD, AD, TD, ED, XA, AA, TA, float(h), seed=seed)
    ev, lo, hi = _ci(p1v - p0v, eval_rule(cond, XV))
    ea, loa, hia = _ci(p1a - p0a, eval_rule(cond, XA))
    se_v = (hi - lo) / (2 * Z95) if np.isfinite(hi) else np.nan
    lcb = ev - Z95 * se_v if np.isfinite(se_v) else np.nan
    return dict(seed=seed, horizon=h, events=int(((TD <= h) & (ED == 1)).sum()),
                at_risk=float((TD > h).mean()), support=int(sup[j]),
                fallback=fallback, val_effect=ev, val_se=se_v, val_lcb=lcb,
                asm_effect=ea, committed=bool(np.isfinite(lcb) and lcb > 0))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=6)
    args = ap.parse_args(argv)

    from joblib import Parallel, delayed
    jobs = [(s, h) for s in SEEDS for h in HORIZONS]
    out = Parallel(n_jobs=args.jobs, verbose=5)(
        delayed(run_one)(s, h) for s, h in jobs)

    raw = pd.DataFrame(out)
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw.to_csv(os.path.join(root, "results", "gate44_stability.csv"), index=False)
    summ = (raw.groupby("horizon")
            .agg(reps=("seed", "size"),
                 mean_lcb=("val_lcb", "mean"),
                 sd_lcb=("val_lcb", "std"),
                 mean_effect=("val_effect", "mean"),
                 mean_assessment=("asm_effect", "mean"),
                 mean_support=("support", "mean"),
                 commit=("committed", lambda s: 100 * s.mean()))
            .reset_index())
    summ.to_csv(os.path.join(root, "results", "gate44_summary.csv"), index=False)
    print("=== Gate 44, horizon stability (20 splits) ===")
    print(summ.round(3).to_string(index=False))
    best = summ.loc[summ.mean_lcb.idxmax()]
    base = summ[summ.horizon == 730].iloc[0]
    print(f"\nbest mean LCB: {int(best.horizon)} ({best.mean_lcb:+.3f}); "
          f"730 {base.mean_lcb:+.3f}; gain {best.mean_lcb - base.mean_lcb:+.3f}")
    return raw, summ


if __name__ == "__main__":
    main()
