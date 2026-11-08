"""Gate 36 - fixed-horizon IPCW-TMLE vs AIPW.

Pre-registration: `results/gate36_PREREGISTRATION.md`.

Both estimators use the same cross-fitted Cox nuisances, folds, partitions and
C200 learner. The only difference is the targeting step.

Usage
-----
    python -m ciscarl2.gate36 --reps 2 --start 940900   # smoke
    python -m ciscarl2.gate36 --reps 20 --jobs 8
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import argparse
import time

import numpy as np
import pandas as pd
from scipy.optimize import brentq
from scipy.special import expit, logit
from sklearn.model_selection import train_test_split

from . import dgp
from .estimators import (_cox_fit, aipw, crossfit_nuisances, phi_on_holdout)
from .gate2 import pseudo_outcome
from .gate4d import TSTAR, _delta_for
from .gate20 import _capped_G
from .gate23 import E1, E2, _boot, _config23, _regions
from .gate26 import _calibrate_kind, _sim_kind
from .gate31 import _downstream

from .paths import data_path

DATA = data_path()
START = 940100
KINDS = ("single", "two")
N = 8000
Z95 = 1.959963984540054


def _clip(p):
    return np.clip(np.asarray(p, float), 1e-6, 1 - 1e-6)


def _fit_epsilon(mu, A, arm, Y, G, e=0.5):
    """Solve sum H (Y - expit(logit(mu)+eps H)) = 0 for one arm."""
    e_a = e if arm == 1 else 1.0 - e
    H = (A == arm).astype(float) / e_a * Y / np.maximum(G, 1e-6)
    if H.sum() <= 0:
        return 0.0
    base = logit(_clip(mu))

    def score(eps):
        return float(np.sum(H * (Y - expit(base + eps * H))))

    lo, hi = -20.0, 20.0
    if score(lo) * score(hi) > 0:
        return 0.0
    return float(brentq(score, lo, hi, maxiter=100))


def _targeted_mu(mu, A, arm, Y, G, eps):
    e_a = 0.5 if arm == 1 else 0.5
    H = (A == arm).astype(float) / e_a * Y / np.maximum(G, 1e-6)
    return expit(logit(_clip(mu)) + eps * H)


def _targeted_phi(XD, AD, TD, ED, XH, AH, TH, eps1, eps0):
    """Apply the discovery targeting step to held-out patients."""
    mu1 = np.zeros(len(XH))
    mu0 = np.zeros(len(XH))
    for arm, out in ((1, mu1), (0, mu0)):
        m = AD == arm
        s0, beta, _ = _cox_fit(XD[m], TD[m], ED[m], TSTAR)
        out[:] = _clip(s0 ** np.exp(XH @ beta))
    s0c, betac, _ = _cox_fit(XD, TD, (ED == 0).astype(int), TSTAR)
    G = np.clip(s0c ** np.exp(XH @ betac), 1e-3, 1.0)
    Y = (TH > TSTAR).astype(float)
    H1 = (AH == 1).astype(float) / 0.5 * Y / G
    H0 = (AH == 0).astype(float) / 0.5 * Y / G
    m1 = expit(logit(mu1) + eps1 * H1)
    m0 = expit(logit(mu0) + eps0 * H0)
    Yipcw = Y / G
    phi1 = m1 + (AH == 1) / 0.5 * (Yipcw - m1)
    phi0 = m0 + (AH == 0) / 0.5 * (Yipcw - m0)
    return phi1, phi0


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

    muD, GD, Gmarg, fid, fcaps, _ = crossfit_nuisances(
        XD, AD, TD, ED, TSTAR, seed=seed, return_folds=True)
    G = _capped_G(muD, GD, Gmarg, fid, fcaps, "conditional", TD)
    Y = (TD > TSTAR).astype(float)
    Yipcw = Y / G

    # AIPW baseline
    psi_a = pseudo_outcome(AD, TD, TSTAR, muD, G)
    t_a, se_a, _, _ = aipw(XD, AD, TD, TSTAR, muD, G)
    p1v, p0v = phi_on_holdout(XD, AD, TD, ED, XV, AV, TV, TSTAR, seed=seed)
    p1a, p0a = phi_on_holdout(XD, AD, TD, ED, XA, AA, TA, TSTAR, seed=seed)
    down_a = _downstream(psi_a, XD, XV, XA, p1v - p0v, p1a - p0a, t_a,
                         truth, uniA)

    # TMLE targeting
    t0 = time.time()
    eps1 = _fit_epsilon(muD[:, 1], AD, 1, Y, G)
    eps0 = _fit_epsilon(muD[:, 0], AD, 0, Y, G)
    m1 = _targeted_mu(muD[:, 1], AD, 1, Y, G, eps1)
    m0 = _targeted_mu(muD[:, 0], AD, 0, Y, G, eps0)
    psi_t = (m1 - m0 + (AD == 1) / 0.5 * (Yipcw - m1)
             - (AD == 0) / 0.5 * (Yipcw - m0))
    tau_t = float(np.mean(m1 - m0))
    se_t = float(np.sqrt(((psi_t - psi_t.mean()) ** 2).sum()) / len(psi_t))
    p1vt, p0vt = _targeted_phi(XD, AD, TD, ED, XV, AV, TV, eps1, eps0)
    p1at, p0at = _targeted_phi(XD, AD, TD, ED, XA, AA, TA, eps1, eps0)
    down_t = _downstream(psi_t, XD, XV, XA, p1vt - p0vt, p1at - p0at,
                         float(psi_t.mean()), truth, uniA)
    elapsed = time.time() - t0

    rows = []
    for est, tau, se, psi, down in (
            ("aipw", t_a, se_a, psi_a, down_a),
            ("tmle", tau_t, se_t, psi_t, down_t)):
        lo, hi = tau - Z95 * se, tau + Z95 * se
        mae = float(np.abs((m1 - m0 if est == "tmle" else
                            muD[:, 1] - muD[:, 0]) - tau_d).mean())
        brier = float(0.5 * (
            np.mean((m1 - S1d) ** 2) + np.mean((m0 - S0d) ** 2))
            if est == "tmle" else
            0.5 * (np.mean((muD[:, 1] - S1d) ** 2) +
                   np.mean((muD[:, 0] - S0d) ** 2)))
        rows.append(dict(
            rep=rep, kind=kind, estimator=est,
            bias=tau - float(tau_d.mean()), se=se,
            covered=bool(lo <= tau_d.mean() <= hi),
            mae_nuis=mae, brier=brier,
            purity=down["purity_rule"], capture=down["capture_rule"],
            jaccard=down["jaccard"], commit=down["committed"],
            mae_assessment=down["mae_assessment"],
            seconds=(elapsed if est == "tmle" else 0.0),
        ))
    return rows


def summarise(raw):
    out = []
    for kind in sorted(raw.kind.unique()):
        g = raw[raw.kind == kind]
        base = g[g.estimator == "aipw"].set_index("rep")
        for est in ("aipw", "tmle"):
            d = g[g.estimator == est].set_index("rep")
            common = sorted(set(base.index) & set(d.index))
            row = dict(kind=kind, estimator=est, reps=len(d),
                       bias=d.bias.mean(), abs_bias=d.bias.abs().mean(),
                       coverage=100.0 * d.covered.mean(),
                       mae_nuis=d.mae_nuis.mean(), brier=d.brier.mean(),
                       purity=d.purity.mean(), capture=d.capture.mean(),
                       jaccard=d.jaccard.mean(),
                       commit=100.0 * d.commit.mean(),
                       mae_assessment=d.mae_assessment.mean(),
                       seconds=d.seconds.mean())
            for metric in ("mae_nuis", "bias", "brier", "purity", "capture"):
                diff = (d.loc[common, metric] - base.loc[common, metric]).to_numpy()
                lo, hi, p = _boot(diff, seed=13)
                row[f"d_{metric}"] = float(diff.mean())
                row[f"lo_{metric}"] = lo
                row[f"hi_{metric}"] = hi
                row[f"p_{metric}"] = p
            out.append(row)
    return pd.DataFrame(out)


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
    raw.to_csv(os.path.join(root, "results", "gate36_replications.csv"),
               index=False)
    res = summarise(raw)
    res.to_csv(os.path.join(root, "results", "gate36_summary.csv"), index=False)

    print(f"\n=== Gate 36, AIPW vs TMLE, {args.reps} reps ===")
    print(res[["kind", "estimator", "bias", "coverage", "mae_nuis", "brier",
               "purity", "capture", "commit", "mae_assessment", "seconds"]]
          .round(4).to_string(index=False))
    print("\nPaired TMLE vs AIPW:")
    for _, r in res[res.estimator == "tmle"].iterrows():
        print(f"  {r.kind:>6} dMAE={r.d_mae_nuis:+.4f} "
              f"[{r.lo_mae_nuis:+.4f},{r.hi_mae_nuis:+.4f}] p={r.p_mae_nuis:.3f} "
              f"dBrier={r.d_brier:+.4f} dPurity={r.d_purity:+.3f}")
    return raw, res


if __name__ == "__main__":
    main()
