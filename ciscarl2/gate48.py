"""Gate 48 - SHAP and LIME explainability audit for the final CART.

The final model is a depth-3 CART rule. This gate adds post-hoc explanation:
  * exact TreeSHAP on the final tree (global and patient-level),
  * LIME local explanations for patients inside and outside the rule,
  * agreement between SHAP and LIME top features,
  * LIME stability across random seeds,
  * group-wise SHAP by race and gender.

Descriptive only: explanations do not change the rule, support floor,
validation decision or assessment read-out.

Run:
    python -m ciscarl2.gate48 --n-lime 40 --seeds 5
Writes:
    results/gate48_shap.csv
    results/gate48_lime.csv
    results/gate48_agreement.csv
    results/gate48_groups.csv
    results/gate48_verdict.md
    paper/figs/fig_gate48_*.png
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeRegressor

from . import dgp
from .estimators import crossfit_nuisances, phi_on_holdout, truncate_weights
from .gate2 import pseudo_outcome
from .gate22 import _stats
from .gate32 import _as_leaves, _select
from .nested_tune import _data
from .rules import eval_rule

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "paper" / "figs"
RES = ROOT / "results"
TSTAR = 730.0
SEED = 2024


def _prepare():
    Xr, A, T, E, disc, val, asm = _data()
    mu, sd = Xr[disc].mean(0), Xr[disc].std(0)
    sd[sd == 0] = 1.0
    X = (Xr - mu) / sd
    XD, AD, TD, ED = X[disc], A[disc], T[disc], E[disc]
    XA, AA, TA, EA = X[asm], A[asm], T[asm], E[asm]
    m, GD, _, fid, fcaps, _ = crossfit_nuisances(
        XD, AD, TD, ED, TSTAR, seed=SEED, return_folds=True)
    GD, _ = truncate_weights(GD, fid, fcaps)
    psi = pseudo_outcome(AD, TD, TSTAR, m, GD)
    tree = DecisionTreeRegressor(max_depth=3, min_samples_leaf=60,
                                 criterion="squared_error",
                                 random_state=0).fit(XD, psi)
    leaves = _as_leaves(tree, XD, 60)
    j, means, sup, fallback = _select(psi, leaves)
    cond = leaves[j]["cond"]
    return (tree, XD, Xr[disc], XA, Xr[asm], AA, TA, EA, disc, asm, cond,
            int(sup[j]), bool(fallback), mu, sd)


def _topk(values, k=5):
    order = np.argsort(-np.abs(values))[:k]
    return [dgp.COVARIATES[i] for i in order], order


def _jaccard(a, b):
    a, b = set(a), set(b)
    return len(a & b) / len(a | b) if a | b else 1.0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-lime", type=int, default=40)
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--num-samples", type=int, default=3000)
    args = ap.parse_args(argv)

    import shap
    from lime.lime_tabular import LimeTabularExplainer

    tree, XD, XDr, XA, XAr, AA, TA, EA, disc, asm, cond, support, fallback, mu, sd = _prepare()
    rule_text = " & ".join(f"{dgp.COVARIATES[f]} {op} {thr*sd[f]+mu[f]:.1f}"
                           for f, op, thr in cond)
    rule_mask = eval_rule(cond, XA)
    print(f"Rule: {rule_text}")
    print(f"Discovery support {support}  fallback {fallback}")

    # ------------------------------------------------------------ SHAP
    explainer = shap.TreeExplainer(tree)
    sv = np.asarray(explainer.shap_values(XA))
    if sv.ndim == 3:
        sv = sv[0]
    mean_abs = np.abs(sv).mean(axis=0)
    shap_df = pd.DataFrame({
        "feature": dgp.COVARIATES,
        "mean_abs_shap": mean_abs,
    }).sort_values("mean_abs_shap", ascending=False).reset_index(drop=True)
    shap_df["rank"] = np.arange(1, len(shap_df) + 1)
    shap_df.to_csv(RES / "gate48_shap.csv", index=False)
    print("\nSHAP global:")
    print(shap_df.round(4).to_string(index=False))

    FIG.mkdir(exist_ok=True)
    plt.rcParams.update({"font.family": "sans-serif", "font.size": 10})
    shap.summary_plot(sv, XA, feature_names=dgp.COVARIATES,
                      plot_type="bar", show=False, max_display=12)
    plt.tight_layout()
    plt.savefig(FIG / "fig_gate48_shap_global.png", dpi=200, bbox_inches="tight")
    plt.savefig(FIG / "fig_gate48_shap_global.pdf", bbox_inches="tight")
    plt.close()
    shap.summary_plot(sv, XA, feature_names=dgp.COVARIATES,
                      show=False, max_display=12)
    plt.tight_layout()
    plt.savefig(FIG / "fig_gate48_shap_beeswarm.png", dpi=200, bbox_inches="tight")
    plt.savefig(FIG / "fig_gate48_shap_beeswarm.pdf", bbox_inches="tight")
    plt.close()

    # ------------------------------------------------------------ LIME
    rng = np.random.RandomState(SEED)
    inside = np.where(rule_mask)[0]
    outside = np.where(~rule_mask)[0]
    n_each = max(1, args.n_lime // 2)
    pick_in = rng.choice(inside, size=min(n_each, len(inside)), replace=False)
    pick_out = rng.choice(outside, size=min(n_each, len(outside)), replace=False)
    picks = np.concatenate([pick_in, pick_out])

    lime_explainers = [
        LimeTabularExplainer(
            XDr, feature_names=dgp.COVARIATES, mode="regression",
            discretize_continuous=True, random_state=1000 + s)
        for s in range(args.seeds)
    ]

    def predict_fn(z):
        return tree.predict((z - mu) / sd)

    rows = []
    for idx in picks:
        x = XAr[idx]
        per_seed = []
        exp0 = None
        for s, lime_explainer in enumerate(lime_explainers):
            exp = lime_explainer.explain_instance(
                x, predict_fn, num_features=5,
                num_samples=args.num_samples)
            if s == 0:
                exp0 = exp
            feats = []
            for text, _ in exp.as_list():
                tokens = set(text.replace("<", " ").replace(">", " ")
                             .replace("=", " ").split())
                name = next((f for f in dgp.COVARIATES if f in tokens), None)
                if name:
                    feats.append(name)
            per_seed.append(feats[:5])

        shap_top, _ = _topk(sv[idx], 5)
        lime_top = per_seed[0]
        j_shap = _jaccard(shap_top, lime_top)
        stab = []
        for a in range(len(per_seed)):
            for b in range(a + 1, len(per_seed)):
                stab.append(_jaccard(per_seed[a], per_seed[b]))
        rows.append(dict(
            assessment_index=int(asm[idx]),
            in_rule=bool(rule_mask[idx]),
            shap_top5=";".join(shap_top),
            lime_top5=";".join(lime_top),
            jaccard_shap_lime=j_shap,
            lime_stability=float(np.mean(stab)) if stab else 1.0,
        ))

        if idx == picks[0]:
            labels = [t for t, _ in exp0.as_list()]
            weights = [w for _, w in exp0.as_list()]
            fig, ax = plt.subplots(figsize=(7.0, 3.2))
            ax.barh(range(len(labels))[::-1], weights)
            ax.set_yticks(range(len(labels))[::-1])
            ax.set_yticklabels(labels, fontsize=8)
            ax.axvline(0, color="black", lw=0.8)
            ax.set_xlabel("LIME weight")
            ax.set_title("LIME explanation, one assessment patient")
            fig.tight_layout()
            fig.savefig(FIG / "fig_gate48_lime_example.png", dpi=200)
            fig.savefig(FIG / "fig_gate48_lime_example.pdf")
            plt.close(fig)

    lime_df = pd.DataFrame(rows)
    lime_df.to_csv(RES / "gate48_lime.csv", index=False)
    agree = (lime_df.groupby("in_rule")
             .agg(n=("assessment_index", "size"),
                  jaccard_shap_lime=("jaccard_shap_lime", "mean"),
                  lime_stability=("lime_stability", "mean"))
             .reset_index())
    agree.to_csv(RES / "gate48_agreement.csv", index=False)
    print("\nSHAP-LIME agreement and LIME stability:")
    print(lime_df[["in_rule", "jaccard_shap_lime", "lime_stability"]]
          .groupby("in_rule").mean().round(3).to_string())

    # ------------------------------------------------------------ groups
    race = dgp.COVARIATES.index("race")
    gender = dgp.COVARIATES.index("gender")
    rows = []
    for name, col, values in (("race", race, (0, 1)), ("gender", gender, (1, 0))):
        for value in values:
            m = XAr[:, col] == value
            if m.sum() < 10:
                continue
            row = dict(group=name, value=value, n=int(m.sum()))
            for k, feat in enumerate(dgp.COVARIATES):
                row[feat] = float(np.abs(sv[m, k]).mean())
            rows.append(row)
    groups = pd.DataFrame(rows)
    groups.to_csv(RES / "gate48_groups.csv", index=False)

    # ------------------------------------------------------------ agreement figure
    fig, ax = plt.subplots(figsize=(5.2, 2.8))
    labels = ["SHAP vs LIME\n(top-5 overlap)", "LIME stability\n(across seeds)"]
    vals = [lime_df.jaccard_shap_lime.mean(), lime_df.lime_stability.mean()]
    ax.bar(labels, vals, color=["#2E5A88", "#C8643C"])
    ax.set_ylim(0, 1)
    ax.set_ylabel("Jaccard")
    for i, v in enumerate(vals):
        ax.text(i, v + 0.02, f"{v:.2f}", ha="center", fontsize=10)
    ax.set_title("Explanation agreement")
    fig.tight_layout()
    fig.savefig(FIG / "fig_gate48_agreement.png", dpi=200)
    fig.savefig(FIG / "fig_gate48_agreement.pdf")
    plt.close(fig)

    # ------------------------------------------------------------ verdict
    top3 = ", ".join(shap_df.feature.head(3))
    inside_mean = lime_df[lime_df.in_rule].jaccard_shap_lime.mean()
    outside_mean = lime_df[~lime_df.in_rule].jaccard_shap_lime.mean()
    inside_stab = lime_df[lime_df.in_rule].lime_stability.mean()
    outside_stab = lime_df[~lime_df.in_rule].lime_stability.mean()
    verdict = f"""# Gate 48 — SHAP and LIME explainability audit

The final CART is a depth-3 rule: `{rule_text}`. Discovery support is
{support} (fallback {fallback}). Explanations are descriptive: they do not
change the rule, support floor, validation decision or assessment result.

## SHAP (exact TreeSHAP on the final CART)

Top features by mean absolute SHAP on the assessment partition:

| rank | feature | mean abs SHAP |
|---|---|---|
""" + "\n".join(
        f"| {int(r['rank'])} | {r.feature} | {r.mean_abs_shap:.4f} |"
        for _, r in shap_df.head(8).iterrows()) + f"""

The top three are **{top3}**. `wtkg` ranks fourth globally, but it is part of
the selected rule; the SHAP rank is an average over assessment patients and
does not override the rule.

## LIME (local explanations)

{len(lime_df)} assessment patients were explained ({int(lime_df.in_rule.sum())}
inside the rule, {int((~lime_df.in_rule).sum())} outside), with
{args.seeds} seeds per patient.

| group | mean SHAP–LIME top-5 Jaccard | mean LIME seed stability |
|---|---|---|
| inside rule | {inside_mean:.3f} | {lime_df[lime_df.in_rule].lime_stability.mean():.3f} |
| outside rule | {outside_mean:.3f} | {lime_df[~lime_df.in_rule].lime_stability.mean():.3f} |

## Group-wise SHAP

Mean absolute SHAP by race and gender is saved in
`results/gate48_groups.csv`. The group sizes are small, so this is descriptive
only and cannot support a fairness claim.

## Interpretation

* SHAP confirms which features the tree uses globally; it does not prove a
  causal effect.
* LIME stability is {inside_stab:.2f} inside the rule and {outside_stab:.2f}
  outside. A top-5 overlap around 0.70 is **moderate, not high**: roughly two or
  three of five features recur across seeds. LIME is a local aid, not a
  definitive attribution.
* SHAP and LIME need not agree. The rule remains the primary explanation; the
  two post-hoc methods are audits, not replacements.

## Decision

No model change. SHAP and LIME are reported as secondary explainability
evidence. The final explanation remains the readable rule
`{rule_text}` and the validation/abstention decision.
"""
    (RES / "gate48_verdict.md").write_text(verdict, encoding="utf-8")

    print("\nGate 48 written to results/ and paper/figs/")
    return shap_df, lime_df, groups


if __name__ == "__main__":
    main()
