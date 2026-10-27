"""Classifiers, their small tuning grids and the nested cross validation loop.

Scaling sits inside the Pipeline, so each fold's scaler only ever sees that
fold's training data. Tuning is a GridSearchCV that runs on the training part
of each outer fold (nested CV), so reported scores are never tuned on test data.
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from src import config

CLASSIFIERS = ["SVM", "RF"]

GRIDS = {
    "SVM": {"clf__C": [1, 10, 100], "clf__gamma": ["scale", 0.01, 0.001]},
    "RF": {"clf__n_estimators": [300, 600], "clf__max_depth": [None, 20]},
}


def make_model(name, probability=False):
    if name == "SVM":
        clf = SVC(kernel="rbf", probability=probability, random_state=config.SEED)
    elif name == "RF":
        clf = RandomForestClassifier(random_state=config.SEED, n_jobs=1)
    else:
        raise ValueError(name)
    return Pipeline([("scale", StandardScaler()), ("clf", clf)])


def tuned(name, probability=False, n_splits=3):
    """A model wrapped in its grid search (inner CV)."""
    inner = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=config.SEED)
    return GridSearchCV(make_model(name, probability), GRIDS[name], cv=inner,
                        scoring="accuracy", n_jobs=-1)


def feature_columns(df, prefixes):
    return [c for c in df.columns if c.startswith(tuple(prefixes))]


def nested_cv(X, y, name, n_splits=5):
    """Stratified 5 fold outer CV with grid search inside each training fold.

    Returns per fold accuracy and macro F1, the chosen params per fold and
    the out of fold predictions (used for per genre F1).
    """
    outer = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=config.SEED)
    accs, f1s, params = [], [], []
    oof = np.empty(len(y), dtype=object)
    for train_idx, test_idx in outer.split(X, y):
        search = tuned(name)
        search.fit(X.iloc[train_idx], y.iloc[train_idx])
        pred = search.predict(X.iloc[test_idx])
        oof[test_idx] = pred
        accs.append(accuracy_score(y.iloc[test_idx], pred))
        f1s.append(f1_score(y.iloc[test_idx], pred, average="macro"))
        params.append({k.replace("clf__", ""): v for k, v in search.best_params_.items()})
    return {"acc": np.array(accs), "f1": np.array(f1s), "params": params,
            "oof": pd.Series(oof, index=y.index)}
