import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, precision_recall_curve, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from app.services.ml_scorer import ALL_FEATURES, CATEGORY_FEATURES, MODEL_PATH, NUMBER_FEATURES

ML_FOLDER = Path(__file__).resolve().parent
DATA_PATH = ML_FOLDER / "data" / "claims.csv"
TEST_PATH = ML_FOLDER / "data" / "test_claims.csv"
METRICS_PATH = ML_FOLDER / "train_metrics.json"


def make_pipeline(model):
    preprocess = ColumnTransformer(
        [
            ("numbers", StandardScaler(), NUMBER_FEATURES),
            ("category", OneHotEncoder(handle_unknown="ignore"), CATEGORY_FEATURES),
        ]
    )
    return Pipeline([("preprocess", preprocess), ("model", model)])


def best_threshold(y_true, probabilities):
    precision, recall, thresholds = precision_recall_curve(y_true, probabilities)
    f1 = 2 * precision * recall / np.maximum(precision + recall, 1e-9)
    best = int(np.argmax(f1[:-1]))
    return float(thresholds[best])


def scores(y_true, probabilities, threshold):
    predicted = (probabilities >= threshold).astype(int)
    return {
        "precision": round(precision_score(y_true, predicted, zero_division=0), 3),
        "recall": round(recall_score(y_true, predicted, zero_division=0), 3),
        "f1": round(f1_score(y_true, predicted, zero_division=0), 3),
        "roc_auc": round(roc_auc_score(y_true, probabilities), 3),
    }


def train():
    data = pd.read_csv(DATA_PATH)
    X = data[ALL_FEATURES]
    y = data["is_fraud"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

    candidates = {
        "logistic_regression": LogisticRegression(class_weight="balanced", max_iter=2000),
        "random_forest": RandomForestClassifier(
            n_estimators=300, min_samples_leaf=3, class_weight="balanced", random_state=42
        ),
    }

    folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    results = {}

    for name, model in candidates.items():
        pipeline = make_pipeline(model)
        cv_probabilities = cross_val_predict(pipeline, X_train, y_train, cv=folds, method="predict_proba")[:, 1]
        threshold = best_threshold(y_train, cv_probabilities)

        pipeline.fit(X_train, y_train)
        test_probabilities = pipeline.predict_proba(X_test)[:, 1]

        results[name] = {
            "pipeline": pipeline,
            "threshold": threshold,
            "cv_roc_auc": round(roc_auc_score(y_train, cv_probabilities), 3),
            "test": scores(y_test, test_probabilities, threshold),
        }
        print(f"{name}: cv roc_auc={results[name]['cv_roc_auc']}  test={results[name]['test']}  threshold={threshold:.3f}")

    best_name = max(results, key=lambda name: results[name]["cv_roc_auc"])
    best = results[best_name]

    joblib.dump({"model": best["pipeline"], "threshold": best["threshold"], "name": best_name}, MODEL_PATH)

    test_data = X_test.copy()
    test_data["is_fraud"] = y_test
    test_data.to_csv(TEST_PATH, index=False)

    metrics = {
        name: {key: value for key, value in result.items() if key != "pipeline"}
        for name, result in results.items()
    }
    metrics["chosen_model"] = best_name
    METRICS_PATH.write_text(json.dumps(metrics, indent=2))

    print(f"Chosen model: {best_name}, saved to {MODEL_PATH}")


if __name__ == "__main__":
    train()
