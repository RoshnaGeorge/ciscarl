# Gate 45 — broad CART hyperparameter tuning (nested refit)

Question: does a wider CART grid beat the frozen depth-3 / leaf-60 / squared-error
tree when the nuisance models are refitted inside every fold?

Grid: depth 2–6 × minimum leaf 20, 30, 40, 60, 80, 100 × criterion
squared_error, absolute_error, friedman_mse × ccp_alpha 0, 0.0005, 0.001,
0.002, 0.005, 0.01 = **540 configurations**, 5 outer folds, 5 inner folds,
ACTG175 discovery partition.

## Result

| configuration | nested MAE | rank |
|---|---|---|
| depth 5 / leaf 30 / friedman_mse or squared_error / α 0–0.002 | **0.85982** | 1 |
| depth 4 / leaf 30 / squared_error / α 0.0005–0.002 | 0.86255 | 11 |
| **frozen depth 3 / leaf 60 / squared_error / α 0** | **0.86379** | **54 of 540** |

The best configuration improves nested MAE by only **0.0040** (0.85982 vs
0.86379) and needs five conditions. The frozen tree is 54th of 540, inside the
same narrow band.

## Decision

**Not adopted on this evidence.** Nested MAE measures how well the tree predicts
the pseudo-outcome, not whether it finds a better subgroup. Gate 47 therefore
tests the same grid on simulated subgroup performance; a configuration that
wins on prediction error but loses purity or support is not an improvement.

## Limitation

One dataset (ACTG175 discovery), one split seed, and one tuning objective.
`friedman_mse` is aliased to `squared_error` in current scikit-learn, which is
why several rows tie exactly.
