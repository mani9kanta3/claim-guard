from datetime import datetime, timedelta, timezone

from app.constants import CATEGORY_AVERAGE_AMOUNT, HIGH_RISK_SCORE, MEDIUM_RISK_SCORE, RULE_POINTS
from app.extensions import db
from app.models import Claim, ClaimDocument, RiskFlag
from app.utils.formatting import format_inr


def get_bill(claim):
    return claim.documents[0] if claim.documents else None


def get_extracted_bill(claim):
    bill = get_bill(claim)
    if bill and bill.extraction_status == "DONE":
        return bill.extracted_json
    return None


def find_duplicate_bill_claim(claim):
    bill = get_bill(claim)
    if bill is None:
        return None

    query = (
        db.select(Claim)
        .join(ClaimDocument, ClaimDocument.claim_id == Claim.id)
        .where(ClaimDocument.file_sha256 == bill.file_sha256, Claim.id != claim.id)
        .limit(1)
    )
    return db.session.execute(query).scalar_one_or_none()


def count_recent_claims(claim):
    submitted_at = claim.submitted_at or datetime.now(timezone.utc)
    query = (
        db.select(db.func.count())
        .select_from(Claim)
        .where(
            Claim.policy_id == claim.policy_id,
            Claim.id != claim.id,
            Claim.submitted_at < submitted_at,
            Claim.submitted_at >= submitted_at - timedelta(days=365),
        )
    )
    return db.session.execute(query).scalar()


def bill_mismatch_percent(claim, extracted):
    if not extracted or not extracted.get("total_amount"):
        return None
    claimed = float(claim.claimed_amount)
    return abs(extracted["total_amount"] - claimed) / claimed * 100


def rule_waiting_period(claim, extracted):
    policy = claim.policy
    days = (claim.admission_date - policy.start_date).days
    if days < policy.waiting_period_days:
        return f"Admitted {days} days after policy start; waiting period is {policy.waiting_period_days} days"
    return None


def rule_duplicate_bill(claim, extracted):
    other_claim = find_duplicate_bill_claim(claim)
    if other_claim:
        return f"This bill file was already submitted in {other_claim.claim_number}"
    return None


def rule_uses_most_of_cover(claim, extracted):
    remaining = float(claim.policy.remaining_sum_insured)
    if remaining <= 0:
        return None
    used = float(claim.claimed_amount) / remaining * 100
    if used > 80:
        return f"Claim uses {used:.0f}% of the remaining cover"
    return None


def rule_unusual_amount(claim, extracted):
    average = CATEGORY_AVERAGE_AMOUNT[claim.diagnosis_category]
    amount = float(claim.claimed_amount)
    if amount > 3 * average:
        return f"{format_inr(amount)} for {claim.diagnosis_category}; category average is {format_inr(average)}"
    return None


def rule_non_network_hospital(claim, extracted):
    if not claim.hospital.is_network:
        return "Hospital is outside the network"
    return None


def rule_many_recent_claims(claim, extracted):
    earlier_claims = count_recent_claims(claim)
    if earlier_claims >= 3:
        return f"Claim number {earlier_claims + 1} on this policy in 12 months"
    return None


def rule_bill_total_mismatch(claim, extracted):
    mismatch = bill_mismatch_percent(claim, extracted)
    if mismatch is not None and mismatch > 10:
        return (
            f"Bill total {format_inr(extracted['total_amount'])} but claim says "
            f"{format_inr(float(claim.claimed_amount))}"
        )
    return None


def rule_bill_details_mismatch(claim, extracted):
    if not extracted:
        return None

    bill_admission = extracted.get("admission_date")
    if bill_admission and bill_admission != claim.admission_date.isoformat():
        return f"Bill admission date {bill_admission}, claim says {claim.admission_date.isoformat()}"

    bill_discharge = extracted.get("discharge_date")
    if bill_discharge and bill_discharge != claim.discharge_date.isoformat():
        return f"Bill discharge date {bill_discharge}, claim says {claim.discharge_date.isoformat()}"

    bill_hospital = extracted.get("hospital_name")
    if bill_hospital and not names_match(bill_hospital, claim.hospital.name):
        return f"Bill is from '{bill_hospital}', claim says '{claim.hospital.name}'"

    return None


def names_match(first, second):
    first = first.lower().strip()
    second = second.lower().strip()
    return first in second or second in first


RULES = {
    "R1": rule_waiting_period,
    "R2": rule_duplicate_bill,
    "R3": rule_uses_most_of_cover,
    "R4": rule_unusual_amount,
    "R5": rule_non_network_hospital,
    "R6": rule_many_recent_claims,
    "R7": rule_bill_total_mismatch,
    "R8": rule_bill_details_mismatch,
}


def run_rules(claim):
    extracted = get_extracted_bill(claim)
    flags = []

    for code, rule in RULES.items():
        reason = rule(claim, extracted)
        if reason:
            flags.append({"rule_code": code, "points": RULE_POINTS[code], "reason": reason})

    return flags


def risk_level_for(score):
    if score >= HIGH_RISK_SCORE:
        return "HIGH"
    if score >= MEDIUM_RISK_SCORE:
        return "MEDIUM"
    return "LOW"


def score_claim(claim):
    for old_flag in list(claim.flags):
        db.session.delete(old_flag)
    db.session.flush()

    flags = run_rules(claim)
    for flag in flags:
        db.session.add(RiskFlag(claim_id=claim.id, **flag))

    claim.risk_score = min(100, sum(flag["points"] for flag in flags))
    claim.risk_level = risk_level_for(claim.risk_score)
    db.session.flush()
    db.session.refresh(claim, ["flags"])
    return flags
