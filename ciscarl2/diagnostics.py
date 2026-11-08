"""ACTG175 nuisance diagnostics: PH, ties, survival calibration, weight-cap sensitivity.

Run:  python -m ciscarl2.diagnostics
Writes: results/diagnostics.md, results/diagnostics_calibration.csv,
        results/diagnostics_caps.csv
"""
from __future__ import annotations

import os

import numpy as np
import pandas as pd
from lifelines import CoxPHFitter, KaplanMeierFitter
from lifelines.statistics import proportional_hazard_test
from sklearn.model_selection import train_test_split

from .estimators import crossfit_nuisances, truncate_weights
from .gate2 import pseudo_outcome
from .gate11 import _cart
from .gate22 import _stats
from .paths import data_path
from .rules import eval_rule

COV = ["cd40", "cd80", "age", "wtkg", "karnof", "hemo", "homo",
       "race", "gender", "drugs", "str2", "symptom"]
HORIZON = 730.0
SEED = 2024


def _load():
    d = pd.read_csv(data_path())
    d = d[d["arms"].isin([0, 1])].reset_index(drop=True)
    X = d[COV].to_numpy(float)
    A = (d["arms"] == 1).to_numpy(int)
    T = d["days"].to_numpy(float)
    E = d["cens"].to_numpy(int)
    idx = np.arange(len(d))
    strat = A * 2 + E
    disc, hold = train_test_split(idx, test_size=0.5, random_state=SEED, stratify=strat)
    val, asm = train_test_split(hold, test_size=0.5, random_state=SEED + 1, stratify=strat[hold])
    return d, X, A, T, E, disc, val, asm


def ph_diagnostics(X, A, T, E, disc):
    """Global and per-covariate proportional-hazards tests, per arm."""
    rows = []
    for arm in (0, 1):
        m = A[disc] == arm
        df = pd.DataFrame(X[disc][m], columns=COV)
        df["T"], df["D"] = T[disc][m], E[disc][m]
        cph = CoxPHFitter().fit(df, "T", "D")
        res = proportional_hazard_test(cph, df, time_transform="rank")
        p = res.summary["p"]
        from scipy.stats import chi2 as _chi2
        stat = float(-2.0 * np.sum(np.log(np.clip(p.values, 1e-12, 1.0))))
        pglob = float(_chi2.sf(stat, 2 * len(p)))
        rows.append({"arm": arm, "test": "global (Fisher combination)",
                     "statistic": stat, "p_value": pglob})
        for cov in COV:
            rows.append({"arm": arm, "test": cov,
                         "statistic": float("nan"),
                         "p_value": float(p.loc[cov])})
    out = pd.DataFrame(rows)
    out["flag_p<0.05"] = out.p_value < 0.05
    return out


def tie_comparison(X, A, T, E, disc):
    """Efron vs Breslow coefficients (statsmodels PHReg)."""
    try:
        from statsmodels.duration.hazard_regression import PHReg
    except Exception:
        return pd.DataFrame([{"note": "statsmodels unavailable"}])
    rows = []
    for arm in (0, 1):
        m = A[disc] == arm
        Xa, Ta, Ea = X[disc][m], T[disc][m], E[disc][m]
        betas = {}
        for ties in ("efron", "breslow"):
            fit = PHReg(Ta, Xa, status=Ea, ties=ties).fit(disp=0)
            betas[ties] = np.asarray(fit.params, float)
        diff = np.abs(betas["efron"] - betas["breslow"])
        rows.append({"arm": arm, "max_abs_coef_diff": float(diff.max()),
                     "mean_abs_coef_diff": float(diff.mean()),
                     "corr": float(np.corrcoef(betas["efron"], betas["breslow"])[0, 1])})
    return pd.DataFrame(rows)


def calibration(X, A, T, E, disc, asm, t=HORIZON, bins=3):
    """Predicted S(t) versus KM within predicted-risk bins, per arm."""
    mu, sd = X[disc].mean(0), X[disc].std(0)
    Xs = (X - mu) / sd
    rows = []
    for arm in (0, 1):
        dm = A[disc] == arm
        df = pd.DataFrame(Xs[disc][dm], columns=COV)
        df["T"], df["D"] = T[disc][dm], E[disc][dm]
        cph = CoxPHFitter(penalizer=0.01).fit(df, "T", "D")
        base = float(cph.baseline_survival_.reindex([t], method="ffill").iloc[0, 0])
        beta = cph.params_.values
        am = A[asm] == arm
        pred = base ** np.exp(Xs[asm][am] @ beta)
        obs_t, obs_e = T[asm][am], E[asm][am]
        km_all = KaplanMeierFitter().fit(obs_t, obs_e, timeline=[t])
        rows.append({"arm": arm, "bin": 0, "n": int(am.sum()),
                     "predicted": float(pred.mean()),
                     "observed_km": float(km_all.survival_function_.iloc[0, 0])})
        q = pd.qcut(pred, q=bins, labels=False, duplicates="drop")
        for b in sorted(pd.unique(q)):
            mask = q == b
            if mask.sum() < 15:
                continue
            km = KaplanMeierFitter().fit(obs_t[mask], obs_e[mask], timeline=[t])
            rows.append({"arm": arm, "bin": int(b) + 1, "n": int(mask.sum()),
                         "predicted": float(pred[mask].mean()),
                         "observed_km": float(km.survival_function_.iloc[0, 0])})
    dfc = pd.DataFrame(rows)
    dfc["gap"] = dfc.observed_km - dfc.predicted
    return dfc


def cap_sensitivity(X, A, T, E, disc, val, caps=(1.2, 1.5, 2.0, 5.0, 20.0)):
    """Effect of the weight cap on psi, selected rule and validation effect."""
    mu, sd = X[disc].mean(0), X[disc].std(0)
    Xs = (X - mu) / sd
    rows = []
    for cap in caps:
        muD, GD, _, fid, fcaps, _ = crossfit_nuisances(
            Xs[disc], A[disc], T[disc], E[disc], HORIZON, seed=SEED, return_folds=True)
        w_raw = 1.0 / GD
        frac_bind = float(np.mean(w_raw > cap))
        G = np.maximum(GD, 1.0 / cap)
        psi = pseudo_outcome(A[disc], T[disc], HORIZON, muD, G)
        leaves = _cart(psi, Xs[disc], 3)[1]
        means, ses, sup = _stats(psi, leaves)
        ok = sup >= 200
        j = int(np.nanargmax(np.where(ok, means, -np.inf))) if ok.any() else int(np.nanargmax(means))
        rows.append({"cap": cap, "pct_capped": 100 * frac_bind,
                     "selected_leaf": j + 1,
                     "support": int(sup[j]), "mean_psi": float(means[j]),
                     "fallback": bool(not ok.any()),
                     "max_weight_raw": float(w_raw.max()),
                     "ess": float(G.sum() ** 2 / (G ** 2).sum())})
    return pd.DataFrame(rows)


def main():
    d, X, A, T, E, disc, val, asm = _load()
    out = []
    out.append("# ACTG175 nuisance diagnostics\n")

    ph = ph_diagnostics(X, A, T, E, disc)
    ph.to_csv("results/diagnostics_ph.csv", index=False)
    out.append("## Proportional hazards (Schoenfeld, rank transform)\n")
    out.append(ph.round(4).to_string(index=False))
    out.append("")

    ties = tie_comparison(X, A, T, E, disc)
    ties.to_csv("results/diagnostics_ties.csv", index=False)
    out.append("\n## Cox tie handling: Efron vs Breslow\n")
    out.append(ties.round(4).to_string(index=False))
    out.append("")

    cal = calibration(X, A, T, E, disc, asm)
    cal.to_csv("results/diagnostics_calibration.csv", index=False)
    out.append("\n## Survival calibration at 730 days (assessment, predicted-risk bins)\n")
    out.append(cal.round(3).to_string(index=False))
    ece = float(np.average(np.abs(cal.gap), weights=cal.n))
    out.append(f"\nweighted mean |gap| (ECE-like): {ece:.3f}")

    caps = cap_sensitivity(X, A, T, E, disc, val)
    caps.to_csv("results/diagnostics_caps.csv", index=False)
    out.append("\n## Weight-cap sensitivity\n")
    out.append(caps.round(3).to_string(index=False))

    os.makedirs("results", exist_ok=True)
    with open("results/diagnostics.md", "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
