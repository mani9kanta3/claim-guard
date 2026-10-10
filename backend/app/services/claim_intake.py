import hashlib
from datetime import datetime, timezone

from app.constants import MAX_FILE_SIZE
from app.extensions import db
from app.models import Claim, ClaimDocument, ClaimEvent, Hospital, Policy
from app.schemas.claim import ClaimSubmitRequest
from app.services.extraction import run_extraction
from app.services.ml_scorer import predict_fraud_probability
from app.services.risk_rules import score_claim
from app.utils.errors import AppError
from app.utils.formatting import format_inr
from app.utils.numbering import next_id_and_number


def read_pdf_upload(bill_file):
    if bill_file is None or bill_file.filename == "":
        raise AppError("VALIDATION_ERROR", "Please upload the hospital bill (PDF)", 400)

    file_bytes = bill_file.read()

    if len(file_bytes) > MAX_FILE_SIZE:
        raise AppError("FILE_TOO_LARGE", "File is too large. Maximum size is 2 MB", 413)
    if not file_bytes.startswith(b"%PDF"):
        raise AppError("VALIDATION_ERROR", "Only PDF files are allowed", 400)

    return file_bytes


def hard_validation_problem(claim, policy):
    if policy.status == "CANCELLED":
        return "Policy is cancelled"
    if not (policy.start_date <= claim.admission_date <= policy.end_date):
        return "Policy was not active on the admission date"
    if claim.claimed_amount > policy.remaining_sum_insured:
        return (
            f"Claimed amount is more than the remaining sum insured "
            f"({format_inr(float(policy.remaining_sum_insured))})"
        )
    return None


def add_event(claim, from_status, to_status, actor_id=None, note=None):
    db.session.add(
        ClaimEvent(claim_id=claim.id, from_status=from_status, to_status=to_status, actor_id=actor_id, note=note)
    )


def submit_claim(user_id, form, bill_file):
    data = ClaimSubmitRequest.model_validate(form)
    file_bytes = read_pdf_upload(bill_file)

    policy = db.session.get(Policy, data.policy_id)
    if policy is None or policy.user_id != user_id:
        raise AppError("NOT_FOUND", "Policy not found", 404)

    hospital = db.session.get(Hospital, data.hospital_id)
    if hospital is None:
        raise AppError("NOT_FOUND", "Hospital not found", 404)

    claim_id, claim_number = next_id_and_number("claims", "CLM", 6)
    claim = Claim(
        id=claim_id,
        claim_number=claim_number,
        policy_id=policy.id,
        hospital_id=hospital.id,
        admission_date=data.admission_date,
        discharge_date=data.discharge_date,
        diagnosis_category=data.diagnosis_category,
        claimed_amount=data.claimed_amount,
        status="SUBMITTED",
    )
    db.session.add(claim)
    db.session.flush()
    add_event(claim, None, "SUBMITTED", actor_id=user_id)

    document = ClaimDocument(
        claim_id=claim.id,
        doc_type="HOSPITAL_BILL",
        file_name=bill_file.filename[:200],
        file_data=file_bytes,
        file_sha256=hashlib.sha256(file_bytes).hexdigest(),
    )
    db.session.add(document)
    db.session.flush()

    problem = hard_validation_problem(claim, policy)
    if problem:
        claim.status = "REJECTED"
        claim.decided_at = datetime.now(timezone.utc)
        add_event(claim, "SUBMITTED", "REJECTED", note=problem)
        db.session.commit()
        return claim

    run_extraction(document)
    db.session.flush()
    db.session.refresh(claim, ["documents"])

    score_claim(claim)
    claim.ml_fraud_probability = predict_fraud_probability(claim)

    claim.status = "UNDER_REVIEW"
    add_event(claim, "SUBMITTED", "UNDER_REVIEW", note=f"Automatic checks done, risk {claim.risk_level}")
    db.session.commit()
    return claim


def rescore_claim(claim):
    if claim.status not in ("UNDER_REVIEW", "INVESTIGATION"):
        raise AppError("INVALID_TRANSITION", f"Claim is {claim.status}, it cannot be rescored", 409)

    if claim.documents:
        run_extraction(claim.documents[0])
        db.session.flush()

    score_claim(claim)
    claim.ml_fraud_probability = predict_fraud_probability(claim)
    db.session.commit()
    return claim
