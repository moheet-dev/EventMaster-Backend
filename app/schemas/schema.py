from pydantic import BaseModel
from datetime import datetime

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