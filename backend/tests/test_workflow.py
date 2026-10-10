import pytest

from app.extensions import db
from app.models import ClaimEvent
from tests.conftest import login_as
from tests.factories import make_claim, make_hospital, make_policy


@pytest.fixture
def claim(demo_users):
    policy = make_policy(demo_users["customer"])
    claim = make_claim(policy, make_hospital(), status="UNDER_REVIEW", risk_score=10, risk_level="LOW")
    db.session.commit()
    return claim


def move(client, headers, claim_id, **body):
    return client.post(f"/api/claims/{claim_id}/transition", headers=headers, json=body)


def test_approve_then_settle(client, officer_headers, claim):
    response = move(client, officer_headers, claim.id, to_status="APPROVED", approved_amount=35000)
    assert response.status_code == 200
    assert response.get_json()["status"] == "APPROVED"

    response = client.post(f"/api/claims/{claim.id}/settle", headers=officer_headers)
    data = response.get_json()
    assert response.status_code == 200
    assert data["status"] == "SETTLED"
    assert data["remaining_sum_insured"] == 465000


def test_every_status_change_writes_an_event(client, officer_headers, claim):
    move(client, officer_headers, claim.id, to_status="INVESTIGATION", note="Call the hospital")
    move(client, officer_headers, claim.id, to_status="UNDER_REVIEW", note="Hospital confirmed")
    move(client, officer_headers, claim.id, to_status="REJECTED", note="Not covered")

    events = db.session.execute(db.select(ClaimEvent).filter_by(claim_id=claim.id).order_by(ClaimEvent.id)).scalars().all()
    assert [(e.from_status, e.to_status) for e in events] == [
        ("UNDER_REVIEW", "INVESTIGATION"),
        ("INVESTIGATION", "UNDER_REVIEW"),
        ("UNDER_REVIEW", "REJECTED"),
    ]


def test_settle_twice_returns_409(client, officer_headers, claim):
    move(client, officer_headers, claim.id, to_status="APPROVED", approved_amount=35000)
    client.post(f"/api/claims/{claim.id}/settle", headers=officer_headers)

    response = client.post(f"/api/claims/{claim.id}/settle", headers=officer_headers)
    assert response.status_code == 409


def test_cannot_settle_before_approval(client, officer_headers, claim):
    response = client.post(f"/api/claims/{claim.id}/settle", headers=officer_headers)
    assert response.status_code == 409


def test_rejected_claim_cannot_be_approved(client, officer_headers, claim):
    move(client, officer_headers, claim.id, to_status="REJECTED", note="Not covered")
    response = move(client, officer_headers, claim.id, to_status="APPROVED", approved_amount=1000)

    assert response.status_code == 409
    assert response.get_json()["error"] == "INVALID_TRANSITION"


def test_settled_is_not_allowed_through_transition(client, officer_headers, claim):
    response = move(client, officer_headers, claim.id, to_status="SETTLED")
    assert response.status_code == 400


def test_reject_needs_a_note(client, officer_headers, claim):
    response = move(client, officer_headers, claim.id, to_status="REJECTED")
    assert response.status_code == 400


def test_approved_amount_above_claimed_is_rejected(client, officer_headers, claim):
    response = move(client, officer_headers, claim.id, to_status="APPROVED", approved_amount=50000)
    assert response.status_code == 400


def test_customer_cannot_change_status(client, customer_headers, claim):
    response = move(client, customer_headers, claim.id, to_status="APPROVED", approved_amount=1000)
    assert response.status_code == 403


def test_officer_cannot_decide_own_claim(client, demo_users):
    own_policy = make_policy(demo_users["officer"], policy_number="HLT-2026-00099")
    own_claim = make_claim(own_policy, make_hospital(), claim_number="CLM-OWN", status="UNDER_REVIEW")
    db.session.commit()

    headers = login_as(client, "officer@demo.com")
    response = move(client, headers, own_claim.id, to_status="APPROVED", approved_amount=1000)
    assert response.status_code == 403
