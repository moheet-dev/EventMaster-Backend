from database.database import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, func, Text, ForeignKey, DateTime, Numeric, CheckConstraint, Enum as SQLEnum
from datetime import datetime
from decimal import Decimal
from enum import Enum

class SeatStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    HELD = "HELD"
    SOLD = "SOLD"


class BookingStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50),unique=True,nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

class Venue(Base):
    __tablename__ = "venues"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    display_image: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL", onupdate="CASCADE"))


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    display_image: Mapped[str] = mapped_column(Text)
    venue_id: Mapped[int] = mapped_column(ForeignKey("venues.id", ondelete="SET NULL", onupdate="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL", onupdate="CASCADE"))
    event_on: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

class Section(Base):
    __tablename__ = "sections"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    tier: Mapped[int] = mapped_column(Numeric, nullable=False)
    venue_id: Mapped[int] = mapped_column(ForeignKey("venues.id", ondelete="CASCADE", onupdate="CASCADE"))

class Seat(Base):
    __tablename__ = "seats"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    row_number: Mapped[int] = mapped_column(Numeric, nullable=False)
    section_id: Mapped[int] = mapped_column(ForeignKey("sections.id", ondelete="CASCADE", onupdate="CASCADE"))

class EventSection(Base):
    __tablename__ = "event_sections"

    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    section_id: Mapped[int] = mapped_column(ForeignKey("sections.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    __table_args__ = (
        CheckConstraint("price > 0", name="check_event_section_price"),
    )

class EventSeat(Base):
    __tablename__ = "event_seats"

    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    seat_id: Mapped[int] = mapped_column(ForeignKey("seats.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    status: Mapped[SeatStatus] = mapped_column(SQLEnum(SeatStatus, name="seat_status"), nullable=False, default=SeatStatus.AVAILABLE)
    timeout_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[BookingStatus] = mapped_column(SQLEnum(BookingStatus, name="booking_status"), nullable=False, default=BookingStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    order_id: Mapped[str | None] = mapped_column(Text, unique=True)
    payment_id: Mapped[str | None] = mapped_column(Text, unique=True)

    __table_args__ = (
        CheckConstraint("total_amount > 0", name="check_booking_total_amount"),
    )


class BookingSeat(Base):
    __tablename__ = "booking_seats"

    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id", ondelete="RESTRICT", onupdate="CASCADE"), primary_key=True)
    seat_id: Mapped[int] = mapped_column(ForeignKey("seats.id", ondelete="RESTRICT", onupdate="CASCADE"), primary_key=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    __table_args__ = (
        CheckConstraint("price > 0", name="check_booking_seat_price"),
    )