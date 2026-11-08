"""Gate 39 - learned stacking vs equal-weight stacking vs Cox.

Pre-registration: `results/gate39_PREREGISTRATION.md`.

Base models: Cox, RSF, GBM. The learned stack fits positive weights on discovery
out-of-fold predictions and the IPCW outcome; the equal-weight stack uses 1/3
each. All three use the same folds, partitions and C200 downstream.

Usage
-----
    python -m ciscarl2.gate39 --reps 2 --start 970900   # smoke
    python -m ciscarl2.gate39 --reps 10 --jobs 6
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import argparse

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split

from . import dgp
from .estimators import aipw, crossfit_nuisances
from .gate4d import TSTAR, _delta_for
from .gate20 import _capped_G
from .gate23 import E1, E2, _boot, _config23, _regions
from .gate26 import _calibrate_kind, _sim_kind
from .gate31 import (_censoring_G, _crossfit_mu, _downstream, _fit_surv)

from .paths import data_path

DATA = data_path()
START = 970100
KINDS = ("single", "two")
N = 8000


def _meta_weights(mu_list, A, Yipcw, arm):
    X = np.column_stack([m[:, arm] for m in mu_list])
    y = Yipcw
    m = A == arm
    reg = LinearRegression(positive=True, fit_intercept=False).fit(X[m], y[m])
    w = np.clip(reg.coef_, 0, None)
    if w.sum() <= 0:
        w = np.ones_like(w) / len(w)
    return w / w.sum()


def _combine(mu_list, w):
    return sum(w[k] * mu_list[k] for k in range(len(mu_list)))


def _holdout_mu(XD, AD, TD, ED, XH, model, seed):
    mu = np.zeros((len(XH), 2))
    for arm in (0, 1):
        m = AD == arm
        mu[:, arm] = _fit_surv(XD[m], TD[m], ED[m], XH, TSTAR, model, seed)
    return mu


def _phi(mu, AH, TH, G):
    Y = (TH > TSTAR).astype(float) / G
    m1, m0 = mu[:, 1], mu[:, 0]
    p1 = m1 + (AH == 1) / 0.5 * (Y - m1)
    p0 = m0 + (AH == 0) / 0.5 * (Y - m0)
    return p1, p0


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

    mu_cox, GD, Gmarg, fid, fcaps, _ = crossfit_nuisances(
        XD, AD, TD, ED, TSTAR, seed=seed, return_folds=True)
    G = _capped_G(mu_cox, GD, Gmarg, fid, fcaps, "conditional", TD)
    mu_rsf = _crossfit_mu(XD, AD, TD, ED, TSTAR, "rsf", fid, seed)
    mu_gbm = _crossfit_mu(XD, AD, TD, ED, TSTAR, "gbm", fid, seed)
    mus = [mu_cox, mu_rsf, mu_gbm]
    Yipcw = (TD > TSTAR).astype(float) / G

    w_learn = np.array([_meta_weights(mus, AD, Yipcw, a) for a in (1, 0)])
    mu_learn = np.column_stack([
        sum(w_learn[a, k] * mus[k][:, a] for k in range(3)) for a in (0, 1)])
    mu_equal = np.mean(mus, axis=0)

    # held-out predictions
    mu_h = {
        "cox": _holdout_mu(XD, AD, TD, ED, XV, "cox", seed),
        "rsf": _holdout_mu(XD, AD, TD, ED, XV, "rsf", seed),
        "gbm": _holdout_mu(XD, AD, TD, ED, XV, "gbm", seed),
    }
    mu_a = {
        "cox": _holdout_mu(XD, AD, TD, ED, XA, "cox", seed),
        "rsf": _holdout_mu(XD, AD, TD, ED, XA, "rsf", seed),
        "gbm": _holdout_mu(XD, AD, TD, ED, XA, "gbm", seed),
    }
    Gv = _censoring_G(XD, TD, ED, XV, TSTAR)
    Ga = _censoring_G(XD, TD, ED, XA, TSTAR)
    mu_h["learn"] = np.column_stack([
        sum(w_learn[a, k] * mu_h[["cox", "rsf", "gbm"][k]][:, a] for k in range(3))
        for a in (0, 1)])
    mu_h["equal"] = np.mean([mu_h[k] for k in ("cox", "rsf", "gbm")], axis=0)
    mu_a["learn"] = np.column_stack([
        sum(w_learn[a, k] * mu_a[["cox", "rsf", "gbm"][k]][:, a] for k in range(3))
        for a in (0, 1)])
    mu_a["equal"] = np.mean([mu_a[k] for k in ("cox", "rsf", "gbm")], axis=0)

    rows = []
    for est, mu_d, mu_v, mu_aa in (
            ("cox", mu_cox, mu_h["cox"], mu_a["cox"]),
            ("equal", mu_equal, mu_h["equal"], mu_a["equal"]),
            ("learn", mu_learn, mu_h["learn"], mu_a["learn"])):
        psi = (mu_d[:, 1] - mu_d[:, 0]
               + (AD == 1) / 0.5 * (Yipcw - mu_d[:, 1])
               - (AD == 0) / 0.5 * (Yipcw - mu_d[:, 0]))
        const = float(psi.mean())
        p1v, p0v = _phi(mu_v, AV, TV, Gv)
        p1a, p0a = _phi(mu_aa, AA, TA, Ga)
        down = _downstream(psi, XD, XV, XA, p1v - p0v, p1a - p0a, const,
                           truth, uniA)
        rows.append(dict(
            rep=rep, kind=kind, estimator=est,
            mae_nuis=float(np.abs((mu_d[:, 1] - mu_d[:, 0]) -
                                  tau_i[disc]).mean()),
            purity=down["purity_rule"], capture=down["capture_rule"],
            jaccard=down["jaccard"], commit=down["committed"],
            mae_assessment=down["mae_assessment"],
            w_cox=float(w_learn[0, 0]), w_rsf=float(w_learn[0, 1]),
            w_gbm=float(w_learn[0, 2]),
        ))
    return rows


def summarise(raw):
    out = []
    for kind in sorted(raw.kind.unique()):
        g = raw[raw.kind == kind]
        base = g[g.estimator == "cox"].set_index("rep")
        for est in ("cox", "equal", "learn"):
            d = g[g.estimator == est].set_index("rep")
            common = sorted(set(base.index) & set(d.index))
            row = dict(kind=kind, estimator=est, reps=len(d),
                       mae_nuis=d.mae_nuis.mean(),
                       purity=d.purity.mean(), capture=d.capture.mean(),
                       jaccard=d.jaccard.mean(),
                       commit=100 * d.commit.mean(),
                       mae_assessment=d.mae_assessment.mean(),
                       w_cox=d.w_cox.mean(), w_rsf=d.w_rsf.mean(),
                       w_gbm=d.w_gbm.mean())
            for metric in ("mae_nuis", "purity", "capture"):
                diff = (d.loc[common, metric] - base.loc[common, metric]).to_numpy()
                lo, hi, p = _boot(diff, seed=17)
                row[f"d_{metric}"] = float(diff.mean())
                row[f"lo_{metric}"] = lo
                row[f"hi_{metric}"] = hi
                row[f"p_{metric}"] = p
            out.append(row)
    return pd.DataFrame(out)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=10)
    ap.add_argument("--start", type=int, default=None)
    ap.add_argument("--jobs", type=int, default=6)
    args = ap.parse_args(argv)

    global START
    if args.start is not None:
        START = args.start
    import ciscarl2.gate31 as g31
    g31.RSF_TREES, g31.GBM_TREES = 50, 30
    cfg = _config23()
    lam = {k: _calibrate_kind(cfg, k) for k in KINDS}

    from joblib import Parallel, delayed
    jobs = [(rep, kind) for kind in KINDS for rep in range(args.reps)]
    out = Parallel(n_jobs=args.jobs, verbose=5)(
        delayed(run_rep)(rep, kind, cfg, lam[kind]) for rep, kind in jobs)

    raw = pd.DataFrame([r for ch in out for r in ch])
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw.to_csv(os.path.join(root, "results", "gate39_replications.csv"), index=False)
    res = summarise(raw)
    res.to_csv(os.path.join(root, "results", "gate39_summary.csv"), index=False)

    print(f"\n=== Gate 39, learned stacking, {args.reps} reps ===")
    print(res[["kind", "estimator", "mae_nuis", "purity", "capture",
               "commit", "mae_assessment", "w_cox", "w_rsf", "w_gbm"]]
          .round(4).to_string(index=False))
    print("\nPaired vs Cox:")
    for _, r in res[res.estimator != "cox"].iterrows():
        print(f"  {r.kind:>6} {r.estimator:>5} dMAE={r.d_mae_nuis:+.4f} "
              f"[{r.lo_mae_nuis:+.4f},{r.hi_mae_nuis:+.4f}] p={r.p_mae_nuis:.3f} "
              f"dPurity={r.d_purity:+.3f} dCapture={r.d_capture:+.3f}")
    return raw, res


if __name__ == "__main__":
    main()
