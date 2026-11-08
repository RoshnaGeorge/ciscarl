"""Policy value, net benefit and interval coverage for C200 vs treat-all/none and SCRE.

Run:  python -m ciscarl2.policy_eval --reps 40 --jobs 8
Writes: results/policy_eval_raw.csv, results/policy_eval_summary.csv,
        results/net_benefit.csv
"""
from __future__ import annotations

import argparse
import contextlib
import io
import os

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from . import dgp
from .estimators import (aipw, crossfit_nuisances, phi_on_holdout,
                         truncate_weights)
from .gate2 import pseudo_outcome
from .gate4 import scre_select_alpha
from .gate4d import TSTAR, _delta_for
from .gate11 import _cart
from .gate20 import _capped_G
from .gate22 import _stats
from .gate23 import E1, E2, _config23, _regions
from .gate26 import _calibrate_kind, _sim_kind
from .rules import eval_rule

SUP = 200
START = 700100
LAMBDAS = (0.0, 0.05, 0.10, 0.20, 0.50)


def _scre_fit(XD, XV, AV, TV, EV, psi, AD, TD, ED):
    """Return SCRE predictions on XV (or None if unavailable)."""
    try:
        from .external.scre import SurvivalCausalRuleEnsemble
    except Exception:
        return None
    try:
        s = SurvivalCausalRuleEnsemble(
            alpha=0.5, pred_n_estimators=100, progn_n_estimators=100,
            rule_min_support=20, max_rules=200, max_rule_conditions=3,
            max_selected_rules=10, random_state=42)
        with contextlib.redirect_stdout(io.StringIO()):
            s.fit(XD, psi, np.isfinite(psi),
                  feature_names=[f"x{i}" for i in range(XD.shape[1])],
                  time=TD, event=ED.astype(bool), treatment=AD)
            pick = scre_select_alpha(s, XV, AV, TV, EV.astype(bool), TSTAR)
        if pick is not None:
            s.alpha_ = s.alpha_final_ = pick[1]
            s.coef_ = pick[2]
        s.t_star_ = TSTAR
        with contextlib.redirect_stdout(io.StringIO()):
            return np.asarray(s.predict(XV), float)
    except Exception:
        return None


def run_rep(rep, kind, cfg, lam_c):
    seed = START + rep
    rng = np.random.RandomState(seed)
    n = 8000
    pool, lam0 = cfg[0], cfg[5]
    X = pool[rng.choice(len(pool), n, replace=True)]
    R1, R2 = _regions(X, cfg)
    if kind == "single":
        R2 = np.zeros(n, bool)
    union = R1 | R2
    lp0 = X @ dgp.BETA
    s0 = np.exp(-lam0 * TSTAR * np.exp(lp0))
    e1 = np.where(R1, _delta_for(E1, s0), 0.0)
    e2 = np.where(R2, _delta_for(E2, s0), 0.0)
    A = rng.binomial(1, 0.5, n)
    sim = _sim_kind(X, A, lam_c, lam0, rng, e1, e2)
    T, E = sim["Tobs"], sim["E"]

    ii = np.arange(n)
    disc, hold = train_test_split(ii, test_size=0.5, random_state=seed, stratify=A)
    val, asm = train_test_split(hold, test_size=0.5, random_state=seed + 1,
                                stratify=A[hold])
    XD, AD, TD, ED = X[disc], A[disc], T[disc], E[disc]
    XV, AV, TV, EV = X[val], A[val], T[val], E[val]
    XA, AA, TA, EA = X[asm], A[asm], T[asm], E[asm]
    S0a, S1a, tau_a = sim["S0"][asm], sim["S1"][asm], (sim["S1"] - sim["S0"])[asm]

    muD, GD, _, fid, fcaps, _ = crossfit_nuisances(
        XD, AD, TD, ED, TSTAR, seed=seed, return_folds=True)
    G, _cap = truncate_weights(GD, fid, fcaps)
    psi = pseudo_outcome(AD, TD, TSTAR, muD, G)

    leaves = _cart(psi, XD, 3)[1]
    means, ses, sup = _stats(psi, leaves)
    ok = sup >= SUP
    j = int(np.nanargmax(np.where(ok, means, -np.inf))) if ok.any() else int(np.nanargmax(means))
    cond = leaves[j]["cond"]

    p1v, p0v = phi_on_holdout(XD, AD, TD, ED, XV, AV, TV, TSTAR, seed=seed)
    dv = p1v - p0v
    mv = eval_rule(cond, XV)
    kv = int(mv.sum())
    eff = float(dv[mv].mean()) if kv else np.nan
    se = float(np.sqrt(((dv[mv] - eff) ** 2).sum()) / kv) if kv else np.nan
    committed = bool(kv and eff > 1.645 * se)

    ma = eval_rule(cond, XA)
    treated_c200 = ma if committed else np.zeros(len(asm), bool)

    tau_s = _scre_fit(XD, XV, AV, TV, EV, psi, AD, TD, ED)
    treated_scre = (tau_s > 0) if tau_s is not None and np.all(np.isfinite(tau_s)) else np.zeros(len(asm), bool)

    def value(treated):
        t = np.asarray(treated, bool)
        return float(np.where(t, S1a, S0a).mean())

    rows = []
    for name, treated in (("none", np.zeros(len(asm), bool)),
                          ("all", np.ones(len(asm), bool)),
                          ("C200", treated_c200),
                          ("SCRE", treated_scre)):
        if name == "SCRE" and tau_s is None:
            continue
        rows.append({"rep": rep, "kind": kind, "policy": name,
                     "value": value(treated), "treat_rate": float(np.mean(treated))})

    # interval coverage for the selected rule (validation CI vs true rule effect)
    true_rule = float(tau_a[ma].mean()) if ma.sum() else np.nan
    covered = bool(np.isfinite(true_rule) and np.isfinite(eff) and
                   (eff - 1.96 * se) <= true_rule <= (eff + 1.96 * se))
    rows.append({"rep": rep, "kind": kind, "policy": "C200_rule_ci",
                 "value": np.nan, "treat_rate": np.nan,
                 "true_rule_effect": true_rule, "val_effect": eff,
                 "val_se": se, "covered": covered,
                 "ci_lo": eff - 1.96 * se, "ci_hi": eff + 1.96 * se})
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=40)
    ap.add_argument("--jobs", type=int, default=8)
    args = ap.parse_args(argv)

    cfg = _config23()
    lam = {k: _calibrate_kind(cfg, k) for k in ("single", "two")}
    from joblib import Parallel, delayed
    out = Parallel(n_jobs=args.jobs)(
        delayed(run_rep)(rep, kind, cfg, lam[kind])
        for kind in ("single", "two") for rep in range(args.reps))
    df = pd.DataFrame([r for ch in out for r in ch])
    df.to_csv("results/policy_eval_raw.csv", index=False)

    pol = df[df.policy.isin(["none", "all", "C200", "SCRE"])]
    summ = (pol.groupby(["kind", "policy"])
              .agg(value=("value", "mean"), treat_rate=("treat_rate", "mean"),
                   reps=("rep", "nunique"))
              .reset_index())
    summ["value_vs_none"] = summ.apply(
        lambda r: r.value - summ[(summ.kind == r.kind) & (summ.policy == "none")].value.iloc[0],
        axis=1)
    summ.to_csv("results/policy_eval_summary.csv", index=False)

    # net benefit U = V - lambda * treat_rate
    nb_rows = []
    for kind in ("single", "two"):
        g = pol[pol.kind == kind]
        for lam_ in LAMBDAS:
            for policy in ("C200", "SCRE", "all"):
                sub = g[g.policy == policy]
                if not len(sub):
                    continue
                nb_rows.append({"kind": kind, "lambda": lam_, "policy": policy,
                                "net_benefit": float((sub.value - lam_ * sub.treat_rate).mean())})
    nb = pd.DataFrame(nb_rows)
    nb.to_csv("results/net_benefit.csv", index=False)

    cov = df[df.policy == "C200_rule_ci"]
    print("=== policy value (mean expected event-free survival at 730) ===")
    print(summ.round(4).to_string(index=False))
    print("\n=== C200 validation interval coverage of the true rule effect ===")
    for kind in ("single", "two"):
        c = cov[cov.kind == kind]
        print(f"  {kind:7s} reps={len(c):3d} coverage={100*c.covered.mean():5.1f}% "
              f"mean width={float((c.ci_hi-c.ci_lo).mean()):.3f}")
    print("\n=== net benefit U = V - lambda * treatment rate ===")
    print(nb.pivot_table(index=["kind", "lambda"], columns="policy",
                         values="net_benefit").round(4).to_string())


if __name__ == "__main__":
    main()
