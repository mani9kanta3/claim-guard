from pathlib import Path

import joblib
import pandas as pd

from app.constants import CATEGORY_AVERAGE_AMOUNT
from app.services.risk_rules import (
    bill_mismatch_percent,
    count_recent_claims,
    find_duplicate_bill_claim,
    get_extracted_bill,
)

MODEL_PATH = Path(__file__).resolve().parents[2] / "ml" / "model.joblib"

NUMBER_FEATURES = [
    "days_since_policy_start",
    "amount_to_sum_insured",
    "amount_to_category_average",
    "length_of_stay",
    "is_network",
    "claims_last_12_months",
    "duplicate_bill",
    "bill_mismatch_percent",
]
CATEGORY_FEATURES = ["diagnosis_category"]
ALL_FEATURES = NUMBER_FEATURES + CATEGORY_FEATURES

_saved_model = None


def load_model():
    global _saved_model
    if _saved_model is None and MODEL_PATH.exists():
        _saved_model = joblib.load(MODEL_PATH)
    return _saved_model


def is_model_loaded():
    return load_model() is not None


def build_features(claim):
    amount = float(claim.claimed_amount)
    mismatch = bill_mismatch_percent(claim, get_extracted_bill(claim))

    return {
        "days_since_policy_start": (claim.admission_date - claim.policy.start_date).days,
        "amount_to_sum_insured": amount / float(claim.policy.sum_insured),
        "amount_to_category_average": amount / CATEGORY_AVERAGE_AMOUNT[claim.diagnosis_category],
        "length_of_stay": (claim.discharge_date - claim.admission_date).days,
        "is_network": int(claim.hospital.is_network),
        "claims_last_12_months": count_recent_claims(claim),
        "duplicate_bill": int(find_duplicate_bill_claim(claim) is not None),
        "bill_mismatch_percent": mismatch or 0.0,
        "diagnosis_category": claim.diagnosis_category,
    }


def predict_fraud_probability(claim):
    saved = load_model()
    if saved is None:
        return None

    features = pd.DataFrame([build_features(claim)], columns=ALL_FEATURES)
    probability = saved["model"].predict_proba(features)[0][1]
    return round(float(probability), 3)
