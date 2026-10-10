import hashlib
from datetime import date

from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models import Claim, ClaimDocument, Hospital, Policy, User
from scripts.bill_maker import make_bill_pdf, make_bill_truth

PASSWORD = "password123"
PASSWORD_HASH = generate_password_hash(PASSWORD)


def make_user(email="customer@test.com", role="CUSTOMER", full_name="Test User"):
    user = User(full_name=full_name, email=email, password_hash=PASSWORD_HASH, role=role)
    db.session.add(user)
    db.session.flush()
    return user


def make_policy(user, policy_number="HLT-2026-00001", start_date=date(2026, 1, 1), sum_insured=500000):
    policy = Policy(
        policy_number=policy_number,
        user_id=user.id,
        plan_name="Gold",
        sum_insured=sum_insured,
        remaining_sum_insured=sum_insured,
        start_date=start_date,
        end_date=date(start_date.year + 1, start_date.month, start_date.day),
    )
    db.session.add(policy)
    db.session.flush()
    return policy


def make_hospital(is_network=True, name="Test Hospital"):
    hospital = Hospital(name=name, city="Hyderabad", is_network=is_network)
    db.session.add(hospital)
    db.session.flush()
    return hospital


def make_claim(policy, hospital, **changes):
    values = {
        "claim_number": "CLM-2026-000001",
        "policy_id": policy.id,
        "hospital_id": hospital.id,
        "admission_date": date(2026, 3, 1),
        "discharge_date": date(2026, 3, 4),
        "diagnosis_category": "FEVER",
        "claimed_amount": 40000,
    }
    values.update(changes)
    claim = Claim(**values)
    db.session.add(claim)
    db.session.flush()
    return claim


def make_claim_with_parents(**changes):
    user = make_user()
    policy = make_policy(user)
    hospital = make_hospital()
    return make_claim(policy, hospital, **changes)


def sample_bill_pdf(total_amount=40000, hospital_name="Test Hospital", admission=date(2026, 3, 1)):
    truth = make_bill_truth(
        "Test User", hospital_name, "Hyderabad", admission, date(2026, 3, 4), "FEVER", total_amount, "table"
    )
    return make_bill_pdf(truth, "INV-TEST")


def add_bill(claim, file_bytes=None, extracted=None):
    file_bytes = file_bytes or sample_bill_pdf()
    document = ClaimDocument(
        claim_id=claim.id,
        doc_type="HOSPITAL_BILL",
        file_name="bill.pdf",
        file_data=file_bytes,
        file_sha256=hashlib.sha256(file_bytes).hexdigest(),
        extraction_status="DONE" if extracted else "FAILED",
        extracted_json=extracted,
    )
    db.session.add(document)
    db.session.flush()
    db.session.refresh(claim, ["documents"])
    return document
