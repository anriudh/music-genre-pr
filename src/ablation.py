"""Feature group ablation: which groups of features actually separate genres?

For each classifier we run nested CV on every feature set: each group alone,
all groups together, and all groups minus one. Then the best combined model
gets a held out split (for the confusion matrix) and is refit on all clips
for the demo.

Run: python -m src.ablation
"""
import json

import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split

from src import config
from src.train import CLASSIFIERS, feature_columns, nested_cv, tuned


def feature_sets():
    groups = list(config.GROUPS)
    sets = {g: [config.GROUPS[g]] for g in groups}
    sets["All"] = list(config.GROUPS.values())
    for g in groups:
        sets[f"All minus {g}"] = [config.GROUPS[o] for o in groups if o != g]
    return sets


def run_ablation(df):
    y = df["genre"]
    rows, genre_rows = [], []
    for set_name, prefixes in feature_sets().items():
        X = df[feature_columns(df, prefixes)]
        for clf in CLASSIFIERS:
            res = nested_cv(X, y, clf)
            print(f"{set_name:22s} {clf:3s}  acc {res['acc'].mean():.3f} "
                  f"+/- {res['acc'].std():.3f}  ({X.shape[1]} features)")
            rows.append({
                "feature_set": set_name, "classifier": clf, "n_features": X.shape[1],
                "acc_mean": res["acc"].mean(), "acc_std": res["acc"].std(),
                "f1_mean": res["f1"].mean(), "f1_std": res["f1"].std(),
                "fold_acc": json.dumps([round(a, 4) for a in res["acc"]]),
                "best_params": json.dumps(res["params"]),
            })
            per_genre = f1_score(y, res["oof"], labels=config.GENRES, average=None)
            for genre, f1 in zip(config.GENRES, per_genre):
                genre_rows.append({"feature_set": set_name, "classifier": clf,
                                   "genre": genre, "f1": f1})
    return pd.DataFrame(rows), pd.DataFrame(genre_rows)


def main():
    df = pd.read_csv(config.FEATURES_CSV)
    config.RESULTS_DIR.mkdir(exist_ok=True)
    config.MODELS_DIR.mkdir(exist_ok=True)

    results, per_genre = run_ablation(df)
    results.to_csv(config.RESULTS_DIR / "ablation_results.csv", index=False)
    per_genre.to_csv(config.RESULTS_DIR / "per_genre_f1.csv", index=False)

    all_cols = feature_columns(df, config.GROUPS.values())
    X, y = df[all_cols], df["genre"]
    combined = results[results["feature_set"] == "All"]
    best_clf = combined.sort_values("acc_mean", ascending=False)["classifier"].iloc[0]
    print(f"\nBest combined classifier: {best_clf}")

    # one stratified held out split, only used for the confusion matrix
    X_tr, X_te, y_tr, y_te, f_tr, f_te = train_test_split(
        X, y, df["filename"], test_size=0.2, stratify=y, random_state=config.SEED)
    search = tuned(best_clf).fit(X_tr, y_tr)
    pred = search.predict(X_te)
    print(f"Held out accuracy: {accuracy_score(y_te, pred):.3f}")
    pd.DataFrame({"filename": f_te, "true": y_te, "pred": pred, "classifier": best_clf}) \
        .to_csv(config.RESULTS_DIR / "holdout_predictions.csv", index=False)

    # final model for the demo: tuned and refit on every clip
    final = tuned(best_clf, probability=True).fit(X, y)
    bundle = {
        "model": final.best_estimator_,
        "features": all_cols,
        "classes": list(final.best_estimator_.classes_),
        "classifier": best_clf,
        "best_params": final.best_params_,
        "cv_accuracy": float(combined.set_index("classifier").loc[best_clf, "acc_mean"]),
    }
    joblib.dump(bundle, config.BEST_MODEL, compress=3)
    print(f"Saved {config.BEST_MODEL}")

    # Random Forest importances on all features
    rf = tuned("RF").fit(X, y).best_estimator_.named_steps["clf"]
    prefix_to_group = {p: g for g, p in config.GROUPS.items()}
    imp = pd.DataFrame({"feature": all_cols, "importance": rf.feature_importances_})
    imp["group"] = imp["feature"].map(
        lambda c: next(g for p, g in prefix_to_group.items() if c.startswith(p)))
    imp.sort_values("importance", ascending=False) \
        .to_csv(config.RESULTS_DIR / "rf_importances.csv", index=False)


if __name__ == "__main__":
    main()
