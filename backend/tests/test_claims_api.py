import io

import pytest

from app.extensions import db
from tests.conftest import login_as
from tests.factories import make_claim, make_hospital, make_policy, make_user, sample_bill_pdf


@pytest.fixture
def customer_claim(demo_users):
    policy = make_policy(demo_users["customer"])
    hospital = make_hospital()
    claim = make_claim(policy, hospital, status="UNDER_REVIEW", risk_score=75, risk_level="HIGH")
    db.session.commit()
    return claim


def test_customer_sees_own_claims_without_risk(client, customer_headers, customer_claim):
    response = client.get("/api/claims", headers=customer_headers)
    claims = response.get_json()["items"]

    assert response.status_code == 200
    assert [c["claim_number"] for c in claims] == ["CLM-2026-000001"]
    assert "risk_score" not in claims[0]


def test_officer_sees_risk_score(client, officer_headers, customer_claim):
    response = client.get(f"/api/claims/{customer_claim.id}", headers=officer_headers)

    assert response.status_code == 200
    assert response.get_json()["risk_score"] == 75


def test_officer_can_filter_by_risk_level(client, officer_headers, customer_claim):
    high = client.get("/api/claims?risk_level=HIGH", headers=officer_headers).get_json()
    low = client.get("/api/claims?risk_level=LOW", headers=officer_headers).get_json()

    assert high["total"] == 1
    assert low["total"] == 0


def test_customer_cannot_see_other_customers_claim(client, customer_claim):
    make_user(email="other@demo.com")
    db.session.commit()
    headers = login_as(client, "other@demo.com")

    response = client.get(f"/api/claims/{customer_claim.id}", headers=headers)
    assert response.status_code == 404


def test_customer_sees_only_own_policies(client, customer_headers, demo_users):
    make_policy(demo_users["customer"], policy_number="HLT-2026-00001")
    make_policy(make_user(email="other@demo.com"), policy_number="HLT-2026-00002")
    db.session.commit()

    response = client.get("/api/policies", headers=customer_headers)
    assert [p["policy_number"] for p in response.get_json()] == ["HLT-2026-00001"]


def test_submit_claim_rejects_non_pdf(client, customer_headers):
    fake_file = (io.BytesIO(b"this is not a pdf"), "bill.pdf")

    response = client.post(
        "/api/claims",
        headers=customer_headers,
        data={"bill": fake_file},
        content_type="multipart/form-data",
    )
    assert response.status_code == 400


def test_officer_cannot_submit_claim(client, officer_headers):
    response = client.post("/api/claims", headers=officer_headers)
    assert response.status_code == 403


def test_dashboard_counts_claims(client, admin_headers, customer_claim):
    response = client.get("/api/dashboard/summary", headers=admin_headers)
    data = response.get_json()

    assert response.status_code == 200
    assert data["total_claims"] == 1
    assert data["pending_review"] == 1
    assert data["high_risk"] == 1


def claim_form(policy_id, hospital_id, **changes):
    form = {
        "policy_id": str(policy_id),
        "hospital_id": str(hospital_id),
        "admission_date": "2026-03-01",
        "discharge_date": "2026-03-04",
        "diagnosis_category": "FEVER",
        "claimed_amount": "40000",
    }
    form.update(changes)
    return form


def submit(client, headers, form, file_bytes, file_name="bill.pdf"):
    data = {**form, "bill": (io.BytesIO(file_bytes), file_name)}
    return client.post("/api/claims", headers=headers, data=data, content_type="multipart/form-data")


@pytest.fixture
def policy_and_hospital(demo_users):
    policy = make_policy(demo_users["customer"])
    hospital = make_hospital()
    db.session.commit()
    return policy, hospital


def test_submit_claim_success(client, customer_headers, policy_and_hospital):
    policy, hospital = policy_and_hospital
    response = submit(client, customer_headers, claim_form(policy.id, hospital.id), sample_bill_pdf())
    data = response.get_json()

    assert response.status_code == 201
    assert data["status"] == "UNDER_REVIEW"
    assert data["claim_number"].startswith("CLM-")
    assert "risk_score" not in data
    assert [e["to_status"] for e in data["events"]] == ["SUBMITTED", "UNDER_REVIEW"]


def test_officer_sees_extraction_failed_without_api_key(client, customer_headers, officer_headers, policy_and_hospital):
    policy, hospital = policy_and_hospital
    claim_id = submit(client, customer_headers, claim_form(policy.id, hospital.id), sample_bill_pdf()).get_json()["id"]

    data = client.get(f"/api/claims/{claim_id}", headers=officer_headers).get_json()
    assert data["bill"]["extraction_status"] == "FAILED"
    assert data["risk_level"] == "LOW"


def test_submit_rejects_file_over_2mb(client, customer_headers, policy_and_hospital):
    policy, hospital = policy_and_hospital
    big_file = b"%PDF" + b"0" * (2 * 1024 * 1024)
    response = submit(client, customer_headers, claim_form(policy.id, hospital.id), big_file)
    assert response.status_code == 413


def test_claim_outside_policy_dates_is_auto_rejected(client, customer_headers, policy_and_hospital):
    policy, hospital = policy_and_hospital
    form = claim_form(policy.id, hospital.id, admission_date="2025-06-01", discharge_date="2025-06-03")
    data = submit(client, customer_headers, form, sample_bill_pdf()).get_json()

    assert data["status"] == "REJECTED"
    assert data["events"][-1]["note"] == "Policy was not active on the admission date"


def test_claim_above_remaining_cover_is_auto_rejected(client, customer_headers, policy_and_hospital):
    policy, hospital = policy_and_hospital
    form = claim_form(policy.id, hospital.id, claimed_amount="600000")
    data = submit(client, customer_headers, form, sample_bill_pdf()).get_json()
    assert data["status"] == "REJECTED"


def test_cannot_claim_on_someone_elses_policy(client, customer_headers):
    other_policy = make_policy(make_user(email="other@demo.com"), policy_number="HLT-2026-00777")
    hospital = make_hospital()
    db.session.commit()

    response = submit(client, customer_headers, claim_form(other_policy.id, hospital.id), sample_bill_pdf())
    assert response.status_code == 404


def test_discharge_before_admission_is_400(client, customer_headers, policy_and_hospital):
    policy, hospital = policy_and_hospital
    form = claim_form(policy.id, hospital.id, admission_date="2026-03-05", discharge_date="2026-03-01")
    response = submit(client, customer_headers, form, sample_bill_pdf())
    assert response.status_code == 400


def test_officer_can_download_bill(client, customer_headers, officer_headers, policy_and_hospital):
    policy, hospital = policy_and_hospital
    claim_id = submit(client, customer_headers, claim_form(policy.id, hospital.id), sample_bill_pdf()).get_json()["id"]

    response = client.get(f"/api/claims/{claim_id}/document", headers=officer_headers)
    assert response.status_code == 200
    assert response.data.startswith(b"%PDF")


def test_admin_creates_hospital_and_policy(client, admin_headers, demo_users):
    hospital = client.post("/api/hospitals", headers=admin_headers, json={"name": "New Clinic", "city": "Pune", "is_network": True})
    assert hospital.status_code == 201

    policy = client.post(
        "/api/policies",
        headers=admin_headers,
        json={
            "user_id": demo_users["customer"].id,
            "plan_name": "Gold",
            "sum_insured": 500000,
            "start_date": "2026-01-01",
            "end_date": "2027-01-01",
        },
    )
    assert policy.status_code == 201
    assert policy.get_json()["policy_number"].startswith("HLT-")
