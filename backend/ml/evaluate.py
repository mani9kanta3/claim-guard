import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score

from app.constants import HIGH_RISK_SCORE, RULE_POINTS
from app.services.ml_scorer import ALL_FEATURES, MODEL_PATH

ML_FOLDER = Path(__file__).resolve().parent
TEST_PATH = ML_FOLDER / "data" / "test_claims.csv"
REPORT_PATH = ML_FOLDER / "eval_report.json"


def rule_score(row):
    score = 0
    if row["days_since_policy_start"] < 30:
        score += RULE_POINTS["R1"]
    if row["duplicate_bill"] == 1:
        score += RULE_POINTS["R2"]
    if row["amount_to_sum_insured"] > 0.8:
        score += RULE_POINTS["R3"]
    if row["amount_to_category_average"] > 3:
        score += RULE_POINTS["R4"]
    if row["is_network"] == 0:
        score += RULE_POINTS["R5"]
    if row["claims_last_12_months"] >= 3:
        score += RULE_POINTS["R6"]
    if row["bill_mismatch_percent"] > 10:
        score += RULE_POINTS["R7"]
    return min(100, score)


def metrics(y_true, predicted, ranking_score):
    return {
        "precision": round(precision_score(y_true, predicted, zero_division=0), 3),
        "recall": round(recall_score(y_true, predicted, zero_division=0), 3),
        "f1": round(f1_score(y_true, predicted, zero_division=0), 3),
        "roc_auc": round(roc_auc_score(y_true, ranking_score), 3),
    }


def evaluate():
    test = pd.read_csv(TEST_PATH)
    saved = joblib.load(MODEL_PATH)
    y_true = test["is_fraud"]

    rule_scores = test.apply(rule_score, axis=1)
    rules_flag = (rule_scores >= HIGH_RISK_SCORE).astype(int)

    probabilities = saved["model"].predict_proba(test[ALL_FEATURES])[:, 1]
    ml_flag = (probabilities >= saved["threshold"]).astype(int)

    combined_flag = np.maximum(rules_flag, ml_flag)
    combined_score = np.maximum(rule_scores / 100, probabilities)

    report = {
        "test_claims": int(len(test)),
        "fraud_claims": int(y_true.sum()),
        "model": saved["name"],
        "ml_threshold": round(saved["threshold"], 3),
        "rules_only": metrics(y_true, rules_flag, rule_scores),
        "ml_only": metrics(y_true, ml_flag, probabilities),
        "rules_or_ml": metrics(y_true, combined_flag, combined_score),
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2))

    print(f"Test set: {report['test_claims']} claims, {report['fraud_claims']} fraud")
    print(f"{'':<14}{'precision':>10}{'recall':>8}{'f1':>7}{'roc_auc':>9}")
    for name in ["rules_only", "ml_only", "rules_or_ml"]:
        row = report[name]
        print(f"{name:<14}{row['precision']:>10}{row['recall']:>8}{row['f1']:>7}{row['roc_auc']:>9}")
    print(f"Saved report to {REPORT_PATH}")


if __name__ == "__main__":
    evaluate()
