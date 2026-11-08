"""Gate 31 - outcome-nuisance comparison for AIPW.

Pre-registration: `results/gate31_PREREGISTRATION.md`.

Compares four outcome nuisances on identical folds and identical simulated data:

    cox   per-arm Cox PH (frozen)
    rsf   random survival forest
    gbm   survival gradient boosting
    stack equal-weight mean of the three survival probabilities

The censoring model is held fixed at the conditional Cox used by the frozen
pipeline. Every model is judged by the downstream causal target, not by survival
fit alone.

Usage
-----
    python -m ciscarl2.gate31 --reps 1 --start 900900   # smoke, off-seed
    python -m ciscarl2.gate31 --reps 20 --jobs 8
"""
from __future__ import annotations

import os

# Avoid BLAS/OpenMP oversubscription when joblib runs many workers.
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import argparse
import time

import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.model_selection import KFold, train_test_split
from sksurv.ensemble import (GradientBoostingSurvivalAnalysis,
                             RandomSurvivalForest)
from sksurv.util import Surv

from . import dgp
from .estimators import (_cox_fit, _surv_fallback, aipw, crossfit_nuisances,
                         step_value)
from .gate2 import pseudo_outcome
from .gate4d import TSTAR, _delta_for
from .gate11 import _cart
from .gate19 import _assign_effs, _leaf_table
from .gate20 import _capped_G
from .gate22 import _stats
from .gate23 import E1, E2, _boot, _config23, _regions
from .gate26 import _calibrate_kind, _sim_kind
from .gate30 import _metrics
from .rules import eval_rule, jaccard

from .paths import data_path

DATA = data_path()
START = 900100
KINDS = ("single", "two")
MODELS = ("cox", "rsf", "gbm", "stack")
N = 8000
SUP = 200
Z95 = float(norm.ppf(0.95))
RSF_TREES = 100
GBM_TREES = 60


def _surv_at(model, X, t_star):
    """Evaluate a fitted sksurv model at one horizon, without a per-row loop."""
    u = np.asarray(model.unique_times_, float)
    j = int(np.searchsorted(u, t_star, side="right")) - 1
    if j < 0:
        return np.ones(len(X))
    sf = model.predict_survival_function(X, return_array=True)
    return np.clip(sf[:, j], 1e-6, 1.0)


def _fit_surv(Xfit, Tfit, Efit, Xhold, t_star, model, seed):
    """Fit one outcome nuisance and return S(t_star | Xhold)."""
    if Efit.sum() < 2:
        return np.full(len(Xhold), _surv_fallback(Tfit, Efit, t_star))
    if model == "cox":
        s0, beta, _ = _cox_fit(Xfit, Tfit, Efit, t_star)
        return np.clip(s0 ** np.exp(Xhold @ beta), 1e-6, 1.0)
    if model == "stack":
        parts = [
            _fit_surv(Xfit, Tfit, Efit, Xhold, t_star, "cox", seed),
            _fit_surv(Xfit, Tfit, Efit, Xhold, t_star, "rsf", seed),
            _fit_surv(Xfit, Tfit, Efit, Xhold, t_star, "gbm", seed),
        ]
        return np.clip(np.mean(parts, axis=0), 1e-6, 1.0)

    y = Surv.from_arrays(Efit.astype(bool), Tfit)
    if model == "rsf":
        m = RandomSurvivalForest(
            n_estimators=RSF_TREES, max_depth=5, min_samples_leaf=10,
            random_state=seed, n_jobs=1).fit(Xfit, y)
    elif model == "gbm":
        m = GradientBoostingSurvivalAnalysis(
            n_estimators=GBM_TREES, learning_rate=0.1, max_depth=2,
            random_state=seed).fit(Xfit, y)
    else:  # pragma: no cover - guarded by MODELS
        raise ValueError(f"unknown model {model!r}")
    return _surv_at(m, Xhold, t_star)


def _crossfit_mu(X, A, Tobs, E, t_star, model, fold_id, seed):
    """Cross-fit the outcome nuisance on the pre-computed fold assignment."""
    mu = np.zeros((len(X), 2))
    for k in range(int(fold_id.max()) + 1):
        fit = np.where(fold_id != k)[0]
        hold = np.where(fold_id == k)[0]
        for arm in (0, 1):
            m = fit[A[fit] == arm]
            if len(m) == 0:
                mu[hold, arm] = np.exp(-1e-3 * t_star)
                continue
            mu[hold, arm] = _fit_surv(
                X[m], Tobs[m], E[m], X[hold], t_star, model, seed + 17 * k + arm)
    return np.clip(mu, 1e-6, 1.0)


def _censoring_G(Xfit, Tfit, Efit, Xhold, t_star):
    s0c, betac, _ = _cox_fit(
        Xfit, Tfit, (Efit == 0).astype(int), t_star)
    return np.clip(s0c ** np.exp(Xhold @ betac), 1e-3, 1.0)


def _phi_holdout(XD, AD, TD, ED, XH, AH, TH, t_star, model, seed):
    mu1 = _fit_surv(XD[AD == 1], TD[AD == 1], ED[AD == 1],
                    XH, t_star, model, seed)
    mu0 = _fit_surv(XD[AD == 0], TD[AD == 0], ED[AD == 0],
                    XH, t_star, model, seed + 1)
    G = _censoring_G(XD, TD, ED, XH, t_star)
    Y = np.where(TH > t_star, 1.0, 0.0) / G
    phi1 = mu1 + (AH == 1) / 0.5 * (Y - mu1)
    phi0 = mu0 + (AH == 0) / 0.5 * (Y - mu0)
    return phi1, phi0


def _downstream(psi, XD, XV, XA, dphi_v, dphi_a, const, truth, union_a):
    """Frozen C200 on the supplied psi and validation/assessment phi."""
    leaves = _cart(psi, XD, 3)[1]
    means, ses, sup = _stats(psi, leaves)
    ok = sup >= SUP
    fallback = not bool(ok.any())
    j = (int(np.nanargmax(np.where(ok, means, -np.inf))) if ok.any()
         else int(np.nanargmax(means)))

    tbl_v = _leaf_table(leaves, XV, dphi_v)
    effs = np.array([t["eff"] for t in tbl_v], float)
    ses_v = np.array([t["se"] for t in tbl_v], float)
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
                  eff=use[t], se=ses_v[t]) for t in range(len(leaves))]
    pred = _assign_effs(tbl_a, XA, use, const)
    treated = masks_a[j] if committed else np.zeros(len(XA), bool)
    row = _metrics(pred, treated, truth, union_a)
    rule = masks_a[j]
    k_rule = int(rule.sum())
    row.update(
        support=int(sup[j]), fallback=fallback, committed=committed,
        jaccard=jaccard(rule, union_a),
        purity_rule=(float((rule & union_a).sum() / k_rule) if k_rule else np.nan),
        capture_rule=(float(truth[rule].sum() / truth.sum())
                      if (k_rule and truth.sum() > 0) else np.nan),
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
    tau_d = tau_i[disc]
    S0d, S1d = sim["S0"][disc], sim["S1"][disc]

    # one Cox cross-fit supplies the fold assignment and the censoring weights
    mu_cox, GD, Gmarg, fid, fcaps, _ = crossfit_nuisances(
        XD, AD, TD, ED, TSTAR, seed=seed, return_folds=True)
    G = _capped_G(mu_cox, GD, Gmarg, fid, fcaps, "conditional", TD)

    rows = []
    for model in MODELS:
        t0 = time.time()
        muD = (mu_cox if model == "cox"
               else _crossfit_mu(XD, AD, TD, ED, TSTAR, model, fid, seed))
        psi = pseudo_outcome(AD, TD, TSTAR, muD, G)
        tau_hat, se, _, _ = aipw(XD, AD, TD, TSTAR, muD, G)
        const = float(tau_hat)
        elapsed = time.time() - t0

        p1v, p0v = _phi_holdout(XD, AD, TD, ED, XV, AV, TV, TSTAR,
                                model, seed)
        p1a, p0a = _phi_holdout(XD, AD, TD, ED, XA, AA, TA, TSTAR,
                                model, seed)
        dphi_v, dphi_a = p1v - p0v, p1a - p0a

        mae_nuis = float(np.abs((muD[:, 1] - muD[:, 0]) - tau_d).mean())
        brier = float(0.5 * (np.mean((muD[:, 0] - S0d) ** 2) +
                             np.mean((muD[:, 1] - S1d) ** 2)))
        lo, hi = tau_hat - 1.96 * se, tau_hat + 1.96 * se
        covered = bool(lo <= tau_d.mean() <= hi)

        down = _downstream(psi, XD, XV, XA, dphi_v, dphi_a, const,
                           truth, uniA)
        rows.append(dict(
            rep=rep, kind=kind, model=model, n=N,
            tau_hat=tau_hat, tau_true=float(tau_d.mean()),
            bias=tau_hat - float(tau_d.mean()), se=se,
            covered=covered, ci_lo=lo, ci_hi=hi,
            mae_nuis=mae_nuis, brier=brier,
            mae_assessment=down["mae_assessment"],
            purity=down["purity_rule"], capture=down["capture_rule"],
            jaccard=down["jaccard"], commit=down["committed"],
            support=down["support"], fallback=down["fallback"],
            seconds=elapsed,
        ))
    return rows


def summarise(raw):
    out = []
    for kind in sorted(raw.kind.unique()):
        g = raw[raw.kind == kind]
        base = g[g.model == "cox"].set_index("rep")
        for model in MODELS:
            d = g[g.model == model].set_index("rep")
            common = sorted(set(base.index) & set(d.index))
            row = dict(kind=kind, model=model, reps=len(d),
                       bias=d.bias.mean(), abs_bias=d.bias.abs().mean(),
                       coverage=100.0 * d.covered.mean(),
                       mae_nuis=d.mae_nuis.mean(), brier=d.brier.mean(),
                       purity=d.purity.mean(), capture=d.capture.mean(),
                       jaccard=d.jaccard.mean(),
                       commit=100.0 * d.commit.mean(),
                       mae_assessment=d.mae_assessment.mean(),
                       support=d.support.mean(),
                       seconds=d.seconds.mean())
            for metric in ("mae_nuis", "bias", "brier", "purity", "capture"):
                diff = (d.loc[common, metric] - base.loc[common, metric]).to_numpy()
                lo, hi, p = _boot(diff, seed=7)
                row[f"d_{metric}"] = float(diff.mean())
                row[f"lo_{metric}"] = lo
                row[f"hi_{metric}"] = hi
                row[f"p_{metric}"] = p
            out.append(row)
    return pd.DataFrame(out)


def _holm(df, col="p_mae_nuis"):
    df = df.copy()
    df["p_holm"] = np.nan
    for kind, g in df.groupby("kind"):
        alt = g[g.model != "cox"].sort_values(col)
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
    ap.add_argument("--rsf-trees", type=int, default=100)
    ap.add_argument("--gbm-trees", type=int, default=60)
    ap.add_argument("--models", default="cox,rsf,gbm,stack",
                    help="comma-separated subset of cox,rsf,gbm,stack")
    args = ap.parse_args(argv)

    global START, RSF_TREES, GBM_TREES, MODELS
    START = args.start if args.start is not None else START
    RSF_TREES, GBM_TREES = args.rsf_trees, args.gbm_trees
    MODELS = tuple(m.strip() for m in args.models.split(",") if m.strip())
    bad = [m for m in MODELS if m not in ("cox", "rsf", "gbm", "stack")]
    if bad:
        raise SystemExit(f"unknown models: {bad}")
    if "cox" not in MODELS:
        raise SystemExit("cox must be included as the baseline")
    cfg = _config23()
    lam = {k: _calibrate_kind(cfg, k) for k in KINDS}
    print("  lam:", {k: round(v, 6) for k, v in lam.items()}, flush=True)

    from joblib import Parallel, delayed
    jobs = [(rep, kind) for kind in KINDS for rep in range(args.reps)]
    out = Parallel(n_jobs=args.jobs, verbose=5)(
        delayed(run_rep)(rep, kind, cfg, lam[kind]) for rep, kind in jobs)

    raw = pd.DataFrame([r for ch in out for r in ch])
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw.to_csv(os.path.join(root, "results", "gate31_replications.csv"),
               index=False)
    res = _holm(summarise(raw))
    res.to_csv(os.path.join(root, "results", "gate31_summary.csv"), index=False)

    print(f"\n=== Gate 31, outcome nuisance, {args.reps} reps ===")
    cols = ["kind", "model", "bias", "coverage", "mae_nuis", "brier",
            "purity", "capture", "commit", "mae_assessment", "seconds"]
    print(res[cols].round(4).to_string(index=False))
    print("\nPaired vs Cox (bootstrap 95% CI, Holm on MAE):")
    for _, r in res.iterrows():
        if r.model == "cox":
            continue
        print(f"  {r.kind:>6} {r.model:>5}  "
              f"dMAE={r.d_mae_nuis:+.4f} [{r.lo_mae_nuis:+.4f},{r.hi_mae_nuis:+.4f}] "
              f"p={r.p_mae_nuis:.3f} Holm={r.p_holm:.3f}  "
              f"dBrier={r.d_brier:+.4f}  dPurity={r.d_purity:+.3f}")
    return raw, res


if __name__ == "__main__":
    main()
