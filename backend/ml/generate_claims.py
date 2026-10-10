import random
from pathlib import Path

import pandas as pd

from app.constants import CATEGORY_AMOUNT_RANGES, CATEGORY_AVERAGE_AMOUNT

random.seed(7)

DATA_PATH = Path(__file__).resolve().parent / "data" / "claims.csv"
TOTAL_CLAIMS = 3000
FRAUD_SHARE = 0.12
LABEL_NOISE = 0.06
SUM_INSURED_OPTIONS = [300000, 500000, 1000000]
FRAUD_PATTERNS = ["early", "inflated", "duplicate", "repeat", "mismatch", "non_network"]


def honest_claim():
    category = random.choice(list(CATEGORY_AMOUNT_RANGES))
    low, high = CATEGORY_AMOUNT_RANGES[category]
    amount = random.uniform(low, high)
    if random.random() < 0.04:
        amount *= random.uniform(2.5, 3.5)

    days_since_start = random.randint(31, 700)
    if random.random() < 0.06:
        days_since_start = random.randint(0, 30)

    mismatch = abs(random.gauss(0, 3))
    roll = random.random()
    if roll < 0.06:
        mismatch = random.uniform(8, 20)
    elif roll < 0.16:
        mismatch = 0.0

    return {
        "category": category,
        "amount": amount,
        "days_since_policy_start": days_since_start,
        "length_of_stay": random.randint(1, 7),
        "is_network": int(random.random() < 0.8),
        "claims_last_12_months": min(6, int(random.expovariate(1.6))),
        "duplicate_bill": int(random.random() < 0.005),
        "bill_mismatch_percent": mismatch,
    }


def fraud_claim():
    claim = honest_claim()

    if random.random() < 0.15:
        return claim

    for pattern in random.sample(FRAUD_PATTERNS, random.randint(1, 3)):
        if pattern == "early":
            claim["days_since_policy_start"] = random.randint(2, 29)
        elif pattern == "inflated":
            claim["amount"] = CATEGORY_AVERAGE_AMOUNT[claim["category"]] * random.uniform(2.8, 4.5)
        elif pattern == "duplicate":
            claim["duplicate_bill"] = 1
        elif pattern == "repeat":
            claim["claims_last_12_months"] = random.randint(3, 6)
        elif pattern == "mismatch":
            claim["bill_mismatch_percent"] = random.uniform(15, 60)
        elif pattern == "non_network":
            claim["is_network"] = 0
            claim["length_of_stay"] = random.randint(4, 10)

    return claim


def to_row(claim, is_fraud):
    sum_insured = random.choice(SUM_INSURED_OPTIONS)
    amount = min(claim["amount"], sum_insured)

    if random.random() < LABEL_NOISE:
        is_fraud = not is_fraud

    return {
        "days_since_policy_start": claim["days_since_policy_start"],
        "amount_to_sum_insured": round(amount / sum_insured, 4),
        "amount_to_category_average": round(amount / CATEGORY_AVERAGE_AMOUNT[claim["category"]], 4),
        "length_of_stay": claim["length_of_stay"],
        "is_network": claim["is_network"],
        "claims_last_12_months": claim["claims_last_12_months"],
        "duplicate_bill": claim["duplicate_bill"],
        "bill_mismatch_percent": round(claim["bill_mismatch_percent"], 2),
        "diagnosis_category": claim["category"],
        "is_fraud": int(is_fraud),
    }


def generate():
    rows = []
    for _ in range(TOTAL_CLAIMS):
        is_fraud = random.random() < FRAUD_SHARE
        claim = fraud_claim() if is_fraud else honest_claim()
        rows.append(to_row(claim, is_fraud))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    data = generate()
    DATA_PATH.parent.mkdir(exist_ok=True)
    data.to_csv(DATA_PATH, index=False)
    print(f"Saved {len(data)} claims to {DATA_PATH}")
    print(f"Fraud share: {data['is_fraud'].mean():.1%}")
