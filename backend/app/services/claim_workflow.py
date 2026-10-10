from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import Claim, ClaimEvent, Policy, Settlement
from app.utils.errors import AppError
from app.utils.numbering import next_id_and_number

ALLOWED = {
    ("UNDER_REVIEW", "APPROVED"),
    ("UNDER_REVIEW", "REJECTED"),
    ("UNDER_REVIEW", "INVESTIGATION"),
    ("INVESTIGATION", "UNDER_REVIEW"),
    ("INVESTIGATION", "REJECTED"),
    ("APPROVED", "SETTLED"),
}

NOTE_REQUIRED = {"REJECTED", "INVESTIGATION"}


def lock_claim(claim_id):
    query = (
        db.select(Claim)
        .where(Claim.id == claim_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    claim = db.session.execute(query).scalar_one_or_none()
    if claim is None:
        raise AppError("NOT_FOUND", "Claim not found", 404)
    return claim


def lock_policy(policy_id):
    query = (
        db.select(Policy)
        .where(Policy.id == policy_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    return db.session.execute(query).scalar_one()


def check_not_own_claim(claim, officer_id):
    if claim.policy.user_id == officer_id:
        raise AppError("FORBIDDEN", "You cannot decide a claim on your own policy", 403)


def add_event(claim, to_status, officer_id, note):
    db.session.add(
        ClaimEvent(
            claim_id=claim.id,
            from_status=claim.status,
            to_status=to_status,
            actor_id=officer_id,
            note=note,
        )
    )


def transition(claim_id, officer_id, to_status, note=None, approved_amount=None):
    claim = lock_claim(claim_id)

    if (claim.status, to_status) not in ALLOWED or to_status == "SETTLED":
        raise AppError("INVALID_TRANSITION", f"Claim is {claim.status}, cannot move to {to_status}", 409)

    check_not_own_claim(claim, officer_id)

    note = (note or "").strip() or None
    if (to_status in NOTE_REQUIRED or claim.status == "INVESTIGATION") and not note:
        raise AppError("VALIDATION_ERROR", "A note is required for this action", 400)

    if to_status == "APPROVED":
        if approved_amount is None:
            raise AppError("VALIDATION_ERROR", "Approved amount is required", 400)
        if approved_amount > claim.claimed_amount:
            raise AppError("VALIDATION_ERROR", "Approved amount cannot be more than the claimed amount", 400)
        if approved_amount > claim.policy.remaining_sum_insured:
            raise AppError("VALIDATION_ERROR", "Approved amount is more than the remaining sum insured", 400)
        claim.approved_amount = approved_amount

    if to_status in ("APPROVED", "REJECTED"):
        claim.decided_at = datetime.now(timezone.utc)
        claim.decided_by = officer_id

    add_event(claim, to_status, officer_id, note)
    claim.status = to_status
    db.session.commit()
    return claim


def settle(claim_id, officer_id):
    try:
        claim = lock_claim(claim_id)

        if claim.status != "APPROVED":
            raise AppError("INVALID_TRANSITION", f"Claim is {claim.status}, it cannot be settled", 409)

        check_not_own_claim(claim, officer_id)

        policy = lock_policy(claim.policy_id)
        if policy.remaining_sum_insured < claim.approved_amount:
            raise AppError("INSUFFICIENT_COVER", "Remaining sum insured is not enough to settle this claim", 409)

        settlement_id, reference = next_id_and_number("settlements", "STL", 6)
        db.session.add(
            Settlement(
                id=settlement_id,
                claim_id=claim.id,
                amount=claim.approved_amount,
                reference=reference,
                settled_by=officer_id,
            )
        )
        policy.remaining_sum_insured = policy.remaining_sum_insured - claim.approved_amount

        add_event(claim, "SETTLED", officer_id, f"Settlement {reference}")
        claim.status = "SETTLED"
        db.session.commit()
        return claim

    except AppError:
        db.session.rollback()
        raise
    except IntegrityError:
        db.session.rollback()
        raise AppError("ALREADY_SETTLED", "This claim has already been settled", 409)
