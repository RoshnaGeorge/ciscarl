"""Gate 45 - broad CART hyperparameter tuning with nested refitting.

Extends Gate 18 from 18 configurations to a full grid over depth, minimum leaf
size, split criterion and cost-complexity pruning. Nuisances are refitted inside
every outer fold, so the inner validation rows never influence the
pseudo-outcome used to score a configuration.

Run:
    python -m ciscarl2.gate45
Writes:
    results/gate45_tuning.csv
"""
from __future__ import annotations

import itertools
import os

import pandas as pd

from .nested_tune import _data, nested_cv

DEPTHS = (2, 3, 4, 5, 6)
LEAVES = (20, 30, 40, 60, 80, 100)
CRITERIA = ("squared_error", "absolute_error", "friedman_mse")
ALPHAS = (0.0, 0.0005, 0.001, 0.002, 0.005, 0.01)


def main(argv=None):
    X, A, T, E, disc, val, asm = _data()
    configs = list(itertools.product(DEPTHS, LEAVES, CRITERIA, ALPHAS))
    print(f"Gate 45: {len(configs)} configurations x 5 outer folds "
          f"(nuisances refitted inside each fold)", flush=True)

    df = nested_cv(X, A, T, E, disc, configs)
    summ = (df.groupby(["depth", "leaf", "criterion", "ccp_alpha"])
              .agg(nested_mae=("mae", "mean"),
                   sd=("mae", "std"),
                   folds=("fold", "nunique"))
              .reset_index()
              .sort_values("nested_mae")
              .reset_index(drop=True))
    summ["rank"] = summ.index + 1

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    summ.to_csv(os.path.join(root, "results", "gate45_tuning.csv"), index=False)

    best = summ.iloc[0]
    frozen = summ[(summ.depth == 3) & (summ.leaf == 60) &
                  (summ.criterion == "squared_error") &
                  (summ.ccp_alpha == 0.0)]
    print("\nTop 12 configurations (nested MAE, lower is better):")
    print(summ.head(12).round(5).to_string(index=False))
    print(f"\nBest: depth={int(best.depth)} leaf={int(best.leaf)} "
          f"criterion={best.criterion} alpha={best.ccp_alpha:g} "
          f"nested MAE={best.nested_mae:.5f} (sd {best.sd:.5f})")
    if len(frozen):
        f = frozen.iloc[0]
        print(f"Frozen 3/60/squared/0: nested MAE={f.nested_mae:.5f} "
              f"(rank {int(f['rank'])} of {len(summ)})")
    return summ


if __name__ == "__main__":
    main()
