"""Gate 42 - dense horizon optimisation.

Pre-registration: `results/gate42_PREREGISTRATION.md`.

Maximise validation LCB over 365..1,095 in 30-day steps, subject to >=100 events,
>=30% at risk and support >=60. Assessment is descriptive only.

Usage
-----
    python -m ciscarl2.gate42
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
GRID = tuple(range(365, 1096, 30))
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
    for h in GRID:
        muD, GD, Gmarg, fid, fcaps, _ = crossfit_nuisances(
            XD, AD, TD, ED, float(h), seed=SEED, return_folds=True)
        G = _capped_G(muD, GD, Gmarg, fid, fcaps, "conditional", TD)
        psi = pseudo_outcome(AD, TD, float(h), muD, G)
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
        dphi_v = p1v - p0v
        eff_v, lo_v, hi_v, n_v = _ci(dphi_v, eval_rule(cond, XV))
        se_v = (hi_v - lo_v) / (2 * float(tdist.ppf(0.975, max(n_v - 1, 1))))
        lcb = eff_v - Z95 * se_v if np.isfinite(se_v) else np.nan
        eff_a, lo_a, hi_a, n_a = _ci(p1a - p0a, eval_rule(cond, XA))

        rows.append(dict(
            horizon=h,
            events=int(((TD <= h) & (ED == 1)).sum()),
            at_risk=float((TD > h).mean()),
            support=int(sup[j]), fallback=fallback,
            val_effect=eff_v, val_se=se_v, val_lcb=lcb,
            asm_effect=eff_a, rule=rule,
        ))

    df = pd.DataFrame(rows)
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    df.to_csv(os.path.join(root, "results", "gate42_horizon_grid.csv"), index=False)

    feasible = df[(df.events >= 100) & (df.at_risk >= 0.30) & (df.support >= 60)]
    print("=== Gate 42, dense horizon grid ===")
    print(df[["horizon", "events", "at_risk", "support", "val_effect",
              "val_se", "val_lcb", "asm_effect"]].round(3).to_string(index=False))
    print(f"\nfeasible horizons: {len(feasible)}")
    if len(feasible):
        best = feasible.sort_values("val_lcb", ascending=False).iloc[0]
        print(f"OPTIMUM: {int(best.horizon)} days | LCB {best.val_lcb:+.3f} | "
              f"effect {best.val_effect:+.3f} | support {int(best.support)} | "
              f"assessment {best.asm_effect:+.3f}")
        print("rule:", best.rule)
        print("\nTop 5 feasible:")
        print(feasible.sort_values("val_lcb", ascending=False)
              [["horizon", "events", "at_risk", "support", "val_effect",
                "val_lcb"]].head().round(3).to_string(index=False))
    else:
        print("No feasible horizon; retain 730.")
    return df


if __name__ == "__main__":
    main()
