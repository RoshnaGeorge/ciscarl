"""Generate figures for the detailed IEEE paper from the saved result CSVs."""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(r"C:\Users\roshn\OneDrive\Desktop\Amrita\SEM 5\ML\Project")
R = ROOT / "results"
OUT = ROOT / "paper" / "figs"
OUT.mkdir(exist_ok=True)

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 8.5,
    "axes.titlesize": 9,
    "axes.labelsize": 8.5,
    "legend.fontsize": 7.5,
    "xtick.labelsize": 7.5,
    "ytick.labelsize": 7.5,
    "figure.dpi": 300,
    "savefig.bbox": "tight",
})
C = ["#2E5A88", "#C8643C", "#4E8B57", "#7A5A9E", "#B08A2E"]


def save(fig, name):
    fig.savefig(OUT / f"{name}.png")
    fig.savefig(OUT / f"{name}.pdf")
    plt.close(fig)


# ---------------------------------------------------------------- pipeline
fig, ax = plt.subplots(figsize=(7.2, 3.4))
ax.set_xlim(0, 10)
ax.set_ylim(0, 5.2)
ax.axis("off")
boxes = [
    (0.2, 4.0, 2.2, 0.8, "ACTG175\n1,054 patients"),
    (2.8, 4.0, 2.2, 0.8, "Discovery\n527"),
    (5.4, 4.0, 2.2, 0.8, "Validation\n263"),
    (8.0, 4.0, 1.8, 0.8, "Assessment\n264"),
    (2.8, 2.8, 2.2, 0.8, "Cox nuisances\n+ censoring"),
    (5.4, 2.8, 2.2, 0.8, "AIPW\npseudo-outcome"),
    (8.0, 2.8, 1.8, 0.8, "Depth-3 CART"),
    (2.8, 1.6, 2.2, 0.8, "Support floor\n200"),
    (5.4, 1.6, 2.2, 0.8, "Validation LCB\n> 0"),
    (8.0, 1.6, 1.8, 0.8, "Commit /\nabstain"),
    (2.8, 0.35, 6.6, 0.7, "Post-freeze gates 31-44: nuisance, learner, calibration, intervals, folds, fairness, TMLE, horizon"),
]
for x, y, w, h, t in boxes:
    ax.add_patch(plt.Rectangle((x, y), w, h, facecolor="#EAF0F7", edgecolor="#2E5A88", lw=0.8))
    ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=7.2)

def arrow(a, b):
    ax.annotate("", xy=b, xytext=a, arrowprops=dict(arrowstyle="->", lw=0.8, color="#333333"))
arrow((2.4, 4.4), (2.8, 4.4))
arrow((5.0, 4.4), (5.4, 4.4))
arrow((7.6, 4.4), (8.0, 4.4))
arrow((3.9, 4.0), (3.9, 3.6))
arrow((5.0, 3.2), (5.4, 3.2))
arrow((6.5, 3.2), (6.5, 2.8))
arrow((7.6, 3.2), (8.0, 3.2))
arrow((3.9, 2.8), (3.9, 2.4))
arrow((5.0, 2.0), (5.4, 2.0))
arrow((6.5, 2.0), (6.5, 2.4))
arrow((7.6, 2.0), (8.0, 2.0))
save(fig, "fig_pipeline")

# ---------------------------------------------------------------- gate31
g = pd.read_csv(R / "gate31_summary.csv")
fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.7), sharey=False)
for ax, kind in zip(axes, ["single", "two"]):
    d = g[g.kind == kind]
    x = np.arange(len(d))
    ax.bar(x, d.mae_nuis, color=C[0], width=0.6, label="MAE")
    ax.set_xticks(x)
    ax.set_xticklabels(d.model, rotation=20)
    ax.set_ylabel("patient-level MAE")
    ax.set_title(f"{kind}-region DGP")
    ax2 = ax.twinx()
    ax2.plot(x, d.brier, "o-", color=C[1], lw=1.2, ms=4, label="Brier")
    ax2.set_ylabel("Brier at 730", color=C[1])
    ax2.tick_params(axis="y", colors=C[1])
    for xi, c in zip(x, d.seconds):
        ax.text(xi, 0.002, f"{c:.0f}s", ha="center", va="bottom", fontsize=6, rotation=90, color="white")
fig.tight_layout()
save(fig, "fig_gate31_nuisance")

# ---------------------------------------------------------------- gate32
g = pd.read_csv(R / "gate32_summary.csv")
fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.9), sharey=True)
for ax, kind in zip(axes, ["single", "two"]):
    d = g[g.kind == kind]
    sizes = 20 + 90 * np.log10(d.seconds / 0.02 + 1.0)
    ax.scatter(d.capture, d.purity, s=sizes, c=C[0], alpha=0.85, edgecolor="k", lw=0.4)
    for _, r in d.iterrows():
        ax.annotate(r.learner, (r.capture, r.purity), xytext=(4, 3),
                    textcoords="offset points", fontsize=6.5)
    ax.set_xlabel("captured benefit")
    ax.set_ylabel("purity")
    ax.set_title(f"{kind}-region DGP")
    ax.grid(alpha=0.25)
fig.tight_layout()
save(fig, "fig_gate32_learners")

# ---------------------------------------------------------------- gate33
cal = pd.read_csv(R / "gate33_calibration.csv")
itv = pd.read_csv(R / "gate33_intervals.csv")
fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.7))
ax = axes[0]
for i, kind in enumerate(["single", "two"]):
    d = cal[(cal.kind == kind) & (cal.method != "none")]
    x = np.arange(len(d)) + i * 2.5
    ax.bar(x, d.d_mae, yerr=[d.d_mae - d.lo, d.hi - d.d_mae], color=C[i], width=0.7,
           capsize=2, label=kind)
    ax.set_xticks(x)
    ax.set_xticklabels(d.method, rotation=20)
ax.axhline(0, color="k", lw=0.6)
ax.set_ylabel("ΔMAE vs none")
ax.set_title("Calibration")
ax.legend(frameon=False)
ax = axes[1]
for i, kind in enumerate(["single", "two"]):
    d = itv[itv.kind == kind]
    x = np.arange(len(d)) + i * 4.5
    ax.bar(x, d.coverage, color=C[i], width=1.8, label=kind)
    for xi, w in zip(x, d.width):
        ax.text(xi, 101, f"{w:.2f}", ha="center", fontsize=6, rotation=90)
    ax.set_xticks(x)
    ax.set_xticklabels(d.method, rotation=25, fontsize=6.5)
ax.axhline(95, color="k", ls="--", lw=0.7)
ax.set_ylim(70, 108)
ax.set_ylabel("coverage (%)")
ax.set_title("Intervals (width annotated)")
ax.legend(frameon=False, ncol=2, loc="lower left")
fig.tight_layout()
save(fig, "fig_gate33_calibration_intervals")

# ---------------------------------------------------------------- gate34
g = pd.read_csv(R / "gate34_summary.csv")
fig, ax = plt.subplots(figsize=(4.5, 2.7))
for i, kind in enumerate(["single", "two"]):
    d = g[g.kind == kind]
    ax.plot(d.folds, d.mae, "o-", color=C[i], label=kind)
    ax.set_xticks([3, 5, 10])
ax.set_xlabel("cross-fitting folds")
ax.set_ylabel("MAE")
ax2 = ax.twinx()
for i, kind in enumerate(["single", "two"]):
    d = g[g.kind == kind]
    ax2.plot(d.folds, d.seconds, "s--", color=C[i], alpha=0.5, lw=0.8)
ax2.set_ylabel("seconds (dashed)")
ax.legend(frameon=False)
fig.tight_layout()
save(fig, "fig_gate34_folds")

# ---------------------------------------------------------------- gate35
g = pd.read_csv(R / "gate35_groups.csv")
fig, ax = plt.subplots(figsize=(4.8, 2.6))
y = np.arange(len(g))
ax.errorbar(g.effect, y, xerr=[g.effect - g.lo, g.hi - g.effect], fmt="o",
            color=C[0], capsize=3, ms=5)
ax.axvline(0, color="k", lw=0.7)
ax.set_yticks(y)
ax.set_yticklabels([f"{r.label} (n={r.rule_n})" for _, r in g.iterrows()])
ax.set_xlabel("rule effect (95% CI)")
ax.set_title("Group effects are underpowered")
fig.tight_layout()
save(fig, "fig_gate35_fairness")

# ---------------------------------------------------------------- horizon
g37 = pd.read_csv(R / "gate37_horizon.csv")
g42 = pd.read_csv(R / "gate42_horizon_grid.csv")
g43 = pd.read_csv(R / "gate43_horizon_inner.csv")
g44 = pd.read_csv(R / "gate44_summary.csv")
fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.8))
ax = axes[0]
ax.plot(g42.horizon, g42.val_lcb, "-", color=C[0], lw=1.2, label="Gate 42 validation LCB")
ax.plot(g43.horizon, g43.inner_lcb, "--", color=C[1], lw=1.0, label="Gate 43 inner LCB")
for h, lab in [(730, "730"), (845, "845"), (965, "965")]:
    ax.axvline(h, color="#888888", lw=0.6, ls=":")
    ax.text(h, ax.get_ylim()[1] * 0.95, lab, fontsize=6, rotation=90, va="top")
ax.set_xlabel("horizon (days)")
ax.set_ylabel("lower confidence bound")
ax.legend(frameon=False, fontsize=6.5)
ax.set_title("Single-split criteria disagree")
ax = axes[1]
x = np.arange(len(g44))
ax.bar(x, g44.mean_lcb, yerr=g44.sd_lcb, color=C[0], width=0.55, capsize=3)
ax.set_xticks(x)
ax.set_xticklabels([str(int(h)) for h in g44.horizon])
ax.set_xlabel("horizon (days)")
ax.set_ylabel("mean validation LCB")
ax.set_title("20-split stability")
fig.tight_layout()
save(fig, "fig_gate37_44_horizon")

# ---------------------------------------------------------------- gate36
g = pd.read_csv(R / "gate36_summary.csv")
fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.6))
for ax, metric, ylab in [(axes[0], "mae_nuis", "MAE"), (axes[1], "brier", "Brier")]:
    for i, kind in enumerate(["single", "two"]):
        d = g[g.kind == kind]
        x = np.arange(len(d)) + i * 2.5
        ax.bar(x, d[metric], color=C[i], width=0.7, label=kind)
        ax.set_xticks(x)
        ax.set_xticklabels(d.estimator)
    ax.set_ylabel(ylab)
    ax.set_title(ylab)
    ax.legend(frameon=False)
fig.tight_layout()
save(fig, "fig_gate36_tmle")

# ---------------------------------------------------------------- gate39
g = pd.read_csv(R / "gate39_summary.csv")
fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.4), sharey=False)
for ax, metric, title in zip(axes, ["mae_nuis", "purity", "capture"],
                             ["MAE", "purity", "capture"]):
    for i, kind in enumerate(["single", "two"]):
        d = g[g.kind == kind]
        x = np.arange(len(d)) + i * 3.2
        ax.bar(x, d[metric], color=C[i], width=0.8, label=kind)
        ax.set_xticks(x)
        ax.set_xticklabels(d.estimator, rotation=20, fontsize=6.5)
    ax.set_title(title)
    if metric == "mae_nuis":
        ax.legend(frameon=False, fontsize=6.5)
fig.tight_layout()
save(fig, "fig_gate39_stacking")

# ---------------------------------------------------------------- gate40
p = pd.read_csv(R / "gate40_alpha_path.csv")
p["rank"] = p.groupby(["kind", "rep"]).alpha.rank(ascending=False, method="first")
agg = p.groupby(["kind", "rank"]).agg(mae=("mae", "mean"), purity=("purity", "mean"),
                                      capture=("capture", "mean")).reset_index()
fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.6))
for ax, kind in zip(axes, ["single", "two"]):
    d = agg[agg.kind == kind]
    ax.plot(d["rank"], d.mae, "o-", color=C[0], ms=3, label="MAE")
    ax.plot(d["rank"], d.purity, "s--", color=C[1], ms=3, label="purity")
    ax.plot(d["rank"], d.capture, "^:", color=C[2], ms=3, label="capture")
    ax.set_xlabel("alpha rank (1 = most regularised)")
    ax.set_title(f"{kind}-region")
    ax.legend(frameon=False, fontsize=6.5)
fig.tight_layout()
save(fig, "fig_gate40_scre_path")

# ---------------------------------------------------------------- gate41
g = pd.read_csv(R / "gate41_summary.csv")
fig, ax = plt.subplots(figsize=(4.8, 2.6))
for i, kind in enumerate(["single", "two"]):
    d = g[g.kind == kind]
    x = np.arange(len(d)) + i * 3.5
    ax.bar(x, d.coverage, color=C[i], width=0.9, label=kind)
    for xi, w in zip(x, d.width):
        ax.text(xi, 101, f"{w:.2f}", ha="center", fontsize=6, rotation=90)
    ax.set_xticks(x)
    ax.set_xticklabels(d.method, rotation=20, fontsize=6.5)
ax.axhline(95, color="k", ls="--", lw=0.7)
ax.set_ylim(80, 108)
ax.set_ylabel("coverage (%)")
ax.set_title("Selection-aware intervals (width annotated)")
ax.legend(frameon=False)
fig.tight_layout()
save(fig, "fig_gate41_intervals")

# ---------------------------------------------------------------- gate38
g = pd.read_csv(R / "gate38_features.csv")
fig, ax = plt.subplots(figsize=(4.5, 2.5))
x = np.arange(len(g))
ax.bar(x, g.val_se, color=C[0], width=0.6)
ax.set_xticks(x)
ax.set_xticklabels(g.method)
ax.set_ylabel("validation SE")
ax2 = ax.twinx()
ax2.plot(x, g.support, "o-", color=C[1])
ax2.set_ylabel("support", color=C[1])
ax2.tick_params(axis="y", colors=C[1])
ax.set_title("Feature selection")
fig.tight_layout()
save(fig, "fig_gate38_features")

print("figures written to", OUT)
