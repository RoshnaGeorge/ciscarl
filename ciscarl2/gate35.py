"""Gate 35 - fairness, SHAP and internal transport on ACTG175.

Pre-registration: `results/gate35_PREREGISTRATION.md`.

Descriptive only: ACTG175 has no individual treatment-effect truth. Group
effects are reported with intervals and an explicit power flag; SHAP is a
surrogate explanation; transport is an internal white/non-white check.

Usage
-----
    python -m ciscarl2.gate35
"""
from __future__ import annotations

import os

import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

from . import dgp
from .estimators import (aipw, crossfit_nuisances, ipcw_outcome, km_survival,
                         phi_on_holdout, truncate_weights)
from .gate2 import pseudo_outcome
from .gate11 import _cart
from .gate13 import _holdout
from .gate22 import _stats
from .rules import eval_rule, rule_str

from .paths import data_path

DATA = data_path()
TSTAR = 730.0
SEED = 2024
SUP = 200
Z95 = float(norm.ppf(0.95))


def _load():
    raw = pd.read_csv(DATA)
    raw = raw[raw.arms.isin([0, 1])].reset_index(drop=True)
    Xr = raw[dgp.COVARIATES].to_numpy(float)
    A = (raw.arms == 1).to_numpy(int)
    T = raw.days.to_numpy(float)
    E = raw.cens.to_numpy(int)
    return raw, Xr, A, T, E


def _rule_raw(cond, mu, sd, names):
    return " & ".join(f"{names[f]} {op} {thr * sd[f] + mu[f]:.1f}"
                      for f, op, thr in cond)


def _ci(dphi, mask):
    m = dphi[mask]
    n = len(m)
    if n < 5:
        return np.nan, np.nan, np.nan, n
    eff = float(m.mean())
    se = float(np.sqrt(((m - eff) ** 2).sum()) / n)
    return eff, eff - Z95 * se, eff + Z95 * se, n


def _fit_c200(XD, AD, TD, ED, XV, AV, TV, EV, XA, AA, TA, EA, seed,
              keep=None):
    if keep is None:
        keep = np.arange(XD.shape[1])
    keep = np.asarray(keep, int)
    XD, XV, XA = XD[:, keep], XV[:, keep], XA[:, keep]
    muD, GD, _, fid, fcaps, _ = crossfit_nuisances(
        XD, AD, TD, ED, TSTAR, seed=seed, return_folds=True)
    GD, _ = truncate_weights(GD, fid, fcaps)
    psi = pseudo_outcome(AD, TD, TSTAR, muD, GD)
    const = float(aipw(XD, AD, TD, TSTAR, muD, GD)[0])
    leaves = _cart(psi, XD, 3)[1]
    means, ses, sup = _stats(psi, leaves)
    ok = sup >= SUP
    fallback = not bool(ok.any())
    j = (int(np.nanargmax(np.where(ok, means, -np.inf))) if ok.any()
         else int(np.nanargmax(means)))
    cond_red = leaves[j]["cond"]
    cond = [(int(keep[f]), op, thr) for f, op, thr in cond_red]

    p1v, p0v = phi_on_holdout(XD, AD, TD, ED, XV, AV, TV, TSTAR, seed=seed)
    p1a, p0a = phi_on_holdout(XD, AD, TD, ED, XA, AA, TA, TSTAR, seed=seed)
    dphi_v, dphi_a = p1v - p0v, p1a - p0a
    eff_v, lo_v, hi_v, n_v = _ci(dphi_v, eval_rule(cond_red, XV))
    se_v = (hi_v - lo_v) / (2 * Z95) if np.isfinite(hi_v) else np.nan
    committed = bool(np.isfinite(eff_v) and np.isfinite(se_v)
                     and eff_v > Z95 * se_v)
    eff_a, lo_a, hi_a, n_a = _ci(dphi_a, eval_rule(cond_red, XA))
    return dict(cond=cond, cond_red=cond_red, keep=keep,
                leaves=leaves, j=j, sup=int(sup[j]),
                fallback=fallback, psi=psi, muD=muD, const=const,
                dphi_v=dphi_v, dphi_a=dphi_a, eff_v=eff_v, lo_v=lo_v,
                hi_v=hi_v, n_v=n_v, se_v=se_v, committed=committed,
                eff_a=eff_a, lo_a=lo_a, hi_a=hi_a, n_a=n_a)


def _group_row(raw, XA, dphi_a, rule_a, group, value, label):
    gm = (raw[group].to_numpy() == value)
    m = gm
    rm = rule_a & m
    eff, lo, hi, n = _ci(dphi_a, rm)
    prevalence = float(rm.sum() / max(m.sum(), 1))
    positive_lcb = bool(np.isfinite(eff) and np.isfinite(lo) and lo > 0)
    return dict(group=group, value=value, label=label, n=int(m.sum()),
                rule_n=n, prevalence=prevalence, effect=eff, lo=lo, hi=hi,
                se=(hi - lo) / (2 * Z95) if np.isfinite(hi) else np.nan,
                positive_lcb=positive_lcb, powered=bool(n >= 30))


def _calibration_row(raw, XA, mu_h, group, value, label):
    gm = (raw[group].to_numpy() == value)
    rows = []
    for arm in (0, 1):
        gm_arm = gm & (raw.arms.to_numpy() == arm)
        pred = float(mu_h[gm_arm, arm].mean()) if gm_arm.sum() else np.nan
        obs = (km_survival(raw.days.to_numpy()[gm_arm],
                           raw.cens.to_numpy()[gm_arm], TSTAR)
               if gm_arm.sum() > 5 else np.nan)
        rows.append((pred, obs, int(gm_arm.sum())))
    gaps = [abs(p - o) for p, o, n in rows if np.isfinite(p) and np.isfinite(o)]
    return dict(group=group, value=value, label=label,
                n=int(gm.sum()),
                pred_s0=rows[0][0], obs_s0=rows[0][1], n0=rows[0][2],
                pred_s1=rows[1][0], obs_s1=rows[1][1], n1=rows[1][2],
                ece=float(np.mean(gaps)) if gaps else np.nan)


def main():
    raw, Xr, A, T, E = _load()
    idx = np.arange(len(Xr))
    strat = A * 2 + E
    disc, hold = train_test_split(idx, test_size=0.5, random_state=SEED,
                                  stratify=strat)
    val, asm = train_test_split(hold, test_size=0.5, random_state=SEED + 1,
                                stratify=strat[hold])
    mu_d, sd_d = Xr[disc].mean(0), Xr[disc].std(0)
    sd_d[sd_d == 0] = 1.0
    X = (Xr - mu_d) / sd_d
    XD, AD, TD, ED = X[disc], A[disc], T[disc], E[disc]
    XV, AV, TV, EV = X[val], A[val], T[val], E[val]
    XA, AA, TA, EA = X[asm], A[asm], T[asm], E[asm]

    fit = _fit_c200(XD, AD, TD, ED, XV, AV, TV, EV, XA, AA, TA, EA, SEED)
    cond = fit["cond"]
    rule_a = eval_rule(cond, XA)
    rule_txt = _rule_raw(cond, mu_d, sd_d, dgp.COVARIATES)

    # ---- group rule effects ----
    rows = []
    for group, values in (("race", ((0, "white"), (1, "non-white"))),
                          ("gender", ((1, "male"), (0, "female")))):
        for value, label in values:
            rows.append(_group_row(raw.iloc[asm], XA, fit["dphi_a"],
                                   rule_a, group, value, label))
    groups = pd.DataFrame(rows)

    # ---- group calibration ----
    mu_h, G_h, cap = _holdout(XD, AD, TD, ED, XA, SEED)
    cal = []
    for group, values in (("race", ((0, "white"), (1, "non-white"))),
                          ("gender", ((1, "male"), (0, "female")))):
        for value, label in values:
            cal.append(_calibration_row(raw.iloc[asm], XA, mu_h,
                                        group, value, label))
    cal = pd.DataFrame(cal)

    # ---- SHAP on a surrogate for psi ----
    rf = RandomForestRegressor(
        n_estimators=200, max_depth=3, min_samples_leaf=60,
        random_state=0, n_jobs=-1).fit(XD, fit["psi"])
    import shap
    expl = shap.TreeExplainer(rf)
    sv = np.asarray(expl.shap_values(XA))
    if sv.ndim == 3:
        sv = sv[0]
    imp = np.abs(sv).mean(axis=0)
    shap_df = (pd.DataFrame({"feature": dgp.COVARIATES, "mean_abs_shap": imp})
               .sort_values("mean_abs_shap", ascending=False)
               .reset_index(drop=True))
    shap_df["rank"] = np.arange(1, len(shap_df) + 1)

    # ---- internal transport: white -> non-white ----
    white = raw.race.to_numpy() == 0
    wi = np.where(white)[0]
    wd, wh = train_test_split(wi, test_size=0.5, random_state=SEED,
                              stratify=A[wi])
    wv, wa = train_test_split(wh, test_size=0.5, random_state=SEED + 1,
                              stratify=A[wh])
    nw = np.where(~white)[0]
    mu_w, sd_w = Xr[wd].mean(0), Xr[wd].std(0)
    sd_w[sd_w == 0] = 1.0
    Xw = (Xr - mu_w) / sd_w
    keep = np.where(np.std(Xw[wd], axis=0) > 1e-8)[0]
    tfit = _fit_c200(Xw[wd], A[wd], T[wd], E[wd], Xw[wv], A[wv], T[wv], E[wv],
                     Xw[nw], A[nw], T[nw], E[nw], SEED, keep=keep)
    p1w, p0w = phi_on_holdout(Xw[wd], A[wd], T[wd], E[wd],
                              Xw[wa], A[wa], T[wa], TSTAR, seed=SEED)
    eff_w, lo_w, hi_w, n_w = _ci(p1w - p0w, eval_rule(tfit["cond"], Xw[wa]))
    rule_txt_w = _rule_raw(tfit["cond"], mu_w, sd_w, dgp.COVARIATES)
    tr = pd.DataFrame([
        dict(training="white", evaluation="white assessment",
             n=n_w, support=tfit["sup"], fallback=tfit["fallback"],
             rule=rule_txt_w, effect=eff_w, lo=lo_w, hi=hi_w),
        dict(training="white", evaluation="non-white rule",
             n=tfit["n_a"], support=tfit["sup"], fallback=tfit["fallback"],
             rule=rule_txt_w, effect=tfit["eff_a"],
             lo=tfit["lo_a"], hi=tfit["hi_a"]),
    ])

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    groups.to_csv(os.path.join(root, "results", "gate35_groups.csv"), index=False)
    cal.to_csv(os.path.join(root, "results", "gate35_calibration.csv"), index=False)
    shap_df.to_csv(os.path.join(root, "results", "gate35_shap.csv"), index=False)
    tr.to_csv(os.path.join(root, "results", "gate35_transport.csv"), index=False)

    print("\n=== Gate 35, ACTG175 fairness / SHAP / transport ===")
    print("main rule:", rule_txt)
    print(f"discovery support {fit['sup']}  fallback {fit['fallback']}  "
          f"validation {fit['eff_v']:+.3f} [{fit['lo_v']:+.3f},{fit['hi_v']:+.3f}]  "
          f"commit {fit['committed']}")
    print(f"assessment {fit['eff_a']:+.3f} [{fit['lo_a']:+.3f},{fit['hi_a']:+.3f}]  "
          f"n={fit['n_a']}")
    print("\nGroup rule effects:")
    print(groups.round(3).to_string(index=False))
    print("\nGroup calibration:")
    print(cal.round(3).to_string(index=False))
    print("\nSHAP top 5:")
    print(shap_df.head(5).round(3).to_string(index=False))
    print("\nTransport:")
    print(tr.round(3).to_string(index=False))
    return fit, groups, cal, shap_df, tr


if __name__ == "__main__":
    main()
