from datetime import date

import pytest
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import Claim, ClaimDocument, ClaimEvent, Policy, RiskFlag, Settlement
from tests.factories import make_claim_with_parents, make_policy, make_user


def test_full_claim_can_be_saved(app):
    officer = make_user(email="officer@test.com", role="OFFICER")
    claim = make_claim_with_parents()

    db.session.add_all(
        [
            ClaimDocument(
                claim_id=claim.id,
                doc_type="HOSPITAL_BILL",
                file_name="bill.pdf",
                file_data=b"%PDF-1.4 test",
                file_sha256="a" * 64,
                extracted_json={"total_amount": 40000},
            ),
            RiskFlag(claim_id=claim.id, rule_code="R5", points=10, reason="Hospital is outside the network"),
            ClaimEvent(claim_id=claim.id, from_status=None, to_status="SUBMITTED"),
            Settlement(claim_id=claim.id, amount=40000, reference="STL-2026-000001", settled_by=officer.id),
        ]
    )
    db.session.commit()

    saved = db.session.get(Claim, claim.id)
    assert saved.status == "SUBMITTED"
    assert saved.policy.user.email == "customer@test.com"
    assert saved.documents[0].extracted_json["total_amount"] == 40000
    assert saved.flags[0].rule_code == "R5"
    assert saved.settlement.reference == "STL-2026-000001"


def test_unknown_role_is_rejected(app):
    with pytest.raises(IntegrityError):
        make_user(role="HACKER")


def test_uppercase_email_is_rejected(app):
    with pytest.raises(IntegrityError):
        make_user(email="Customer@Test.com")


def test_negative_claim_amount_is_rejected(app):
    with pytest.raises(IntegrityError):
        make_claim_with_parents(claimed_amount=-100)


def test_discharge_before_admission_is_rejected(app):
    with pytest.raises(IntegrityError):
        make_claim_with_parents(admission_date=date(2026, 3, 5), discharge_date=date(2026, 3, 1))


def test_unknown_status_is_rejected(app):
    with pytest.raises(IntegrityError):
        make_claim_with_parents(status="PAID")


def test_approved_amount_above_claimed_is_rejected(app):
    with pytest.raises(IntegrityError):
        make_claim_with_parents(claimed_amount=40000, approved_amount=50000)


def test_claim_cannot_be_settled_twice(app):
    officer = make_user(email="officer@test.com", role="OFFICER")
    claim = make_claim_with_parents()

    db.session.add(Settlement(claim_id=claim.id, amount=40000, reference="STL-1", settled_by=officer.id))
    db.session.flush()

    with pytest.raises(IntegrityError):
        db.session.add(Settlement(claim_id=claim.id, amount=40000, reference="STL-2", settled_by=officer.id))
        db.session.flush()


def test_policy_with_claims_cannot_be_deleted(app):
    claim = make_claim_with_parents()
    db.session.commit()

    with pytest.raises(IntegrityError, match="fk_claims_policy_id_policies"):
        db.session.execute(delete(Policy).where(Policy.id == claim.policy_id))


def test_remaining_sum_insured_cannot_go_negative(app):
    user = make_user()
    policy = make_policy(user)
    db.session.commit()

    with pytest.raises(IntegrityError):
        policy.remaining_sum_insured = -1
        db.session.flush()
