from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class LineItem(BaseModel):
    description: str
    amount: float = Field(ge=0)


class BillExtraction(BaseModel):
    patient_name: Optional[str] = None
    hospital_name: Optional[str] = None
    admission_date: Optional[date] = None
    discharge_date: Optional[date] = None
    diagnosis: Optional[str] = None
    line_items: list[LineItem] = []
    total_amount: Optional[float] = Field(default=None, ge=0)
