"""Gate 32 - rule-learner comparison.

Pre-registration: `results/gate32_PREREGISTRATION.md`.

Compares the frozen regression CART with cost-complexity pruning, PRIM,
a classification tree on sign(psi), and boosting distillation. Every learner
uses the same discovery psi, validation/assessment AIPW contrasts, support floor
200, and one-sided LCB commitment.

Usage
-----
    python -m ciscarl2.gate32 --reps 1 --start 910900   # smoke
    python -m ciscarl2.gate32 --reps 20 --jobs 8
"""
from __future__ import annotations

import argparse
import os
import time

import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.model_selection import KFold, train_test_split
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

from . import dgp
from .estimators import aipw, crossfit_nuisances, phi_on_holdout
from .gate2 import pseudo_outcome
from .gate4d import TSTAR, _delta_for
from .gate11 import _cart
from .gate19 import _assign_effs, _leaf_table
from .gate20 import _capped_G
from .gate22 import _stats
from .gate23 import E1, E2, _boot, _config23, _regions
from .gate26 import _calibrate_kind, _flex_oof, _sim_kind
from .gate30 import _metrics
from .rules import (eval_rule, extract_leaf_rules, jaccard, simplify)

from .paths import data_path

DATA = data_path()
START = 910100
KINDS = ("single", "two")
LEARNERS = ("cart", "pruned", "prim", "class", "boost")
N = 8000
SUP = 200
Z95 = float(norm.ppf(0.95))
N_EVAL = 20


def _prim_candidates(psi, X, min_support=SUP, peel_frac=0.05, max_conds=6):
    """Peeling-box PRIM; returns (mean psi, cond, mask) candidates."""
    n, p = X.shape
    mask = np.ones(n, bool)
    conds = []
    out = []

    def record():
        k = int(mask.sum())
        if k >= min_support:
            c = simplify(list(conds))
            m = eval_rule(c, X)
            if m.sum() >= min_support:
                out.append((float(psi[m].mean()), c, m))

    record()
    for _ in range(max_conds):
        cur = float(psi[mask].mean())
        k = max(1, int(np.floor(peel_frac * mask.sum())))
        best = None
        for j in range(p):
            xj = X[mask, j]
            order = np.argsort(xj)
            # peel the k lowest values: keep x > k-th smallest
            thr = float(xj[order[k - 1]])
            nm = mask & (X[:, j] > thr)
            if nm.sum() >= min_support:
                sc = float(psi[nm].mean())
                if best is None or sc > best[0]:
                    best = (sc, j, ">", thr, nm)
            # peel the k highest values: keep x < k-th largest
            thr2 = float(xj[order[-k]])
            nm2 = mask & (X[:, j] < thr2)
            if nm2.sum() >= min_support:
                sc2 = float(psi[nm2].mean())
                if best is None or sc2 > best[0]:
                    best = (sc2, j, "<=", thr2, nm2)
        if best is None or best[0] <= cur + 1e-10:
            break
        mask = best[4]
        conds.append((best[1], best[2], best[3]))
        record()
    return out


def _pruned_cart(psi, X, seed):
    """Cost-complexity pruning with the penalty chosen by 5-fold CV."""
    base = DecisionTreeRegressor(max_depth=5, min_samples_leaf=20,
                                 random_state=seed).fit(X, psi)
    path = base.cost_complexity_pruning_path(X, psi)
    alphas = [a for a in np.unique(path.ccp_alphas) if a > 0]
    if not alphas:
        return _fit_leaves(psi, X, 3, 60)
    kf = KFold(5, shuffle=True, random_state=seed)
    best = (np.inf, None)
    for alpha in alphas:
        errs = []
        for fit, hold in kf.split(X):
            t = DecisionTreeRegressor(
                max_depth=5, min_samples_leaf=20, random_state=seed,
                ccp_alpha=alpha).fit(X[fit], psi[fit])
            errs.append(float(np.abs(t.predict(X[hold]) - psi[hold]).mean()))
        m = float(np.mean(errs))
        if m < best[0]:
            best = (m, alpha)
    t = DecisionTreeRegressor(
        max_depth=5, min_samples_leaf=20, random_state=seed,
        ccp_alpha=best[1]).fit(X, psi)
    return _as_leaves(t, X, 20)


def _fit_leaves(psi, X, depth, leaf):
    t = DecisionTreeRegressor(max_depth=depth, min_samples_leaf=leaf,
                              random_state=0).fit(X, psi)
    return _as_leaves(t, X, leaf)


def _as_leaves(tree, X, min_support):
    out = [dict(cond=c, mask=m, score=float(m.sum()))
           for c, m in extract_leaf_rules(tree, X, min_support)]
    if not out:
        # a stump has no split, so extract_leaf_rules drops the empty path
        mask = np.ones(len(X), bool)
        out = [dict(cond=[], mask=mask, score=float(mask.sum()))]
    return out


def _select(psi, leaves, floor=SUP):
    if not leaves:
        return 0, np.array([np.nan]), np.array([0]), True
    means = np.array([float(psi[r["mask"]].mean()) for r in leaves])
    sup = np.array([int(r["mask"].sum()) for r in leaves])
    ok = sup >= floor
    fallback = not bool(ok.any())
    j = (int(np.nanargmax(np.where(ok, means, -np.inf))) if ok.any()
         else int(np.nanargmax(means)))
    return j, means, sup, fallback


def _evaluate(leaves, j, psi, XV, XA, dphi_v, const, truth, union_a):
    tbl_v = _leaf_table(leaves, XV, dphi_v)
    effs = np.array([t["eff"] for t in tbl_v], float)
    ses = np.array([t["se"] for t in tbl_v], float)
    effs_f = np.where(np.isfinite(effs), effs, const)

    mv = eval_rule(leaves[j]["cond"], XV)
    kv = int(mv.sum())
    hi_eff = float(dphi_v[mv].mean()) if kv else np.nan
    hi_se = (float(np.sqrt(((dphi_v[mv] - hi_eff) ** 2).sum()) / kv)
             if kv else np.nan)
    committed = bool(np.isfinite(hi_eff) and np.isfinite(hi_se)
                     and hi_eff > Z95 * hi_se)

    use = effs_f.copy()
    if not committed:
        use[j] = const
    masks_a = [eval_rule(r["cond"], XA) for r in leaves]
    tbl_a = [dict(cond=leaves[t]["cond"], mask=masks_a[t],
                  eff=use[t], se=ses[t]) for t in range(len(leaves))]
    pred = _assign_effs(tbl_a, XA, use, const)
    rule = masks_a[j]
    k = int(rule.sum())
    treated = rule if committed else np.zeros(len(XA), bool)
    row = _metrics(pred, treated, truth, union_a)
    row.update(
        jaccard=jaccard(rule, union_a),
        purity_rule=(float((rule & union_a).sum() / k) if k else np.nan),
        capture_rule=(float(truth[rule].sum() / truth.sum())
                      if (k and truth.sum() > 0) else np.nan),
        support=k, committed=committed,
        conditions=len(leaves[j]["cond"]),
        mae_assessment=row["mae"],
    )
    return row


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
        if learner == "cart":
            leaves = _fit_leaves(psi, XD, 3, 60)
        elif learner == "pruned":
            leaves = _pruned_cart(psi, XD, seed)
        elif learner == "prim":
            cands = _prim_candidates(psi, XD)
            leaves = ([dict(cond=c, mask=m, score=1.0) for _, c, m in cands]
                      if cands else _fit_leaves(psi, XD, 3, 60))
        elif learner == "class":
            t = DecisionTreeClassifier(
                max_depth=3, min_samples_leaf=60, random_state=seed
            ).fit(XD, (psi > 0).astype(int))
            leaves = _as_leaves(t, XD, 60)
        elif learner == "boost":
            tau_oof = _flex_oof(psi, XD, seed)
            t = DecisionTreeRegressor(
                max_depth=3, min_samples_leaf=60, random_state=0
            ).fit(XD, tau_oof)
            leaves = _as_leaves(t, XD, 60)
        else:  # pragma: no cover
            raise ValueError(learner)
        j, means, sup, fallback = _select(psi, leaves)
        down = _evaluate(leaves, j, psi, XV, XA, dphi_v, const, truth, uniA)
        elapsed = time.time() - t0
        rows.append(dict(
            rep=rep, kind=kind, learner=learner, n=N,
            purity=down["purity_rule"], capture=down["capture_rule"],
            jaccard=down["jaccard"], mae_assessment=down["mae_assessment"],
            commit=down["committed"], support=down["support"],
            conditions=down["conditions"], fallback=fallback,
            seconds=elapsed,
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
                       support=d.support.mean(), conditions=d.conditions.mean(),
                       seconds=d.seconds.mean())
            for metric in ("purity", "capture", "jaccard", "mae_assessment"):
                diff = (d.loc[common, metric] - base.loc[common, metric]).to_numpy()
                lo, hi, p = _boot(diff, seed=11)
                row[f"d_{metric}"] = float(diff.mean())
                row[f"lo_{metric}"] = lo
                row[f"hi_{metric}"] = hi
                row[f"p_{metric}"] = p
            out.append(row)
    return pd.DataFrame(out)


def _holm(df, col="p_capture"):
    df = df.copy()
    df["p_holm"] = np.nan
    for kind, g in df.groupby("kind"):
        alt = g[g.learner != "cart"].sort_values(col)
        m = len(alt)
        running = 0.0
        for i, idx in enumerate(alt.index):
            val = min(1.0, (m - i) * df.loc[idx, col])
            running = max(running, val)
            df.loc[idx, "p_holm"] = running
    return df


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
    raw.to_csv(os.path.join(root, "results", "gate32_replications.csv"),
               index=False)
    res = _holm(summarise(raw))
    res.to_csv(os.path.join(root, "results", "gate32_summary.csv"), index=False)

    print(f"\n=== Gate 32, rule learners, {args.reps} reps ===")
    cols = ["kind", "learner", "purity", "capture", "jaccard", "commit",
            "mae_assessment", "support", "conditions", "seconds"]
    print(res[cols].round(4).to_string(index=False))
    print("\nPaired vs CART:")
    for _, r in res.iterrows():
        if r.learner == "cart":
            continue
        print(f"  {r.kind:>6} {r.learner:>7} "
              f"dCapture={r.d_capture:+.3f} [{r.lo_capture:+.3f},{r.hi_capture:+.3f}] "
              f"p={r.p_capture:.3f} Holm={r.p_holm:.3f} "
              f"dPurity={r.d_purity:+.3f} dMAE={r.d_mae_assessment:+.4f}")
    return raw, res


if __name__ == "__main__":
    main()
