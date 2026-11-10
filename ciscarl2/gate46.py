"""Gate 46 - ensemble methods versus CART for rule discovery.

Every ensemble is first turned into a readable rule: its out-of-fold effect
predictions on discovery are distilled into a depth-3 CART, then the same
support-floor and validation-commitment protocol is applied. This keeps the
comparison about the effect signal, not about model format.

Learners:
    cart        frozen depth-3 CART (reference)
    cart_tuned  best configuration from Gate 45
    rf          random forest
    extra       extremely randomised trees
    gbm         gradient boosting
    hist        histogram gradient boosting
    stack       ridge stack of rf + extra + gbm out-of-fold predictions

Run:
    python -m ciscarl2.gate46 --reps 20 --jobs 8
Writes:
    results/gate46_replications.csv
    results/gate46_summary.csv
"""
from __future__ import annotations

import argparse
import os
import time

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.ensemble import (ExtraTreesRegressor, GradientBoostingRegressor,
                              HistGradientBoostingRegressor,
                              RandomForestRegressor)
from sklearn.linear_model import RidgeCV
from sklearn.model_selection import KFold, cross_val_predict, train_test_split
from sklearn.tree import DecisionTreeRegressor

from . import dgp
from .estimators import aipw, crossfit_nuisances, phi_on_holdout
from .gate2 import pseudo_outcome
from .gate4d import TSTAR, _delta_for
from .gate11 import _cart
from .gate19 import _assign_effs, _leaf_table
from .gate20 import _capped_G
from .gate23 import E1, E2, _config23, _regions
from .gate26 import _calibrate_kind, _sim_kind
from .gate30 import _metrics
from .gate32 import _as_leaves, _evaluate, _holm, _select
from .rules import eval_rule, jaccard

from .paths import data_path

DATA = data_path()
START = 980100
KINDS = ("single", "two")
LEARNERS = ("cart", "cart_tuned", "rf", "extra", "gbm", "hist", "stack")
N = 8000
SUP = 200


def _tuned_config():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(root, "results", "gate45_tuning.csv")
    fallback = dict(max_depth=5, min_samples_leaf=30,
                    criterion="squared_error", ccp_alpha=0.0)
    if not os.path.exists(path):
        return fallback
    best = pd.read_csv(path).iloc[0]
    crit = str(best.criterion)
    if crit in ("friedman_mse", "squared_error"):
        crit = "squared_error"
    return dict(max_depth=int(best.depth), min_samples_leaf=int(best.leaf),
                criterion=crit, ccp_alpha=float(best.ccp_alpha))


TUNED = _tuned_config()


def _make_model(kind, seed):
    if kind == "rf":
        return RandomForestRegressor(
            n_estimators=300, min_samples_leaf=10, max_features=0.5,
            n_jobs=1, random_state=seed)
    if kind == "extra":
        return ExtraTreesRegressor(
            n_estimators=300, min_samples_leaf=10, max_features=0.5,
            n_jobs=1, random_state=seed)
    if kind == "gbm":
        return GradientBoostingRegressor(
            n_estimators=150, learning_rate=0.05, max_depth=2,
            random_state=seed)
    if kind == "hist":
        return HistGradientBoostingRegressor(
            max_iter=200, learning_rate=0.05, max_depth=3,
            random_state=seed)
    raise ValueError(kind)


def _oof(psi, X, seed, kind):
    """Out-of-fold effect predictions, so distillation does not see own rows."""
    kf = KFold(5, shuffle=True, random_state=seed)
    pred = np.zeros(len(psi))
    for tr, va in kf.split(X):
        model = _make_model(kind, seed)
        model.fit(X[tr], psi[tr])
        pred[va] = model.predict(X[va])
    return pred


def _oof_cart(psi, X, seed, params):
    kf = KFold(5, shuffle=True, random_state=seed)
    pred = np.zeros(len(psi))
    for tr, va in kf.split(X):
        tree = DecisionTreeRegressor(random_state=0, **params)
        tree.fit(X[tr], psi[tr])
        pred[va] = tree.predict(X[va])
    return pred


def _oof_pred(psi, X, seed, learner):
    if learner == "cart":
        return _oof_cart(psi, X, seed,
                         dict(max_depth=3, min_samples_leaf=60,
                              criterion="squared_error"))
    if learner == "cart_tuned":
        return _oof_cart(psi, X, seed, TUNED)
    if learner in ("rf", "extra", "gbm", "hist"):
        return _oof(psi, X, seed, learner)
    if learner == "stack":
        z = np.column_stack([_oof(psi, X, seed, k) for k in ("rf", "extra", "gbm")])
        meta = RidgeCV(alphas=(0.01, 0.1, 1.0, 10.0))
        return cross_val_predict(meta, z, psi,
                                 cv=KFold(5, shuffle=True, random_state=seed))
    raise ValueError(learner)


def _leaves_for(psi, X, seed, learner):
    if learner == "cart":
        return _fit_leaves(psi, X, 3, 60)
    if learner == "cart_tuned":
        tree = DecisionTreeRegressor(random_state=0, **TUNED).fit(X, psi)
        return _as_leaves(tree, X, 60)
    oof = _oof_pred(psi, X, seed, learner)
    tree = DecisionTreeRegressor(max_depth=3, min_samples_leaf=60,
                                 random_state=0).fit(X, oof)
    return _as_leaves(tree, X, 60)


def _fit_leaves(psi, X, depth, leaf):
    t = DecisionTreeRegressor(max_depth=depth, min_samples_leaf=leaf,
                              random_state=0).fit(X, psi)
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
    for learner in LEARNERS:
        t0 = time.time()
        leaves = _leaves_for(psi, XD, seed, learner)
        j, means, sup, fallback = _select(psi, leaves)
        down = _evaluate(leaves, j, psi, XV, XA, dphi_v, const, truth, uniA)
        oof = _oof_pred(psi, XD, seed, learner)
        mae_tau = float(np.abs(oof - tau_i[disc]).mean())
        rho = float(spearmanr(oof, tau_i[disc]).statistic)
        rows.append(dict(
            rep=rep, kind=kind, learner=learner, n=N,
            purity=down["purity_rule"], capture=down["capture_rule"],
            jaccard=down["jaccard"], mae_assessment=down["mae_assessment"],
            commit=down["committed"], support=down["support"],
            conditions=down["conditions"], fallback=fallback,
            mae_tau=mae_tau, spearman=rho,
            seconds=time.time() - t0,
        ))
    return rows


def summarise(raw):
    out = []
    for kind in sorted(raw.kind.unique()):
        g = raw[raw.kind == kind]
        base = g[g.learner == "cart"].set_index("rep")
        for learner in LEARNERS:
            d = g[g.learner == learner].set_index("rep")
            common = sorted(set(base.index) & set(d.index))
            row = dict(kind=kind, learner=learner, reps=len(d),
                       purity=d.purity.mean(), capture=d.capture.mean(),
                       jaccard=d.jaccard.mean(),
                       commit=100.0 * d.commit.mean(),
                       mae_assessment=d.mae_assessment.mean(),
                       mae_tau=d.mae_tau.mean(), spearman=d.spearman.mean(),
                       support=d.support.mean(), conditions=d.conditions.mean(),
                       seconds=d.seconds.mean())
            for metric in ("purity", "capture", "jaccard", "mae_assessment",
                           "mae_tau"):
                diff = (d.loc[common, metric] - base.loc[common, metric]).to_numpy()
                diff = diff[np.isfinite(diff)]
                if len(diff) < 3:
                    row[f"d_{metric}"] = np.nan
                    row[f"lo_{metric}"] = np.nan
                    row[f"hi_{metric}"] = np.nan
                    row[f"p_{metric}"] = np.nan
                    continue
                lo, hi, p = _boot(diff, seed=11)
                row[f"d_{metric}"] = float(diff.mean())
                row[f"lo_{metric}"] = lo
                row[f"hi_{metric}"] = hi
                row[f"p_{metric}"] = p
            out.append(row)
    return pd.DataFrame(out)


def _boot(diff, seed=11):
    rng = np.random.RandomState(seed)
    n = len(diff)
    means = np.array([diff[rng.randint(0, n, n)].mean() for _ in range(2000)])
    lo, hi = np.percentile(means, [2.5, 97.5])
    p = 2.0 * min((means <= 0).mean(), (means >= 0).mean())
    return float(lo), float(hi), float(min(1.0, p))


def main(argv=None):
    global START, LEARNERS
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=20)
    ap.add_argument("--start", type=int, default=None)
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--learners", default=",".join(LEARNERS))
    args = ap.parse_args(argv)

    if args.start is not None:
        START = args.start
    LEARNERS = tuple(s.strip() for s in args.learners.split(",") if s.strip())

    cfg = _config23()
    lam = {k: _calibrate_kind(cfg, k) for k in KINDS}

    from joblib import Parallel, delayed
    jobs = [(rep, kind) for kind in KINDS for rep in range(args.reps)]
    out = Parallel(n_jobs=args.jobs, verbose=5)(
        delayed(run_rep)(rep, kind, cfg, lam[kind]) for rep, kind in jobs)

    raw = pd.DataFrame([r for ch in out for r in ch])
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw.to_csv(os.path.join(root, "results", "gate46_replications.csv"),
               index=False)
    res = summarise(raw)
    res.to_csv(os.path.join(root, "results", "gate46_summary.csv"), index=False)

    print(f"\n=== Gate 46, ensemble vs CART, {args.reps} reps ===")
    cols = ["kind", "learner", "purity", "capture", "jaccard", "commit",
            "mae_assessment", "mae_tau", "spearman", "support", "conditions",
            "seconds"]
    print(res[cols].round(4).to_string(index=False))

    print("\nPaired vs frozen CART:")
    for _, r in res.iterrows():
        if r.learner == "cart":
            continue
        print(f"  {r.kind:>6} {r.learner:>10} "
              f"dCapture={r.d_capture:+.3f} [{r.lo_capture:+.3f},{r.hi_capture:+.3f}] "
              f"dPurity={r.d_purity:+.3f} "
              f"dMAE={r.d_mae_assessment:+.4f} "
              f"p={r.p_capture:.3f}")

    # Decision rule, fixed before the run.
    print("\nDecision checks:")
    for _, r in res.iterrows():
        if r.learner in ("cart", "cart_tuned"):
            continue
        pass_purity = r.d_purity >= -0.02
        gain = r.lo_capture > 0
        pass_mae = r.d_mae_assessment <= 0.002
        cost = r.seconds <= 5 * max(
            res[(res.kind == r.kind) & (res.learner == "cart")].seconds.iloc[0], 0.01)
        ok = pass_purity and gain and pass_mae and cost
        print(f"  {r.kind:>6} {r.learner:>10} purity={pass_purity} "
              f"capture_gain={gain} mae={pass_mae} cost={cost} -> "
              f"{'ADOPT' if ok else 'reject'}")
    return raw, res


if __name__ == "__main__":
    main()
