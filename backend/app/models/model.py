from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import date, datetime

class Payment(BaseModel):
    payee_first_name: str
    payee_last_name: str
    payee_payment_status: str
    payee_added_date_utc: datetime
    payee_due_date: str
    payee_address_line_1: str
    payee_address_line_2: Optional[str] = None
    payee_city: str
    payee_country: str
    payee_province_or_state: Optional[str] = None
    payee_postal_code: int
    payee_phone_number: int
    payee_email: EmailStr
    currency: str
    discount_percent: Optional[float] = 0.0
    tax_percent: Optional[float] = 0.0
    due_amount: float
    total_due: Optional[float] = 0.0