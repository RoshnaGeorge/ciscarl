"""Gate 43 - discovery-only horizon selection.

Pre-registration: `results/gate43_PREREGISTRATION.md`.

For each horizon, 5-fold inner CV inside discovery: fit Cox nuisances on 4/5,
fit CART and select a rule on 4/5, estimate its LCB on the held-out 1/5. Choose
the horizon with the highest mean LCB under event/at-risk/support constraints.
Validation and assessment are not used to choose the horizon.

Usage
-----
    python -m ciscarl2.gate43
"""
from __future__ import annotations

import os

import numpy as np
import pandas as pd
from scipy.stats import norm, t as tdist
from sklearn.model_selection import StratifiedKFold, train_test_split

from . import dgp
from .estimators import _cox_fit, aipw, crossfit_nuisances, phi_on_holdout
from .gate2 import pseudo_outcome
from .gate11 import _cart
from .gate20 import _capped_G
from .gate22 import _stats
from .rules import eval_rule

from .paths import data_path

DATA = data_path()
SEED = 2024
SUP = 200
GRID = tuple(range(365, 1096, 30))
Z95 = float(norm.ppf(0.95))
Z90 = float(norm.ppf(0.90))


def _ci(dphi, mask, z=Z95):
    m = dphi[mask]
    n = len(m)
    if n < 5:
        return np.nan, np.nan, np.nan, n
    eff = float(m.mean())
    se = float(np.sqrt(((m - eff) ** 2).sum()) / n)
    return eff, eff - z * se, eff + z * se, n


def _phi_fit(Xfit, Afit, Tfit, Efit, Xeval, h):
    mu = np.zeros((len(Xeval), 2))
    for arm in (0, 1):
        m = Afit == arm
        s0, beta, _ = _cox_fit(Xfit[m], Tfit[m], Efit[m], float(h))
        mu[:, arm] = s0 ** np.exp(Xeval @ beta)
    s0c, betac, _ = _cox_fit(Xfit, Tfit, (Efit == 0).astype(int), float(h))
    G = np.clip(s0c ** np.exp(Xeval @ betac), 1e-3, 1.0)
    return mu, G


def _inner_lcb(XD, AD, TD, ED, h):
    skf = StratifiedKFold(5, shuffle=True, random_state=SEED)
    vals, sups = [], []
    for fit, hold in skf.split(XD, AD):
        mu_f, G_f = _phi_fit(XD[fit], AD[fit], TD[fit], ED[fit], XD[fit], h)
        Yf = (TD[fit] > h).astype(float)
        Yf_ipcw = Yf / G_f
        psi = (mu_f[:, 1] - mu_f[:, 0]
               + (AD[fit] == 1) / 0.5 * (Yf_ipcw - mu_f[:, 1])
               - (AD[fit] == 0) / 0.5 * (Yf_ipcw - mu_f[:, 0]))
        leaves = _cart(psi, XD[fit], 3)[1]
        means, ses, sup = _stats(psi, leaves)
        ok = sup >= SUP
        j = (int(np.nanargmax(np.where(ok, means, -np.inf))) if ok.any()
             else int(np.nanargmax(means)))
        mu_h, G_h = _phi_fit(XD[fit], AD[fit], TD[fit], ED[fit], XD[hold], h)
        Yh = (TD[hold] > h).astype(float) / G_h
        p1 = mu_h[:, 1] + (AD[hold] == 1) / 0.5 * (Yh - mu_h[:, 1])
        p0 = mu_h[:, 0] + (AD[hold] == 0) / 0.5 * (Yh - mu_h[:, 0])
        dphi = p1 - p0
        eff, lo, hi, n = _ci(dphi, eval_rule(leaves[j]["cond"], XD[hold]), Z90)
        if np.isfinite(lo):
            vals.append(lo)
            sups.append(int(sup[j]))
    return (float(np.mean(vals)) if vals else np.nan,
            float(np.std(vals, ddof=1)) if len(vals) > 1 else np.nan,
            int(np.median(sups)) if sups else 0)


def main():
    raw = pd.read_csv(DATA)
    raw = raw[raw.arms.isin([0, 1])].reset_index(drop=True)
    Xr = raw[dgp.COVARIATES].to_numpy(float)
    A = (raw.arms == 1).to_numpy(int)
    T = raw.days.to_numpy(float)
    E = raw.cens.to_numpy(int)
    idx = np.arange(len(Xr))
    strat = A * 2 + E
    disc, hold = train_test_split(idx, test_size=0.5, random_state=SEED,
                                  stratify=strat)
    val, asm = train_test_split(hold, test_size=0.5, random_state=SEED + 1,
                                stratify=strat[hold])
    mu, sd = Xr[disc].mean(0), Xr[disc].std(0)
    sd[sd == 0] = 1.0
    X = (Xr - mu) / sd
    XD, AD, TD, ED = X[disc], A[disc], T[disc], E[disc]
    XV, AV, TV, EV = X[val], A[val], T[val], E[val]
    XA, AA, TA, EA = X[asm], A[asm], T[asm], E[asm]

    rows = []
    for h in GRID:
        lcb, sd_lcb, sup = _inner_lcb(XD, AD, TD, ED, h)
        rows.append(dict(
            horizon=h,
            events=int(((TD <= h) & (ED == 1)).sum()),
            at_risk=float((TD > h).mean()),
            inner_lcb=lcb, inner_sd=sd_lcb, inner_support=sup,
        ))

    df = pd.DataFrame(rows)
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    df.to_csv(os.path.join(root, "results", "gate43_horizon_inner.csv"), index=False)

    feasible = df[(df.events >= 100) & (df.at_risk >= 0.30) &
                  (df.inner_support >= 60)]
    print("=== Gate 43, discovery-only horizon selection ===")
    print(df[["horizon", "events", "at_risk", "inner_lcb", "inner_sd",
              "inner_support"]].round(3).to_string(index=False))
    print(f"\nfeasible: {len(feasible)}")
    if len(feasible):
        best = feasible.sort_values("inner_lcb", ascending=False).iloc[0]
        base = df.iloc[(df.horizon - 730).abs().argsort()[:1]].iloc[0]
        print(f"OPTIMUM: {int(best.horizon)} days | inner LCB {best.inner_lcb:+.3f} "
              f"| 730 inner LCB {base.inner_lcb:+.3f} "
              f"| gain {best.inner_lcb - base.inner_lcb:+.3f}")
        print(f"events {int(best.events)} | at risk {best.at_risk:.3f} | "
              f"support {int(best.inner_support)}")

        # evaluate the chosen horizon once on validation/assessment
        h = int(best.horizon)
        muD, GD, Gmarg, fid, fcaps, _ = crossfit_nuisances(
            XD, AD, TD, ED, float(h), seed=SEED, return_folds=True)
        G = _capped_G(muD, GD, Gmarg, fid, fcaps, "conditional", TD)
        psi = pseudo_outcome(AD, TD, float(h), muD, G)
        leaves = _cart(psi, XD, 3)[1]
        means, ses, sup = _stats(psi, leaves)
        ok = sup >= SUP
        j = (int(np.nanargmax(np.where(ok, means, -np.inf))) if ok.any()
             else int(np.nanargmax(means)))
        cond = leaves[j]["cond"]
        rule = " & ".join(f"{dgp.COVARIATES[f]} {op} {thr * sd[f] + mu[f]:.1f}"
                          for f, op, thr in cond)
        p1v, p0v = phi_on_holdout(XD, AD, TD, ED, XV, AV, TV, float(h), seed=SEED)
        p1a, p0a = phi_on_holdout(XD, AD, TD, ED, XA, AA, TA, float(h), seed=SEED)
        ev, lo, hi, nv = _ci(p1v - p0v, eval_rule(cond, XV))
        ea, loa, hia, na = _ci(p1a - p0a, eval_rule(cond, XA))
        print(f"validation: effect {ev:+.3f} [{lo:+.3f}, {hi:+.3f}] n={nv}")
        print(f"assessment: effect {ea:+.3f} [{loa:+.3f}, {hia:+.3f}] n={na}")
        print("rule:", rule)
    else:
        print("No feasible horizon; retain 730.")
    return df


if __name__ == "__main__":
    main()
