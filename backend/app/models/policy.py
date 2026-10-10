from app.constants import POLICY_STATUSES, sql_in
from app.extensions import db


class Policy(db.Model):
    __tablename__ = "policies"

    id = db.Column(db.Integer, primary_key=True)
    policy_number = db.Column(db.String(20), nullable=False, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    plan_name = db.Column(db.String(60))
    sum_insured = db.Column(db.Numeric(12, 2), nullable=False)
    remaining_sum_insured = db.Column(db.Numeric(12, 2), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    waiting_period_days = db.Column(db.Integer, nullable=False, server_default="30")
    status = db.Column(db.String(10), nullable=False, server_default="ACTIVE")

    user = db.relationship("User", backref="policies")

    __table_args__ = (
        db.CheckConstraint("sum_insured > 0", name="sum_insured_positive"),
        db.CheckConstraint(
            "remaining_sum_insured >= 0 AND remaining_sum_insured <= sum_insured",
            name="remaining_sum_insured_range",
        ),
        db.CheckConstraint("end_date > start_date", name="end_after_start"),
        db.CheckConstraint("waiting_period_days >= 0", name="waiting_period_not_negative"),
        db.CheckConstraint(sql_in("status", POLICY_STATUSES), name="status"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "policy_number": self.policy_number,
            "user_id": self.user_id,
            "holder_name": self.user.full_name,
            "plan_name": self.plan_name,
            "sum_insured": float(self.sum_insured),
            "remaining_sum_insured": float(self.remaining_sum_insured),
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "waiting_period_days": self.waiting_period_days,
            "status": self.status,
        }
