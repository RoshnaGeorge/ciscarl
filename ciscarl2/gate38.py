"""Gate 38 - feature-selection alternatives on ACTG175.

Pre-registration: `results/gate38_PREREGISTRATION.md`.

Compares the 12 published covariates with the 16-candidate set, lasso and RFE.
Feature selection is fitted on discovery only; the target and nuisances are
refitted on the selected columns.

Usage
-----
    python -m ciscarl2.gate38
"""
from __future__ import annotations

import os

import numpy as np
import pandas as pd
from scipy.stats import norm, t as tdist
from sklearn.feature_selection import RFECV
from sklearn.linear_model import LassoCV, LinearRegression
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
SEED = 2024
SUP = 200
EXTRA = ["oprior", "z30", "preanti", "strat"]
Z95 = float(norm.ppf(0.95))


def _ci(dphi, mask):
    m = dphi[mask]
    n = len(m)
    if n < 5:
        return np.nan, np.nan, np.nan, n
    eff = float(m.mean())
    se = float(np.sqrt(((m - eff) ** 2).sum()) / n)
    q = float(tdist.ppf(0.975, n - 1))
    return eff, eff - q * se, eff + q * se, n


def _fit_set(raw, cols, disc, val, asm):
    Xr = raw[cols].to_numpy(float)
    mu, sd = Xr[disc].mean(0), Xr[disc].std(0)
    sd[sd == 0] = 1.0
    X = (Xr - mu) / sd
    XD, XV, XA = X[disc], X[val], X[asm]
    A = (raw.arms == 1).to_numpy(int)
    T = raw.days.to_numpy(float)
    E = raw.cens.to_numpy(int)
    AD, TD, ED = A[disc], T[disc], E[disc]
    AV, TV, EV = A[val], T[val], E[val]
    AA, TA, EA = A[asm], T[asm], E[asm]

    muD, GD, Gmarg, fid, fcaps, _ = crossfit_nuisances(
        XD, AD, TD, ED, 730.0, seed=SEED, return_folds=True)
    G = _capped_G(muD, GD, Gmarg, fid, fcaps, "conditional", TD)
    psi = pseudo_outcome(AD, TD, 730.0, muD, G)
    const = float(aipw(XD, AD, TD, 730.0, muD, G)[0])
    leaves = _cart(psi, XD, 3)[1]
    means, ses, sup = _stats(psi, leaves)
    ok = sup >= SUP
    fallback = not bool(ok.any())
    j = (int(np.nanargmax(np.where(ok, means, -np.inf))) if ok.any()
         else int(np.nanargmax(means)))
    cond = leaves[j]["cond"]
    rule = " & ".join(f"{cols[f]} {op} {thr * sd[f] + mu[f]:.1f}"
                      for f, op, thr in cond)

    p1v, p0v = phi_on_holdout(XD, AD, TD, ED, XV, AV, TV, 730.0, seed=SEED)
    p1a, p0a = phi_on_holdout(XD, AD, TD, ED, XA, AA, TA, 730.0, seed=SEED)
    dphi_v, dphi_a = p1v - p0v, p1a - p0a
    eff_v, lo_v, hi_v, n_v = _ci(dphi_v, eval_rule(cond, XV))
    eff_a, lo_a, hi_a, n_a = _ci(dphi_a, eval_rule(cond, XA))
    se_v = (hi_v - lo_v) / (2 * float(tdist.ppf(0.975, max(n_v - 1, 1))))
    lcb = eff_v - Z95 * se_v if np.isfinite(se_v) else np.nan
    return dict(
        n_features=len(cols), features=", ".join(cols),
        support=int(sup[j]), fallback=fallback, rule=rule,
        n_conditions=len(cond), val_effect=eff_v, val_se=se_v,
        val_lcb=lcb, asm_effect=eff_a, asm_lo=lo_a, asm_hi=hi_a,
        asm_n=n_a, psi=psi, XD=XD, cols=cols,
    )


def main():
    raw = pd.read_csv(DATA)
    raw = raw[raw.arms.isin([0, 1])].reset_index(drop=True)
    A = (raw.arms == 1).to_numpy(int)
    T = raw.days.to_numpy(float)
    E = raw.cens.to_numpy(int)
    idx = np.arange(len(raw))
    strat = A * 2 + E
    disc, hold = train_test_split(idx, test_size=0.5, random_state=SEED,
                                  stratify=strat)
    val, asm = train_test_split(hold, test_size=0.5, random_state=SEED + 1,
                                stratify=strat[hold])

    base12 = _fit_set(raw, dgp.COVARIATES, disc, val, asm)
    base16 = _fit_set(raw, dgp.COVARIATES + EXTRA, disc, val, asm)

    # lasso / RFE on the 12-feature discovery matrix and the 12-feature psi
    X12 = raw[dgp.COVARIATES].to_numpy(float)
    mu, sd = X12[disc].mean(0), X12[disc].std(0)
    sd[sd == 0] = 1.0
    X12D = (X12[disc] - mu) / sd
    lasso = LassoCV(cv=5, random_state=SEED, max_iter=50000).fit(
        X12D, base12["psi"])
    lasso_cols = [c for c, b in zip(dgp.COVARIATES, lasso.coef_)
                  if abs(b) > 1e-8]
    if len(lasso_cols) < 2:
        lasso_cols = list(dgp.COVARIATES)

    rfe = RFECV(LinearRegression(), step=1, cv=5,
                scoring="neg_mean_absolute_error",
                min_features_to_select=2, n_jobs=1).fit(
                    X12D, base12["psi"])
    rfe_cols = [c for c, keep in zip(dgp.COVARIATES, rfe.support_) if keep]

    rows = []
    for name, cols in (("12", dgp.COVARIATES),
                       ("16", dgp.COVARIATES + EXTRA),
                       ("lasso", lasso_cols),
                       ("rfe", rfe_cols)):
        if name == "12":
            r = base12
        elif name == "16":
            r = base16
        else:
            r = _fit_set(raw, cols, disc, val, asm)
        r = dict(r)
        r.pop("psi", None)
        r.pop("XD", None)
        r.pop("cols", None)
        r["method"] = name
        rows.append(r)

    df = pd.DataFrame(rows)
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    df.to_csv(os.path.join(root, "results", "gate38_features.csv"), index=False)

    print("=== Gate 38, feature selection ===")
    print(df[["method", "n_features", "support", "fallback", "val_effect",
              "val_se", "val_lcb", "asm_effect", "n_conditions"]]
          .round(3).to_string(index=False))
    print("\nRules:")
    for _, r in df.iterrows():
        print(f"  {r.method:>5}  {r.rule}  | support {r.support}")
    print("\nLasso features:", lasso_cols)
    print("RFE features  :", rfe_cols)
    return df


if __name__ == "__main__":
    main()
