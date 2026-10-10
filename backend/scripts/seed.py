import hashlib
import random
from datetime import date, datetime, time, timedelta, timezone

from werkzeug.security import generate_password_hash

from app import create_app
from app.constants import CATEGORY_AMOUNT_RANGES, CATEGORY_AVERAGE_AMOUNT
from app.extensions import db
from app.models import Claim, ClaimDocument, ClaimEvent, Hospital, Policy, RiskFlag, Settlement, User
from app.services.ml_scorer import predict_fraud_probability
from app.services.risk_rules import score_claim
from scripts.bill_maker import LAYOUTS, make_bill_pdf, make_bill_truth

random.seed(42)

TODAY = date.today()
IST = timezone(timedelta(hours=5, minutes=30))
DEMO_PASSWORD = "password123"
TOTAL_CLAIMS = 60

CUSTOMER_NAMES = [
    "Ravi Kumar", "Priya Sharma", "Arjun Reddy", "Sneha Iyer", "Vikram Singh",
    "Lakshmi Nair", "Rahul Verma", "Divya Menon", "Karthik Rao", "Pooja Patel",
    "Suresh Babu", "Anjali Gupta", "Manoj Pillai", "Kavya Joshi", "Naveen Das",
    "Meera Krishnan", "Aditya Kulkarni", "Swathi Prasad", "Imran Khan", "Deepa Raghavan",
]

HOSPITALS = [
    ("Sunrise Multispeciality Hospital", "Hyderabad", True),
    ("City Care Clinic", "Bengaluru", True),
    ("Lotus Heart Institute", "Chennai", True),
    ("Green Park Hospital", "Pune", True),
    ("Blue Cross Medical Centre", "Mumbai", True),
    ("Silver Oak Hospital", "Hyderabad", True),
    ("Riverside Health", "Kochi", True),
    ("Apex Ortho Care", "Bengaluru", True),
    ("Shanti Maternity Home", "Chennai", True),
    ("Metro Lifeline Hospital", "Delhi", True),
    ("Green Valley Hospital", "Chennai", False),
    ("Hilltop Nursing Home", "Mysuru", False),
    ("New Hope Clinic", "Vijayawada", False),
    ("Star Health Point", "Nagpur", False),
    ("Royal Care Hospital", "Indore", False),
]

PLANS = {"Silver": 300000, "Gold": 500000, "Platinum": 1000000}
CHEAP_CATEGORIES = ["FEVER", "RESPIRATORY", "OTHER", "SURGERY_MINOR"]


def money(amount):
    return round(amount / 100) * 100


def at_time(day, hour):
    return datetime.combine(day, time(hour=hour), tzinfo=IST)


def create_users():
    password_hash = generate_password_hash(DEMO_PASSWORD)

    admin = User(full_name="Admin User", email="admin@demo.com", role="ADMIN", password_hash=password_hash)
    officers = [
        User(full_name="Anita Rao", email="officer@demo.com", role="OFFICER", password_hash=password_hash),
        User(full_name="Rohit Mehta", email="officer2@demo.com", role="OFFICER", password_hash=password_hash),
    ]

    customers = []
    for index, name in enumerate(CUSTOMER_NAMES):
        email = "customer@demo.com" if index == 0 else name.lower().replace(" ", ".") + "@example.com"
        customers.append(User(full_name=name, email=email, role="CUSTOMER", password_hash=password_hash))

    db.session.add_all([admin, *officers, *customers])
    db.session.flush()
    return officers, customers


def create_hospitals():
    hospitals = [Hospital(name=name, city=city, is_network=is_network) for name, city, is_network in HOSPITALS]
    db.session.add_all(hospitals)
    db.session.flush()
    return hospitals


def create_policies(customers):
    owners = customers + customers[:10]
    policies = []

    for number, owner in enumerate(owners, start=1):
        plan_name = random.choice(list(PLANS))
        start_date = TODAY - timedelta(days=random.randint(60, 500))
        end_date = start_date + timedelta(days=365)

        policies.append(
            Policy(
                policy_number=f"HLT-{start_date.year}-{number:05d}",
                user_id=owner.id,
                plan_name=plan_name,
                sum_insured=PLANS[plan_name],
                remaining_sum_insured=PLANS[plan_name],
                start_date=start_date,
                end_date=end_date,
                waiting_period_days=30,
                status="ACTIVE" if end_date > TODAY else "EXPIRED",
            )
        )

    db.session.add_all(policies)
    db.session.flush()
    return policies


def choose_policy(policies, claim_counts, suspicious):
    if suspicious:
        return random.choice(policies)
    quiet_policies = [policy for policy in policies if claim_counts.get(policy.id, 0) < 2]
    return random.choice(quiet_policies or policies)


def plan_claim(policy, hospitals, suspicious):
    last_day = min(policy.end_date, TODAY - timedelta(days=3))

    if suspicious:
        admission_date = policy.start_date + timedelta(days=random.randint(5, 25))
        category = random.choice(CHEAP_CATEGORIES)
        amount = CATEGORY_AVERAGE_AMOUNT[category] * random.uniform(3.2, 4.0)
        hospital = random.choice([h for h in hospitals if not h.is_network])
    else:
        first_day = policy.start_date + timedelta(days=policy.waiting_period_days)
        admission_date = first_day + timedelta(days=random.randint(0, (last_day - first_day).days))
        category = random.choice(list(CATEGORY_AMOUNT_RANGES))
        amount = random.uniform(*CATEGORY_AMOUNT_RANGES[category])
        hospital = random.choices(hospitals, weights=[4 if h.is_network else 1 for h in hospitals])[0]

    admission_date = min(admission_date, last_day)
    discharge_date = min(admission_date + timedelta(days=random.randint(1, 6)), TODAY - timedelta(days=1))

    return {
        "policy": policy,
        "hospital": hospital,
        "admission_date": admission_date,
        "discharge_date": discharge_date,
        "category": category,
        "amount": money(amount),
        "suspicious": suspicious,
    }


def make_bill(plan, claim_amount, bill_number):
    bill_total = claim_amount
    bill_admission = plan["admission_date"]

    if plan["suspicious"]:
        trick = random.choice(["lower_total", "earlier_date", "none"])
        if trick == "lower_total":
            bill_total = money(claim_amount * random.uniform(0.55, 0.8))
        elif trick == "earlier_date":
            bill_admission = plan["admission_date"] + timedelta(days=random.randint(1, 3))
            bill_admission = min(bill_admission, plan["discharge_date"])

    truth = make_bill_truth(
        plan["policy"].user.full_name,
        plan["hospital"].name,
        plan["hospital"].city,
        bill_admission,
        plan["discharge_date"],
        plan["category"],
        bill_total,
        random.choice(LAYOUTS),
    )
    pdf_bytes = make_bill_pdf(truth, bill_number)

    extracted = {key: value for key, value in truth.items() if key not in ("city", "layout")}
    extracted["provider"] = "seed"
    extracted["line_items_total"] = round(sum(item["amount"] for item in truth["line_items"]), 2)
    return pdf_bytes, extracted


def pick_status(risk_level, submitted_on):
    if (TODAY - submitted_on).days <= 20:
        return "UNDER_REVIEW"
    if risk_level == "HIGH":
        return random.choice(["UNDER_REVIEW", "UNDER_REVIEW", "INVESTIGATION", "REJECTED"])
    return random.choice(["UNDER_REVIEW", "UNDER_REVIEW", "INVESTIGATION", "APPROVED", "SETTLED", "SETTLED", "REJECTED"])


def reject_reason(flag_codes):
    if "R2" in flag_codes:
        return "Same bill was already used in another claim"
    if "R1" in flag_codes:
        return "Treatment falls inside the waiting period"
    if "R7" in flag_codes or "R8" in flag_codes:
        return "Bill details do not match the claim form"
    if "R4" in flag_codes or "R3" in flag_codes:
        return "Amount is much higher than usual for this treatment"
    return "Treatment is not covered under the policy terms"


def add_event(claim, from_status, to_status, created_at, actor_id=None, note=None):
    db.session.add(
        ClaimEvent(
            claim_id=claim.id,
            from_status=from_status,
            to_status=to_status,
            actor_id=actor_id,
            note=note,
            created_at=created_at,
        )
    )


def finish_claim(claim, status, officer, flag_codes, settlement_number):
    submitted_at = claim.submitted_at
    add_event(claim, "SUBMITTED", "UNDER_REVIEW", submitted_at + timedelta(seconds=4),
              note=f"Automatic checks done, risk {claim.risk_level}")

    if status == "UNDER_REVIEW":
        claim.status = status
        return settlement_number

    decided_at = submitted_at + timedelta(hours=random.randint(2, 72))

    if status == "INVESTIGATION":
        add_event(claim, "UNDER_REVIEW", "INVESTIGATION", decided_at, officer.id, "Calling the hospital to verify the bill")
        claim.status = status
        return settlement_number

    if status == "REJECTED":
        add_event(claim, "UNDER_REVIEW", "REJECTED", decided_at, officer.id, reject_reason(flag_codes))
        claim.status, claim.decided_at, claim.decided_by = status, decided_at, officer.id
        return settlement_number

    policy = claim.policy
    approved = min(money(float(claim.claimed_amount) * random.uniform(0.85, 1.0)), float(policy.remaining_sum_insured))
    claim.approved_amount = approved
    claim.decided_at, claim.decided_by = decided_at, officer.id
    add_event(claim, "UNDER_REVIEW", "APPROVED", decided_at, officer.id, "Documents verified")
    claim.status = "APPROVED"

    if status == "SETTLED":
        settlement_number += 1
        settled_at = decided_at + timedelta(hours=random.randint(1, 24))
        reference = f"STL-{settled_at.year}-{settlement_number:06d}"
        db.session.add(
            Settlement(claim_id=claim.id, amount=approved, reference=reference, settled_by=officer.id, settled_at=settled_at)
        )
        policy.remaining_sum_insured = float(policy.remaining_sum_insured) - approved
        add_event(claim, "APPROVED", "SETTLED", settled_at, officer.id, f"Settlement {reference}")
        claim.status = "SETTLED"

    return settlement_number


def create_claims(policies, hospitals, officers):
    plans = []
    claim_counts = {}
    for _ in range(TOTAL_CLAIMS):
        suspicious = random.random() < 0.22
        policy = choose_policy(policies, claim_counts, suspicious)
        claim_counts[policy.id] = claim_counts.get(policy.id, 0) + 1
        plans.append(plan_claim(policy, hospitals, suspicious))
    plans.sort(key=lambda plan: plan["admission_date"])

    settlement_number = 0
    saved_bills = []

    for number, plan in enumerate(plans, start=1):
        policy = plan["policy"]
        remaining = float(policy.remaining_sum_insured)
        amount = plan["amount"]
        if plan["suspicious"] and random.random() < 0.5:
            amount = money(remaining * random.uniform(0.82, 0.95))
        if amount > remaining:
            amount = money(remaining * 0.5)

        submitted_on = min(plan["discharge_date"] + timedelta(days=random.randint(1, 5)), TODAY)
        claim = Claim(
            claim_number=f"CLM-{submitted_on.year}-{number:06d}",
            policy_id=policy.id,
            hospital_id=plan["hospital"].id,
            admission_date=plan["admission_date"],
            discharge_date=plan["discharge_date"],
            diagnosis_category=plan["category"],
            claimed_amount=amount,
            status="SUBMITTED",
            submitted_at=at_time(submitted_on, random.randint(9, 18)),
        )
        db.session.add(claim)
        db.session.flush()
        add_event(claim, None, "SUBMITTED", claim.submitted_at, actor_id=policy.user_id)

        if plan["suspicious"] and saved_bills and random.random() < 0.2:
            pdf_bytes, extracted = random.choice(saved_bills)
        else:
            pdf_bytes, extracted = make_bill(plan, amount, f"INV-{number:05d}")
            saved_bills.append((pdf_bytes, extracted))

        db.session.add(
            ClaimDocument(
                claim_id=claim.id,
                doc_type="HOSPITAL_BILL",
                file_name=f"bill_{claim.claim_number}.pdf",
                file_data=pdf_bytes,
                file_sha256=hashlib.sha256(pdf_bytes).hexdigest(),
                extraction_status="DONE",
                extracted_json=extracted,
            )
        )
        db.session.flush()
        db.session.refresh(claim, ["documents"])

        flags = score_claim(claim)
        claim.ml_fraud_probability = predict_fraud_probability(claim)

        status = pick_status(claim.risk_level, submitted_on)
        flag_codes = [flag["rule_code"] for flag in flags]
        settlement_number = finish_claim(claim, status, random.choice(officers), flag_codes, settlement_number)
        db.session.flush()


def seed():
    db.drop_all()
    db.create_all()

    officers, customers = create_users()
    hospitals = create_hospitals()
    policies = create_policies(customers)
    create_claims(policies, hospitals, officers)

    db.session.commit()


def print_summary():
    print("Tables created and filled:")
    for model in [User, Hospital, Policy, Claim, ClaimDocument, RiskFlag, ClaimEvent, Settlement]:
        count = db.session.execute(db.select(db.func.count()).select_from(model)).scalar()
        print(f"  {model.__tablename__:<16} {count}")

    by_status = db.session.execute(db.select(Claim.status, db.func.count()).group_by(Claim.status)).all()
    by_risk = db.session.execute(db.select(Claim.risk_level, db.func.count()).group_by(Claim.risk_level)).all()
    by_rule = db.session.execute(db.select(RiskFlag.rule_code, db.func.count()).group_by(RiskFlag.rule_code)).all()
    print("Claims by status:", dict(by_status))
    print("Claims by risk:", dict(by_risk))
    print("Flags by rule:", dict(sorted(by_rule)))
    print(f"Demo logins: customer@demo.com / officer@demo.com / admin@demo.com, password: {DEMO_PASSWORD}")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        seed()
        print_summary()
