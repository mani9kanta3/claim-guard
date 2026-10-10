from datetime import date
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator

from app.constants import DIAGNOSIS_CATEGORIES

DiagnosisCategory = Literal[tuple(DIAGNOSIS_CATEGORIES)]


class ClaimSubmitRequest(BaseModel):
    policy_id: int
    hospital_id: int
    admission_date: date
    discharge_date: date
    diagnosis_category: DiagnosisCategory
    claimed_amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)

    @model_validator(mode="after")
    def check_dates(self):
        if self.discharge_date < self.admission_date:
            raise ValueError("discharge date cannot be before admission date")
        if self.admission_date > date.today():
            raise ValueError("admission date cannot be in the future")
        return self


class TransitionRequest(BaseModel):
    to_status: Literal["UNDER_REVIEW", "INVESTIGATION", "APPROVED", "REJECTED"]
    note: Optional[str] = Field(default=None, max_length=1000)
    approved_amount: Optional[Decimal] = Field(default=None, gt=0, max_digits=12, decimal_places=2)
