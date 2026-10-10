from sqlalchemy.dialects.postgresql import JSONB

from app.constants import (
    CLAIM_STATUSES,
    DIAGNOSIS_CATEGORIES,
    DOCUMENT_TYPES,
    EXTRACTION_STATUSES,
    MAX_FILE_SIZE,
    RISK_LEVELS,
    RULE_CODES,
    sql_in,
)
from app.extensions import db


class Claim(db.Model):
    __tablename__ = "claims"

    id = db.Column(db.Integer, primary_key=True)
    claim_number = db.Column(db.String(20), nullable=False, unique=True)
    policy_id = db.Column(db.Integer, db.ForeignKey("policies.id", ondelete="RESTRICT"), nullable=False)
    hospital_id = db.Column(db.Integer, db.ForeignKey("hospitals.id", ondelete="RESTRICT"), nullable=False)
    admission_date = db.Column(db.Date, nullable=False)
    discharge_date = db.Column(db.Date, nullable=False)
    diagnosis_category = db.Column(db.String(40), nullable=False)
    claimed_amount = db.Column(db.Numeric(12, 2), nullable=False)
    approved_amount = db.Column(db.Numeric(12, 2))
    status = db.Column(db.String(15), nullable=False, server_default="SUBMITTED")
    risk_score = db.Column(db.Integer)
    risk_level = db.Column(db.String(6))
    ml_fraud_probability = db.Column(db.Numeric(4, 3))
    submitted_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    decided_at = db.Column(db.DateTime(timezone=True))
    decided_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"))

    policy = db.relationship("Policy", backref="claims")
    hospital = db.relationship("Hospital")
    officer = db.relationship("User", foreign_keys=[decided_by])
    documents = db.relationship("ClaimDocument", back_populates="claim")
    flags = db.relationship("RiskFlag", back_populates="claim", order_by="RiskFlag.rule_code")
    events = db.relationship("ClaimEvent", back_populates="claim", order_by="ClaimEvent.created_at")
    settlement = db.relationship("Settlement", back_populates="claim", uselist=False)

    __table_args__ = (
        db.CheckConstraint("discharge_date >= admission_date", name="discharge_after_admission"),
        db.CheckConstraint(sql_in("diagnosis_category", DIAGNOSIS_CATEGORIES), name="diagnosis_category"),
        db.CheckConstraint("claimed_amount > 0", name="claimed_amount_positive"),
        db.CheckConstraint(
            "approved_amount IS NULL OR (approved_amount > 0 AND approved_amount <= claimed_amount)",
            name="approved_amount_range",
        ),
        db.CheckConstraint(sql_in("status", CLAIM_STATUSES), name="status"),
        db.CheckConstraint("risk_score IS NULL OR risk_score BETWEEN 0 AND 100", name="risk_score_range"),
        db.CheckConstraint(f"risk_level IS NULL OR {sql_in('risk_level', RISK_LEVELS)}", name="risk_level"),
        db.CheckConstraint(
            "ml_fraud_probability IS NULL OR ml_fraud_probability BETWEEN 0 AND 1",
            name="ml_fraud_probability_range",
        ),
        db.Index("ix_claims_status_risk_score", "status", "risk_score"),
        db.Index("ix_claims_policy_id_submitted_at", "policy_id", "submitted_at"),
    )

    def to_dict(self, include_risk=True):
        data = {
            "id": self.id,
            "claim_number": self.claim_number,
            "policy_id": self.policy_id,
            "policy_number": self.policy.policy_number,
            "customer_name": self.policy.user.full_name,
            "hospital_id": self.hospital_id,
            "hospital_name": self.hospital.name,
            "admission_date": self.admission_date.isoformat(),
            "discharge_date": self.discharge_date.isoformat(),
            "diagnosis_category": self.diagnosis_category,
            "claimed_amount": float(self.claimed_amount),
            "approved_amount": float(self.approved_amount) if self.approved_amount is not None else None,
            "status": self.status,
            "submitted_at": self.submitted_at.isoformat(),
            "decided_at": self.decided_at.isoformat() if self.decided_at else None,
        }

        if include_risk:
            data["risk_score"] = self.risk_score
            data["risk_level"] = self.risk_level
            data["ml_fraud_probability"] = (
                float(self.ml_fraud_probability) if self.ml_fraud_probability is not None else None
            )

        return data


class ClaimDocument(db.Model):
    __tablename__ = "claim_documents"

    id = db.Column(db.Integer, primary_key=True)
    claim_id = db.Column(db.Integer, db.ForeignKey("claims.id", ondelete="CASCADE"), nullable=False, index=True)
    doc_type = db.Column(db.String(20), nullable=False)
    file_name = db.Column(db.String(200))
    file_data = db.Column(db.LargeBinary, nullable=False)
    file_sha256 = db.Column(db.CHAR(64), nullable=False, index=True)
    extracted_json = db.Column(JSONB)
    extraction_status = db.Column(db.String(10), nullable=False, server_default="PENDING")
    uploaded_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())

    claim = db.relationship("Claim", back_populates="documents")

    __table_args__ = (
        db.CheckConstraint(sql_in("doc_type", DOCUMENT_TYPES), name="doc_type"),
        db.CheckConstraint(f"octet_length(file_data) <= {MAX_FILE_SIZE}", name="file_size_max_2mb"),
        db.CheckConstraint(sql_in("extraction_status", EXTRACTION_STATUSES), name="extraction_status"),
    )


class RiskFlag(db.Model):
    __tablename__ = "risk_flags"

    id = db.Column(db.Integer, primary_key=True)
    claim_id = db.Column(db.Integer, db.ForeignKey("claims.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_code = db.Column(db.String(10), nullable=False)
    points = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.Text, nullable=False)

    claim = db.relationship("Claim", back_populates="flags")

    __table_args__ = (
        db.CheckConstraint(sql_in("rule_code", RULE_CODES), name="rule_code"),
        db.CheckConstraint("points > 0", name="points_positive"),
        db.UniqueConstraint("claim_id", "rule_code", name="uq_risk_flags_claim_id_rule_code"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "rule_code": self.rule_code,
            "points": self.points,
            "reason": self.reason,
        }


class ClaimEvent(db.Model):
    __tablename__ = "claim_events"

    id = db.Column(db.Integer, primary_key=True)
    claim_id = db.Column(db.Integer, db.ForeignKey("claims.id", ondelete="RESTRICT"), nullable=False, index=True)
    from_status = db.Column(db.String(15))
    to_status = db.Column(db.String(15), nullable=False)
    actor_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"))
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())

    claim = db.relationship("Claim", back_populates="events")
    actor = db.relationship("User")

    __table_args__ = (
        db.CheckConstraint(f"from_status IS NULL OR {sql_in('from_status', CLAIM_STATUSES)}", name="from_status"),
        db.CheckConstraint(sql_in("to_status", CLAIM_STATUSES), name="to_status"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "from_status": self.from_status,
            "to_status": self.to_status,
            "actor_name": self.actor.full_name if self.actor else None,
            "note": self.note,
            "created_at": self.created_at.isoformat(),
        }


class Settlement(db.Model):
    __tablename__ = "settlements"

    id = db.Column(db.Integer, primary_key=True)
    claim_id = db.Column(db.Integer, db.ForeignKey("claims.id", ondelete="RESTRICT"), nullable=False, unique=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    reference = db.Column(db.String(30), nullable=False, unique=True)
    settled_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    settled_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())

    claim = db.relationship("Claim", back_populates="settlement")
    officer = db.relationship("User")

    __table_args__ = (db.CheckConstraint("amount > 0", name="amount_positive"),)
