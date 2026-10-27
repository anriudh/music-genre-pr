"""All figures for the report, saved as 300 dpi PNGs in figures/.

Run: python -m src.plots (after python -m src.ablation)
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import confusion_matrix

from src import config
from src.ablation import feature_sets

plt.rcParams.update({
    "font.size": 12, "axes.titlesize": 15, "axes.labelsize": 13,
    "xtick.labelsize": 11, "ytick.labelsize": 11, "legend.fontsize": 11,
})
COLORS = {"SVM": "#2f6db5", "RF": "#e08a2c"}
SET_ORDER = list(feature_sets())


def save(fig, name):
    config.FIGURES_DIR.mkdir(exist_ok=True)
    fig.savefig(config.FIGURES_DIR / name, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("saved", name)


def best_classifier(results):
    combined = results[results["feature_set"] == "All"]
    return combined.sort_values("acc_mean", ascending=False)["classifier"].iloc[0]


def plot_ablation_accuracy(results):
    fig, ax = plt.subplots(figsize=(13, 6))
    x = np.arange(len(SET_ORDER))
    width = 0.38
    for i, clf in enumerate(["SVM", "RF"]):
        r = results[results["classifier"] == clf].set_index("feature_set").loc[SET_ORDER]
        pos = x + (i - 0.5) * width
        ax.bar(pos, r["acc_mean"] * 100, width, yerr=r["acc_std"] * 100, capsize=4,
               color=COLORS[clf], label=clf, edgecolor="white")
        for p, v, sd in zip(pos, r["acc_mean"] * 100, r["acc_std"] * 100):
            ax.text(p, v + sd + 1, f"{v:.0f}", ha="center", va="bottom", fontsize=10)
    ax.axhline(10, color="grey", ls="--", lw=1, label="Chance (10%)")
    ax.axvline(3.5, color="lightgrey", lw=1)
    ax.axvline(4.5, color="lightgrey", lw=1)
    labels = [s.replace("All minus ", "All minus\n") for s in SET_ORDER]
    ax.set_xticks(x, labels)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Accuracy (%)")
    ax.set_title("Genre accuracy by feature set (stratified 5 fold CV, mean and std)")
    ax.legend(loc="upper left")
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "ablation_accuracy.png")


def plot_per_genre_heatmap(per_genre, clf):
    data = per_genre[per_genre["classifier"] == clf] \
        .pivot(index="feature_set", columns="genre", values="f1") \
        .loc[SET_ORDER, config.GENRES]
    fig, ax = plt.subplots(figsize=(13, 6.5))
    sns.heatmap(data, annot=True, fmt=".2f", cmap="YlGnBu", vmin=0, vmax=1,
                linewidths=0.5, cbar_kws={"label": "F1 score"}, ax=ax,
                annot_kws={"fontsize": 10})
    ax.axhline(4, color="black", lw=2)
    ax.axhline(5, color="black", lw=2)
    ax.set_xlabel("Genre")
    ax.set_ylabel("Feature set")
    ax.set_title(f"Per genre F1 by feature set ({clf}, out of fold predictions)")
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    plt.setp(ax.get_yticklabels(), rotation=0)
    save(fig, "per_genre_f1_heatmap.png")


def plot_rf_importance(imp):
    order = list(config.GROUPS)
    summed = imp.groupby("group")["importance"].sum().loc[order]
    counts = imp.groupby("group").size().loc[order]
    fig, ax = plt.subplots(figsize=(9, 5.5))
    bars = ax.bar([f"{g}\n({counts[g]} features)" for g in order], summed * 100,
                  color=["#2f6db5", "#4fa36c", "#e08a2c", "#a05ab5"])
    for b, g in zip(bars, order):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.8,
                f"{summed[g] * 100:.1f}%\n({summed[g] / counts[g] * 100:.2f}% per feature)",
                ha="center", va="bottom", fontsize=10)
    ax.set_ylim(0, summed.max() * 100 * 1.25)
    ax.set_ylabel("Summed importance (%)")
    ax.set_title("Random Forest feature importance summed per group")
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "rf_importance_by_group.png")


def plot_confusion(holdout):
    clf = holdout["classifier"].iloc[0]
    cm = confusion_matrix(holdout["true"], holdout["pred"], labels=config.GENRES)
    acc = (holdout["true"] == holdout["pred"]).mean()
    fig, ax = plt.subplots(figsize=(9, 7.5))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", cbar=False,
                xticklabels=config.GENRES, yticklabels=config.GENRES, ax=ax,
                linewidths=0.5, annot_kws={"fontsize": 11})
    ax.set_xlabel("Predicted genre")
    ax.set_ylabel("True genre")
    ax.set_title(f"Confusion matrix, {clf} on all features\n"
                 f"(20% held out split, {len(holdout)} clips, accuracy {acc:.1%})")
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    plt.setp(ax.get_yticklabels(), rotation=0)
    save(fig, "confusion_matrix.png")


def main():
    results = pd.read_csv(config.RESULTS_DIR / "ablation_results.csv")
    per_genre = pd.read_csv(config.RESULTS_DIR / "per_genre_f1.csv")
    imp = pd.read_csv(config.RESULTS_DIR / "rf_importances.csv")
    holdout = pd.read_csv(config.RESULTS_DIR / "holdout_predictions.csv")

    plot_ablation_accuracy(results)
    plot_per_genre_heatmap(per_genre, best_classifier(results))
    plot_rf_importance(imp)
    plot_confusion(holdout)


if __name__ == "__main__":
    main()
