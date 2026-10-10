from datetime import date
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator


class HospitalCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    city: Optional[str] = Field(default=None, max_length=60)
    is_network: bool = False


class PolicyCreateRequest(BaseModel):
    user_id: int
    plan_name: Literal["Silver", "Gold", "Platinum"]
    sum_insured: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    start_date: date
    end_date: date
    waiting_period_days: int = Field(default=30, ge=0, le=365)

    @model_validator(mode="after")
    def check_dates(self):
        if self.end_date <= self.start_date:
            raise ValueError("end date must be after start date")
        return self
