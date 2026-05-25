from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel


class TripIter(BaseModel):
    nr: int
    country: str
    start: str
    depart_at: Optional[datetime]
    border_at: Optional[datetime]
    destination: str
    arrive_at: Optional[datetime]
    hours_diff: float


class TripVoyDiet(BaseModel):
    nr: int
    country: str
    currency: str
    rate: Decimal
    units: Decimal
    amount: Decimal
    fx_rate: Decimal
    fx_date: Optional[date]
    fx_table: str
    amount_pln: Decimal


class Trip(BaseModel):
    nr_del: str
    employee: str
    purpose_city: str
    purpose_desc: str
    transport: str
    advance: Decimal
    currency: str
    date_from: Optional[date]
    date_to: Optional[date]
    year: int
    signed_at: Optional[date]
    proofs_count: int
    test: bool
    created_at: Optional[datetime]
    iters: List[TripIter]
    diets: List[TripVoyDiet]
    total_diet_pln: Decimal
