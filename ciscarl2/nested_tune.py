"""Nested-refit hyperparameter tuning: nuisances refit inside every inner fold.

The naive procedure builds psi once on the whole discovery set and cross-validates
the tree on it. That lets inner-validation rows influence the nuisance models used
for the inner-training pseudo-outcomes. Here each outer fold refits the nuisances
on the outer-training rows only, cross-fits psi within them, and predicts psi for
the held-out fold from models that never saw it.

Run:  python -m ciscarl2.nested_tune
Writes: results/nested_tuning.csv
"""
from __future__ import annotations

import itertools

import numpy as np
import pandas as pd
from sklearn.model_selection import KFold, train_test_split
from sklearn.tree import DecisionTreeRegressor

from .estimators import (_fit_predict_nuisances, crossfit_nuisances,
                         truncate_weights, ipcw_outcome)
from .gate2 import pseudo_outcome
from .paths import data_path

COV = ["cd40", "cd80", "age", "wtkg", "karnof", "hemo", "homo",
       "race", "gender", "drugs", "str2", "symptom"]
HORIZON = 730.0
SEED = 2024
CAP_CEILING = 20.0


def _data():
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
    return X, A, T, E, disc, val, asm


def _leaf_means(tree, X, target):
    leaf_tr = tree.apply(X)
    means = {int(k): float(target[leaf_tr == k].mean()) for k in np.unique(leaf_tr)}
    return means


def nested_cv(X, A, T, E, disc, configs, outer_folds=5, inner_folds=5):
    mu, sd = X[disc].mean(0), X[disc].std(0)
    XD = (X[disc] - mu) / sd
    AD, TD, ED = A[disc], T[disc], E[disc]
    rows = []

    outer = list(KFold(outer_folds, shuffle=True, random_state=SEED + 7).split(XD))
    for fold, (tr, va) in enumerate(outer):
        # psi on the outer-training rows, cross-fitted within them
        mu_tr, G_tr, _, fid, fcaps, _ = crossfit_nuisances(
            XD[tr], AD[tr], TD[tr], ED[tr], HORIZON, n_splits=inner_folds,
            seed=SEED, return_folds=True)
        G_tr, cap = truncate_weights(G_tr, fid, fcaps)
        psi_tr = pseudo_outcome(AD[tr], TD[tr], HORIZON, mu_tr, G_tr)

        # psi for the held-out rows from models fitted on tr only
        mu_va, G_va = _fit_predict_nuisances(
            XD[tr], AD[tr], TD[tr], ED[tr], XD[va], HORIZON)
        G_va = np.maximum(G_va, 1.0 / min(float(cap.max()), CAP_CEILING))
        psi_va = pseudo_outcome(AD[va], TD[va], HORIZON, mu_va, G_va)

        for depth, leaf, crit in configs:
            tree = DecisionTreeRegressor(max_depth=depth, min_samples_leaf=leaf,
                                         criterion=crit, random_state=0).fit(XD[tr], psi_tr)
            means = _leaf_means(tree, XD[tr], psi_tr)
            pred = np.array([means.get(int(k), float(psi_tr.mean()))
                             for k in tree.apply(XD[va])])
            rows.append({"fold": fold, "depth": depth, "leaf": leaf, "criterion": crit,
                         "mae": float(np.mean(np.abs(pred - psi_va))),
                         "n_val": len(va)})
    return pd.DataFrame(rows)


def main():
    X, A, T, E, disc, val, asm = _data()
    configs = list(itertools.product((2, 3, 4), (40, 60, 100),
                                     ("squared_error", "absolute_error")))
    df = nested_cv(X, A, T, E, disc, configs)
    summ = (df.groupby(["depth", "leaf", "criterion"])
              .agg(nested_mae=("mae", "mean"),
                   sd=("mae", "std"), folds=("fold", "nunique"))
              .reset_index().sort_values("nested_mae"))
    summ.to_csv("results/nested_tuning.csv", index=False)
    print("Nested-refit tuning (5 outer folds; nuisances refit inside each)\n")
    print(summ.round(4).to_string(index=False))
    best = summ.iloc[0]
    print(f"\nbest: depth={int(best.depth)} leaf={int(best.leaf)} "
          f"criterion={best.criterion} nested MAE={best.nested_mae:.4f}")

    frozen = summ[(summ.depth == 3) & (summ.leaf == 60) &
                  (summ.criterion == "squared_error")]
    if len(frozen):
        print(f"frozen config (3/60/squared_error): {frozen.nested_mae.iloc[0]:.4f}")


if __name__ == "__main__":
    main()
