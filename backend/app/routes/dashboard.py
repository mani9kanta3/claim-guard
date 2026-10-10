from flask import Blueprint, jsonify

from app.auth.decorators import role_required
from app.extensions import db
from app.models import Claim, RiskFlag, Settlement

dashboard_bp = Blueprint("dashboard", __name__)


def count_by(column):
    rows = db.session.execute(
        db.select(column, db.func.count()).where(column.is_not(None)).group_by(column).order_by(column)
    ).all()
    return {value: count for value, count in rows}


@dashboard_bp.get("/summary")
@role_required("ADMIN", "OFFICER")
def summary():
    claims_by_status = count_by(Claim.status)
    claims_by_risk = count_by(Claim.risk_level)
    flags_by_rule = count_by(RiskFlag.rule_code)

    settled_amount = db.session.execute(db.select(db.func.coalesce(db.func.sum(Settlement.amount), 0))).scalar()

    avg_seconds = db.session.execute(
        db.select(db.func.avg(db.func.extract("epoch", Claim.decided_at - Claim.submitted_at))).where(
            Claim.decided_at.is_not(None)
        )
    ).scalar()

    return jsonify(
        {
            "total_claims": sum(claims_by_status.values()),
            "pending_review": claims_by_status.get("UNDER_REVIEW", 0) + claims_by_status.get("INVESTIGATION", 0),
            "awaiting_settlement": claims_by_status.get("APPROVED", 0),
            "high_risk": claims_by_risk.get("HIGH", 0),
            "settled_amount": float(settled_amount),
            "avg_hours_to_decision": round(float(avg_seconds) / 3600, 1) if avg_seconds else None,
            "claims_by_status": [{"status": key, "count": value} for key, value in claims_by_status.items()],
            "claims_by_risk": [{"risk_level": key, "count": value} for key, value in claims_by_risk.items()],
            "flags_by_rule": [{"rule_code": key, "count": value} for key, value in flags_by_rule.items()],
        }
    )
