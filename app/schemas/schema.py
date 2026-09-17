from typing import Literal
from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal

class UserReq(BaseModel):
    username: str
    email: str
    password: str

class LoginReq(BaseModel):
    identifier: str
    password: str

class VenueReq(BaseModel):
    name: str
    address: str
    display_image: str

class EventReq(BaseModel):
    name: str
    description: str
    display_image: str
    venue_id: int
    event_on: datetime

class SectionReq(BaseModel):
    name: str

class SectionModel(BaseModel):
    id: int
    name: str
    venue_id: int
    tier: int
    seat_count: int

class SectionReq(BaseModel):
    id: int
    name: str
    venue_id: int
    tier: int
    seat_count: int
    price: int

class SeatReq(BaseModel):
    code: str
    row_number: int

class BookingReq(BaseModel):
    section_id: int
    event_id: int
    seats: list[int]

class PaymentVerify(BaseModel):
    order_id: str
    payment_id: str
    signature: str

class SeatsQuery(BaseModel):
    format: Literal["true", "false"] = "true"

class TicketSaleFeature(BaseModel):
    days_since_live: int
    capacity: int

class SectionWiseStat(BaseModel):
    name: str
    tier: int
    price: Decimal = Decimal("0.0")
    capacity: int = 0
    sold: int = 0
    available: int = 0
    revenue: Decimal = Decimal("0.0")