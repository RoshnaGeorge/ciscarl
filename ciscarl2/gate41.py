"""Gate 41 - selection-aware intervals: IF vs Bonferroni vs sample-splitting.

Pre-registration: `results/gate41_PREREGISTRATION.md`.

Usage
-----
    python -m ciscarl2.gate41 --reps 2 --start 950900   # smoke
    python -m ciscarl2.gate41 --reps 20 --jobs 8
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import argparse

import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.model_selection import train_test_split

from . import dgp
from .estimators import aipw, crossfit_nuisances, phi_on_holdout
from .gate2 import pseudo_outcome
from .gate4d import TSTAR, _delta_for
from .gate20 import _capped_G
from .gate23 import E1, E2, _boot, _config23, _regions
from .gate26 import _calibrate_kind, _sim_kind
from .gate32 import _fit_leaves, _select
from .rules import eval_rule

from .paths import data_path

DATA = data_path()
START = 950100
KINDS = ("single", "two")
N = 8000
Z = float(norm.ppf(0.975))


def _ci(dphi, mask):
    m = dphi[mask]
    n = len(m)
    if n < 5:
        return np.nan, np.nan, np.nan
    eff = float(m.mean())
    se = float(np.sqrt(((m - eff) ** 2).sum()) / n)
    return eff, eff - Z * se, eff + Z * se


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
    truth = tau_i[asm]

    muD, GD, Gmarg, fid, fcaps, _ = crossfit_nuisances(
        XD, AD, TD, ED, TSTAR, seed=seed, return_folds=True)
    G = _capped_G(muD, GD, Gmarg, fid, fcaps, "conditional", TD)
    psi = pseudo_outcome(AD, TD, TSTAR, muD, G)
    _, _, q1, q0 = aipw(XD, AD, TD, TSTAR, muD, G)
    dphi_d = q1 - q0
    p1v, p0v = phi_on_holdout(XD, AD, TD, ED, XV, AV, TV, TSTAR, seed=seed)
    dphi_v = p1v - p0v

    leaves = _fit_leaves(psi, XD, 3, 60)
    j, means, sup, fallback = _select(psi, leaves)
    cond = leaves[j]["cond"]
    rule_a = eval_rule(cond, XA)
    if rule_a.sum() < 5:
        return []
    true_rule = float(truth[rule_a].mean())
    eff, lo, hi = _ci(dphi_v, eval_rule(cond, XV))
    rows = [dict(rep=rep, kind=kind, method="if", coverage=bool(lo <= true_rule <= hi),
                 width=hi - lo, eff=eff, truth=true_rule, n_leaves=len(leaves))]

    # Bonferroni over candidate leaves
    n_leaves = max(len(leaves), 1)
    z_adj = float(norm.ppf(1 - 0.05 / (2 * n_leaves)))
    lo_b = eff - z_adj * ((hi - lo) / (2 * Z))
    hi_b = eff + z_adj * ((hi - lo) / (2 * Z))
    rows.append(dict(rep=rep, kind=kind, method="bonferroni",
                     coverage=bool(lo_b <= true_rule <= hi_b),
                     width=hi_b - lo_b, eff=eff, truth=true_rule,
                     n_leaves=n_leaves))

    # Sample-splitting: select on half A, estimate on half B
    a, b = train_test_split(np.arange(len(XD)), test_size=0.5,
                            random_state=seed + 7, stratify=AD)
    leaves_s = _fit_leaves(psi[a], XD[a], 3, 60)
    floor = max(60, int(round(200 * len(a) / 4000)))
    js, _, _, _ = _select(psi[a], leaves_s, floor=floor)
    cond_s = leaves_s[js]["cond"]
    rule_s_a = eval_rule(cond_s, XA)
    if rule_s_a.sum() < 5:
        return rows
    mb = eval_rule(cond_s, XD[b])
    eff_s, lo_s, hi_s = _ci(dphi_d[b], mb)
    true_s = float(truth[rule_s_a].mean())
    rows.append(dict(rep=rep, kind=kind, method="split", coverage=bool(lo_s <= true_s <= hi_s),
                     width=hi_s - lo_s, eff=eff_s, truth=true_s,
                     n_leaves=len(leaves_s)))
    return rows


def summarise(raw):
    out = []
    for kind in sorted(raw.kind.unique()):
        g = raw[raw.kind == kind]
        for method in ("if", "bonferroni", "split"):
            d = g[g.method == method]
            if not len(d):
                continue
            out.append(dict(kind=kind, method=method, reps=len(d),
                            coverage=100 * d.coverage.mean(),
                            width=d.width.mean()))
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
    raw.to_csv(os.path.join(root, "results", "gate41_replications.csv"), index=False)
    res = summarise(raw)
    res.to_csv(os.path.join(root, "results", "gate41_summary.csv"), index=False)

    print(f"\n=== Gate 41, selection-aware intervals, {args.reps} reps ===")
    print(res.round(3).to_string(index=False))
    return raw, res


if __name__ == "__main__":
    main()
