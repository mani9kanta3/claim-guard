from io import BytesIO

from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import get_jwt, get_jwt_identity

from app.auth.decorators import role_required
from app.extensions import db
from app.models import Claim, Policy
from app.schemas.claim import TransitionRequest
from app.services import claim_intake, claim_workflow
from app.services.risk_rules import names_match
from app.utils.errors import AppError
from app.utils.formatting import format_inr

claims_bp = Blueprint("claims", __name__)

PAGE_SIZE = 10


def is_customer():
    return get_jwt()["role"] == "CUSTOMER"


def current_user_id():
    return int(get_jwt_identity())


def find_claim_for_current_user(claim_id):
    claim = db.session.get(Claim, claim_id)

    if claim is None or (is_customer() and claim.policy.user_id != current_user_id()):
        raise AppError("NOT_FOUND", "Claim not found", 404)

    return claim


def compare_row(field, entered, extracted, is_match):
    return {
        "field": field,
        "entered": entered,
        "extracted": extracted,
        "match": None if extracted is None else is_match,
    }


def build_comparison(claim, extracted):
    bill_total = extracted.get("total_amount")
    claimed = float(claim.claimed_amount)

    return [
        compare_row(
            "Hospital name",
            claim.hospital.name,
            extracted.get("hospital_name"),
            bool(extracted.get("hospital_name")) and names_match(extracted["hospital_name"], claim.hospital.name),
        ),
        compare_row(
            "Admission date",
            claim.admission_date.isoformat(),
            extracted.get("admission_date"),
            extracted.get("admission_date") == claim.admission_date.isoformat(),
        ),
        compare_row(
            "Discharge date",
            claim.discharge_date.isoformat(),
            extracted.get("discharge_date"),
            extracted.get("discharge_date") == claim.discharge_date.isoformat(),
        ),
        compare_row(
            "Total amount",
            format_inr(claimed),
            format_inr(bill_total) if bill_total is not None else None,
            bill_total is not None and abs(bill_total - claimed) <= claimed * 0.10,
        ),
    ]


def bill_details(claim):
    if not claim.documents:
        return None

    document = claim.documents[0]
    details = {
        "file_name": document.file_name,
        "extraction_status": document.extraction_status,
        "uploaded_at": document.uploaded_at.isoformat(),
    }

    if document.extraction_status == "DONE":
        details["extracted"] = document.extracted_json
        details["comparison"] = build_comparison(claim, document.extracted_json)
    elif document.extracted_json:
        details["error"] = document.extracted_json.get("error")

    return details


def claim_detail(claim):
    data = claim.to_dict(include_risk=not is_customer())
    data["events"] = [event.to_dict() for event in claim.events]

    if not is_customer():
        data["flags"] = [flag.to_dict() for flag in claim.flags]
        data["bill"] = bill_details(claim)
        data["remaining_sum_insured"] = float(claim.policy.remaining_sum_insured)
        if claim.settlement:
            data["settlement_reference"] = claim.settlement.reference

    return data


@claims_bp.get("")
@role_required("CUSTOMER", "OFFICER")
def list_claims():
    status = request.args.get("status")
    risk_level = request.args.get("risk_level")
    search = request.args.get("search", "").strip()
    page = request.args.get("page", 1, type=int)

    query = db.select(Claim).join(Claim.policy)

    if is_customer():
        query = query.where(Policy.user_id == current_user_id()).order_by(Claim.submitted_at.desc())
    else:
        query = query.order_by(Claim.risk_score.desc().nulls_last(), Claim.submitted_at)

    if status:
        query = query.where(Claim.status == status)
    if risk_level and not is_customer():
        query = query.where(Claim.risk_level == risk_level)
    if search:
        query = query.where(Claim.claim_number.ilike(f"%{search}%"))

    result = db.paginate(query, page=page, per_page=PAGE_SIZE, error_out=False)

    return jsonify(
        {
            "items": [claim.to_dict(include_risk=not is_customer()) for claim in result.items],
            "page": result.page,
            "total": result.total,
            "total_pages": result.pages,
        }
    )


@claims_bp.get("/<int:claim_id>")
@role_required("CUSTOMER", "OFFICER")
def get_claim(claim_id):
    claim = find_claim_for_current_user(claim_id)
    return jsonify(claim_detail(claim))


@claims_bp.post("")
@role_required("CUSTOMER")
def submit_claim():
    claim = claim_intake.submit_claim(current_user_id(), request.form.to_dict(), request.files.get("bill"))
    return jsonify(claim_detail(claim)), 201


@claims_bp.get("/<int:claim_id>/document")
@role_required("CUSTOMER", "OFFICER")
def download_document(claim_id):
    claim = find_claim_for_current_user(claim_id)

    if not claim.documents:
        raise AppError("NOT_FOUND", "No bill uploaded for this claim", 404)

    document = claim.documents[0]
    return send_file(
        BytesIO(document.file_data),
        mimetype="application/pdf",
        download_name=document.file_name or f"{claim.claim_number}.pdf",
    )


@claims_bp.post("/<int:claim_id>/transition")
@role_required("OFFICER")
def transition_claim(claim_id):
    data = TransitionRequest.model_validate(request.get_json(silent=True) or {})
    claim = claim_workflow.transition(
        claim_id,
        current_user_id(),
        data.to_status,
        note=data.note,
        approved_amount=data.approved_amount,
    )
    return jsonify(claim_detail(claim))


@claims_bp.post("/<int:claim_id>/settle")
@role_required("OFFICER")
def settle_claim(claim_id):
    claim = claim_workflow.settle(claim_id, current_user_id())
    return jsonify(claim_detail(claim))


@claims_bp.post("/<int:claim_id>/rescore")
@role_required("OFFICER")
def rescore_claim(claim_id):
    claim = find_claim_for_current_user(claim_id)
    claim = claim_intake.rescore_claim(claim)
    return jsonify(claim_detail(claim))
