from datetime import date

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity

from app.auth.decorators import role_required
from app.extensions import db
from app.models import Policy, User
from app.schemas.admin import PolicyCreateRequest
from app.utils.errors import AppError
from app.utils.numbering import next_id_and_number

policies_bp = Blueprint("policies", __name__)


@policies_bp.get("")
@role_required("CUSTOMER", "ADMIN")
def list_policies():
    query = db.select(Policy).order_by(Policy.id.desc())

    if get_jwt()["role"] == "CUSTOMER":
        query = query.filter_by(user_id=int(get_jwt_identity()))

    policies = db.session.execute(query).scalars().all()
    return jsonify([policy.to_dict() for policy in policies])


@policies_bp.post("")
@role_required("ADMIN")
def create_policy():
    data = PolicyCreateRequest.model_validate(request.get_json(silent=True) or {})

    customer = db.session.get(User, data.user_id)
    if customer is None or customer.role != "CUSTOMER":
        raise AppError("VALIDATION_ERROR", "Policies can only be created for customers", 400)

    policy_id, policy_number = next_id_and_number("policies", "HLT", 5)
    policy = Policy(
        id=policy_id,
        policy_number=policy_number,
        user_id=customer.id,
        plan_name=data.plan_name,
        sum_insured=data.sum_insured,
        remaining_sum_insured=data.sum_insured,
        start_date=data.start_date,
        end_date=data.end_date,
        waiting_period_days=data.waiting_period_days,
        status="ACTIVE" if data.end_date >= date.today() else "EXPIRED",
    )
    db.session.add(policy)
    db.session.commit()

    return jsonify(policy.to_dict()), 201
