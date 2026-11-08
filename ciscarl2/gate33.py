"""Gate 33 - calibration and interval comparison.

Pre-registration: `results/gate33_PREREGISTRATION.md`.

Calibration: none / empirical-Bayes shrinkage / out-of-fold isotonic.
Intervals: influence function / validation bootstrap / selection bootstrap /
repeated split-half conformal-style.

Usage
-----
    python -m ciscarl2.gate33 --reps 1 --start 920900   # smoke
    python -m ciscarl2.gate33 --reps 20 --jobs 8
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
from sklearn.isotonic import IsotonicRegression
from sklearn.model_selection import KFold, train_test_split

from . import dgp
from .estimators import aipw, crossfit_nuisances, phi_on_holdout
from .gate2 import pseudo_outcome
from .gate4d import TSTAR, _delta_for
from .gate19 import _assign_effs
from .gate20 import _capped_G
from .gate23 import E1, E2, _boot, _config23, _regions
from .gate26 import _calibrate_kind, _sim_kind
from .gate30 import _metrics
from .gate32 import _fit_leaves, _select
from .rules import eval_rule

from .paths import data_path

DATA = data_path()
START = 920100
KINDS = ("single", "two")
CAL = ("none", "shrink", "isotonic")
INT = ("if", "boot", "select", "conformal")
N = 8000
SUP = 200
Z95 = float(norm.ppf(0.95))
B_BOOT = 500
B_SEL = 200
B_CONF = 200


def _shrink_factor(effs, ses, ceiling=0.8):
    ok = np.isfinite(effs) & np.isfinite(ses)
    if ok.sum() < 2:
        return 0.0
    within = float(np.mean(ses[ok] ** 2))
    between = float(np.var(effs[ok], ddof=1))
    if within + between <= 0:
        return 0.0
    return float(np.clip(within / (within + between), 0.0, ceiling))


def _isotonic_oof(score, y, seed, n_splits=5):
    oof = np.zeros(len(y))
    for fit, hold in KFold(n_splits, shuffle=True, random_state=seed).split(score):
        iso = IsotonicRegression(out_of_bounds="clip").fit(score[fit], y[fit])
        oof[hold] = iso.predict(score[hold])
    return oof


def _leaf_effects(leaves, means, XV, dphi_v, const, method, seed):
    masks = [eval_rule(r["cond"], XV) for r in leaves]
    effs = np.array([float(dphi_v[m].mean()) if m.sum() else np.nan
                     for m in masks])
    ses = np.array([float(np.sqrt(((dphi_v[m] - e) ** 2).sum()) / m.sum())
                    if m.sum() >= 2 else np.nan
                    for m, e in zip(masks, effs)])
    if method == "none":
        return effs, ses, masks
    if method == "shrink":
        lam = _shrink_factor(effs, ses)
        return (1.0 - lam) * effs + lam * const, ses, masks
    # out-of-fold isotonic calibration of the discovery leaf score
    score = np.full(len(XV), const)
    for t, m in enumerate(masks):
        score[m] = means[t]
    cal = _isotonic_oof(score, dphi_v, seed)
    eff = np.array([float(cal[m].mean()) if m.sum() else np.nan for m in masks])
    return eff, ses, masks


def _if_interval(dphi_v, mask):
    m = mask
    k = int(m.sum())
    if k < 5:
        return np.nan, np.nan, np.nan
    eff = float(dphi_v[m].mean())
    se = float(np.sqrt(((dphi_v[m] - eff) ** 2).sum()) / k)
    return eff, eff - Z95 * se, eff + Z95 * se


def _boot_interval(dphi_v, mask, seed):
    m = mask
    k = int(m.sum())
    if k < 5:
        return np.nan, np.nan
    rng = np.random.RandomState(seed)
    vals = np.array([dphi_v[m][rng.choice(k, k, replace=True)].mean()
                     for _ in range(B_BOOT)])
    lo, hi = np.percentile(vals, [2.5, 97.5])
    return float(lo), float(hi)


def _select_boot(psi, XD, XV, dphi_v, seed):
    rng = np.random.RandomState(seed)
    vals = []
    for _ in range(B_SEL):
        idx = rng.choice(len(XD), len(XD), replace=True)
        leaves = _fit_leaves(psi[idx], XD[idx], 3, 60)
        j, _, _, _ = _select(psi[idx], leaves)
        m = eval_rule(leaves[j]["cond"], XV)
        if m.sum() >= 5:
            vals.append(float(dphi_v[m].mean()))
    if len(vals) < 20:
        return np.nan, np.nan
    lo, hi = np.percentile(vals, [2.5, 97.5])
    return float(lo), float(hi)


def _conformal_interval(dphi_v, mask, seed):
    rng = np.random.RandomState(seed)
    vals = []
    for _ in range(B_CONF):
        idx = rng.permutation(len(dphi_v))
        h = len(idx) // 2
        a, b = idx[:h], idx[h:]
        ma, mb = a[mask[a]], b[mask[b]]
        if len(ma) >= 5 and len(mb) >= 5:
            vals.append(abs(float(dphi_v[ma].mean() - dphi_v[mb].mean())))
    if len(vals) < 20:
        return np.nan, np.nan
    q = float(np.quantile(vals, 0.95))
    eff = float(dphi_v[mask].mean())
    return eff - q, eff + q


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
    const = float(aipw(XD, AD, TD, TSTAR, muD, G)[0])
    p1v, p0v = phi_on_holdout(XD, AD, TD, ED, XV, AV, TV, TSTAR, seed=seed)
    p1a, p0a = phi_on_holdout(XD, AD, TD, ED, XA, AA, TA, TSTAR, seed=seed)
    dphi_v, dphi_a = p1v - p0v, p1a - p0a

    leaves = _fit_leaves(psi, XD, 3, 60)
    j, means, sup, fallback = _select(psi, leaves)
    rule_v = eval_rule(leaves[j]["cond"], XV)
    rule_a = eval_rule(leaves[j]["cond"], XA)
    k = int(rule_v.sum())
    eff_raw = float(dphi_v[rule_v].mean()) if k else np.nan
    se_raw = (float(np.sqrt(((dphi_v[rule_v] - eff_raw) ** 2).sum()) / k)
              if k else np.nan)
    committed = bool(np.isfinite(eff_raw) and np.isfinite(se_raw)
                     and eff_raw > Z95 * se_raw)
    truth_rule = float(truth[rule_a].mean()) if rule_a.sum() else np.nan

    cal_rows = []
    for method in CAL:
        effs, ses, masks = _leaf_effects(
            leaves, means, XV, dphi_v, const, method, seed)
        use = np.where(np.isfinite(effs), effs, const)
        if not committed:
            use[j] = const
        tbl_a = [dict(cond=leaves[t]["cond"],
                      mask=eval_rule(leaves[t]["cond"], XA),
                      eff=use[t], se=ses[t]) for t in range(len(leaves))]
        pred = _assign_effs(tbl_a, XA, use, const)
        treated = rule_a if committed else np.zeros(len(XA), bool)
        metrics = _metrics(pred, treated, truth, union[asm])
        cal_rows.append(dict(
            rep=rep, kind=kind, method=method,
            mae=metrics["mae"], purity=metrics["purity"],
            capture=metrics["capture"], commit=committed,
            support=int(sup[j]), fallback=fallback))

    int_rows = []
    if k >= 5 and rule_a.sum() >= 5:
        intervals = {
            "if": _if_interval(dphi_v, rule_v)[1:],
            "boot": _boot_interval(dphi_v, rule_v, seed + 1),
            "select": _select_boot(psi, XD, XV, dphi_v, seed + 2),
            "conformal": _conformal_interval(dphi_v, rule_v, seed + 3),
        }
        for method, (lo, hi) in intervals.items():
            if not (np.isfinite(lo) and np.isfinite(hi)):
                continue
            int_rows.append(dict(
                rep=rep, kind=kind, method=method,
                eff=eff_raw, lo=lo, hi=hi, width=hi - lo,
                covered=bool(lo <= truth_rule <= hi),
                truth_rule=truth_rule, commit=committed))
    return cal_rows, int_rows


def _summ_cal(raw):
    out = []
    for kind in sorted(raw.kind.unique()):
        g = raw[raw.kind == kind]
        base = g[g.method == "none"].set_index("rep")
        for method in CAL:
            d = g[g.method == method].set_index("rep")
            common = sorted(set(base.index) & set(d.index))
            diff = (d.loc[common, "mae"] - base.loc[common, "mae"]).to_numpy()
            lo, hi, p = _boot(diff, seed=5)
            out.append(dict(
                kind=kind, method=method, reps=len(d),
                mae=d.mae.mean(), purity=d.purity.mean(),
                capture=d.capture.mean(), commit=100 * d.commit.mean(),
                d_mae=float(diff.mean()), lo=lo, hi=hi, p=p))
    return pd.DataFrame(out)


def _summ_int(raw):
    out = []
    for kind in sorted(raw.kind.unique()):
        g = raw[raw.kind == kind]
        for method in INT:
            d = g[g.method == method]
            if not len(d):
                continue
            out.append(dict(
                kind=kind, method=method, reps=len(d),
                coverage=100 * d.covered.mean(), width=d.width.mean(),
                eff=d.eff.mean(), truth=d.truth_rule.mean()))
    return pd.DataFrame(out)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=20)
    ap.add_argument("--start", type=int, default=None)
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--tag", default="")
    args = ap.parse_args(argv)
    suffix = f"_{args.tag}" if args.tag else ""

    global START
    if args.start is not None:
        START = args.start
    cfg = _config23()
    lam = {k: _calibrate_kind(cfg, k) for k in KINDS}

    from joblib import Parallel, delayed
    jobs = [(rep, kind) for kind in KINDS for rep in range(args.reps)]
    out = Parallel(n_jobs=args.jobs, verbose=5)(
        delayed(run_rep)(rep, kind, cfg, lam[kind]) for rep, kind in jobs)

    cal = pd.DataFrame([r for c, _ in out for r in c])
    itv = pd.DataFrame([r for _, i in out for r in i])
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cal.to_csv(os.path.join(root, "results", f"gate33_calibration_raw{suffix}.csv"),
               index=False)
    itv.to_csv(os.path.join(root, "results", f"gate33_intervals_raw{suffix}.csv"),
               index=False)
    cs = _summ_cal(cal)
    isum = _summ_int(itv)
    cs.to_csv(os.path.join(root, "results", f"gate33_calibration{suffix}.csv"),
              index=False)
    isum.to_csv(os.path.join(root, "results", f"gate33_intervals{suffix}.csv"),
                index=False)

    print(f"\n=== Gate 33, calibration, {args.reps} reps ===")
    print(cs.round(4).to_string(index=False))
    print("\n=== Gate 33, intervals ===")
    print(isum.round(3).to_string(index=False))
    return cal, itv, cs, isum


if __name__ == "__main__":
    main()
