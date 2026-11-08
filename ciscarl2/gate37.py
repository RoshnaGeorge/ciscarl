"""Gate 37 - horizon selection on ACTG175.

Pre-registration: `results/gate37_PREREGISTRATION.md`.

Compares 365, 548, 730, 912 and 1,095 days on events, at-risk, support,
validation precision and the selected rule. Assessment is descriptive only.

Usage
-----
    python -m ciscarl2.gate37
"""
from __future__ import annotations

import os

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
SEED = 2024
SUP = 200
HORIZONS = (365, 548, 730, 912, 1095)
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
    for h in HORIZONS:
        muD, GD, Gmarg, fid, fcaps, _ = crossfit_nuisances(
            XD, AD, TD, ED, float(h), seed=SEED, return_folds=True)
        G = _capped_G(muD, GD, Gmarg, fid, fcaps, "conditional", TD)
        psi = pseudo_outcome(AD, TD, float(h), muD, G)
        const = float(aipw(XD, AD, TD, float(h), muD, G)[0])
        leaves = _cart(psi, XD, 3)[1]
        means, ses, sup = _stats(psi, leaves)
        ok = sup >= SUP
        fallback = not bool(ok.any())
        j = (int(np.nanargmax(np.where(ok, means, -np.inf))) if ok.any()
             else int(np.nanargmax(means)))
        cond = leaves[j]["cond"]
        rule = " & ".join(f"{dgp.COVARIATES[f]} {op} {thr * sd[f] + mu[f]:.1f}"
                          for f, op, thr in cond)

        p1v, p0v = phi_on_holdout(XD, AD, TD, ED, XV, AV, TV, float(h), seed=SEED)
        p1a, p0a = phi_on_holdout(XD, AD, TD, ED, XA, AA, TA, float(h), seed=SEED)
        dphi_v, dphi_a = p1v - p0v, p1a - p0a
        eff_v, lo_v, hi_v, n_v = _ci(dphi_v, eval_rule(cond, XV))
        eff_a, lo_a, hi_a, n_a = _ci(dphi_a, eval_rule(cond, XA))
        se_v = (hi_v - lo_v) / (2 * float(tdist.ppf(0.975, max(n_v - 1, 1))))
        lcb = eff_v - Z95 * se_v if np.isfinite(se_v) else np.nan

        rows.append(dict(
            horizon=h,
            events=int(((TD <= h) & (ED == 1)).sum()),
            at_risk=float((TD > h).mean()),
            censored=float(((TD <= h) & (ED == 0)).mean()),
            support=int(sup[j]), fallback=fallback,
            n_conditions=len(cond), rule=rule,
            tau_discovery=const,
            val_effect=eff_v, val_se=se_v, val_lcb=lcb, val_n=n_v,
            asm_effect=eff_a, asm_lo=lo_a, asm_hi=hi_a, asm_n=n_a,
        ))

    df = pd.DataFrame(rows)
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    df.to_csv(os.path.join(root, "results", "gate37_horizon.csv"), index=False)

    print("=== Gate 37, horizon selection ===")
    show = df[["horizon", "events", "at_risk", "censored", "support",
               "fallback", "val_effect", "val_se", "val_lcb",
               "asm_effect", "n_conditions"]].round(3)
    print(show.to_string(index=False))
    print("\nRules:")
    for _, r in df.iterrows():
        print(f"  {r.horizon:4d}d  {r.rule}  | support {r.support}"
              f"  | LCB {r.val_lcb:+.3f}")

    base = df[df.horizon == 730].iloc[0]
    checks = []
    for _, r in df.iterrows():
        checks.append(dict(
            horizon=int(r.horizon),
            events_ok=bool(r.events >= 150),
            at_risk_ok=bool(r.at_risk >= 0.30),
            se_ok=bool(r.val_se <= base.val_se + 0.02),
            support_ok=bool(r.support >= SUP or (r.fallback and r.support >= 60)),
        ))
    checks = pd.DataFrame(checks)
    print("\nCriteria:")
    print(checks.to_string(index=False))
    return df, checks


if __name__ == "__main__":
    main()
