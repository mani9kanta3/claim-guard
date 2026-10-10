from datetime import date

import pytest

from app.extensions import db
from app.services.risk_rules import risk_level_for, run_rules, score_claim
from tests.factories import add_bill, make_claim, make_hospital, make_policy, make_user

GOOD_BILL = {
    "hospital_name": "Test Hospital",
    "admission_date": "2026-03-01",
    "discharge_date": "2026-03-04",
    "total_amount": 40000,
    "line_items": [],
}


def rule_codes(claim):
    return [flag["rule_code"] for flag in run_rules(claim)]


@pytest.fixture
def parents(app):
    user = make_user()
    return {"policy": make_policy(user), "network": make_hospital(), "outside": make_hospital(is_network=False, name="Far Away Clinic")}


def test_clean_claim_has_no_flags(parents):
    claim = make_claim(parents["policy"], parents["network"])
    add_bill(claim, extracted=GOOD_BILL)
    assert rule_codes(claim) == []


def test_r1_waiting_period(parents):
    claim = make_claim(parents["policy"], parents["network"], admission_date=date(2026, 1, 13), discharge_date=date(2026, 1, 15))
    assert "R1" in rule_codes(claim)


def test_r2_duplicate_bill(parents):
    first = make_claim(parents["policy"], parents["network"], claim_number="CLM-1")
    second = make_claim(parents["policy"], parents["network"], claim_number="CLM-2")
    bill_bytes = add_bill(first).file_data
    add_bill(second, file_bytes=bill_bytes)

    flags = run_rules(second)
    duplicate = [flag for flag in flags if flag["rule_code"] == "R2"]
    assert duplicate and "CLM-1" in duplicate[0]["reason"]


def test_r3_uses_most_of_cover(parents):
    claim = make_claim(parents["policy"], parents["network"], diagnosis_category="CARDIAC", claimed_amount=450000)
    assert "R3" in rule_codes(claim)


def test_r4_unusual_amount_for_category(parents):
    claim = make_claim(parents["policy"], parents["network"], claimed_amount=150000)
    assert "R4" in rule_codes(claim)


def test_r5_non_network_hospital(parents):
    claim = make_claim(parents["policy"], parents["outside"])
    assert rule_codes(claim) == ["R5"]


def test_r6_many_claims_in_a_year(parents):
    for number in range(4):
        make_claim(parents["policy"], parents["network"], claim_number=f"CLM-{number}")
    db.session.commit()

    latest = make_claim(parents["policy"], parents["network"], claim_number="CLM-LATEST")
    db.session.commit()
    assert "R6" in rule_codes(latest)


def test_r7_bill_total_mismatch(parents):
    claim = make_claim(parents["policy"], parents["network"])
    add_bill(claim, extracted={**GOOD_BILL, "total_amount": 25000})
    assert "R7" in rule_codes(claim)


def test_r8_bill_date_mismatch(parents):
    claim = make_claim(parents["policy"], parents["network"])
    add_bill(claim, extracted={**GOOD_BILL, "admission_date": "2026-03-03"})
    assert "R8" in rule_codes(claim)


def test_r7_and_r8_skip_when_extraction_failed(parents):
    claim = make_claim(parents["policy"], parents["network"], claimed_amount=41000)
    add_bill(claim, extracted=None)
    assert rule_codes(claim) == []


def test_score_is_capped_at_100(parents):
    claim = make_claim(
        parents["policy"], parents["outside"],
        admission_date=date(2026, 1, 10), discharge_date=date(2026, 1, 12), claimed_amount=450000,
    )
    add_bill(claim, extracted={**GOOD_BILL, "total_amount": 1000, "admission_date": "2026-01-01"})
    score_claim(claim)

    assert claim.risk_score == 100
    assert claim.risk_level == "HIGH"


@pytest.mark.parametrize("score, level", [(0, "LOW"), (29, "LOW"), (30, "MEDIUM"), (59, "MEDIUM"), (60, "HIGH"), (100, "HIGH")])
def test_risk_level_boundaries(score, level):
    assert risk_level_for(score) == level
