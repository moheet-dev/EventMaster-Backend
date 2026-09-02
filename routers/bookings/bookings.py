from fastapi import APIRouter, Depends, HTTPException
from routers.bookings.eventSections.eventSections import event_section_router
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select
from helpers.helper import get_section_lock
from dependency.dependency import getDb, getCurrentUser
from models.models import User, Booking, BookingSeat, EventSeat, Event, EventSection, Seat, SeatStatus, BookingStatus, Venue, Section
from schemas.schema import BookingReq, PaymentVerify
from datetime import timedelta, datetime, timezone
import razorpay
import os

RAZORPAY_ID = os.getenv("RAZORPAY_ID")
RAZORPAY_SECRET = os.getenv("RAZORPAY_SECRET")

client = razorpay.Client(auth=(RAZORPAY_ID, RAZORPAY_SECRET))

router = APIRouter()

router.include_router(
    event_section_router,
    prefix="/{eventId}/sections"
)

@router.post("/book")
async def addBookings(booking: BookingReq, db: AsyncSession = Depends(getDb), user: User = Depends(getCurrentUser)):
    result = await db.execute(select(Event).filter(Event.id == booking.event_id))
    existingEvent = result.scalars().first()

    result = await db.execute(
        select(EventSection).filter(
            EventSection.event_id == booking.event_id,
            EventSection.section_id == booking.section_id
        )
    )
    existingSection = result.scalars().first()

    if not existingEvent:
        raise HTTPException(
            detail="event does not exists",
            status_code=400
        )
    if not existingSection:
        raise HTTPException(
            detail="section does not exists",
            status_code=400
        )
    
    sessionLock = await get_section_lock(booking.event_id, booking.section_id)
    async with sessionLock:
        try:

            result = await db.execute(
                select(EventSeat)
                .join(Seat, Seat.id == EventSeat.seat_id)
                .join(
                    EventSection,
                    EventSection.section_id == Seat.section_id
                )
                .filter(
                    EventSection.section_id == booking.section_id,
                    EventSection.event_id == booking.event_id,
                    EventSeat.event_id == booking.event_id,
                    EventSeat.seat_id.in_(booking.seats)
                )
                .with_for_update()
            )
            eventSeats = result.scalars().all()
            if len(booking.seats) != len(set(eventSeats)):
                raise HTTPException(
                    detail="seat not found",
                    status_code=404
                )
            timeout = datetime.now(timezone.utc) + timedelta(minutes=5)
            for seat in eventSeats:
                if seat.status != SeatStatus.AVAILABLE:
                    raise HTTPException(
                        detail="seat already booked",
                        status_code=400
                    )
            
                seat.status = SeatStatus.HELD
                seat.timeout_at = timeout
            
            amountPayable = existingSection.price * (len(eventSeats))

            newBooking = Booking(
                user_id = user.id,
                event_id = booking.event_id,
                total_amount = amountPayable,
            )

            db.add(newBooking)
            await db.flush()
            for seat in eventSeats:
                db.add(BookingSeat(
                    booking_id = newBooking.id,
                    seat_id = seat.seat_id,
                    price = existingSection.price
                ))
            
            data = {
                "amount": int(amountPayable * 100),
                "currency": "INR",
                "receipt": (f"order_receipt_{newBooking.id}")
            }

            payment = client.order.create(data=data)
            newBooking.order_id = payment["id"]

            await db.commit()

            res = {
                "order_id": payment["id"],
                "amount": amountPayable
            }

            return {
                "data": res,
                "message": "please make the payment",
                "status": 201
            }
        except:
            await db.rollback()
            raise

@router.post("/book/verify")
async def paymentCallback(data: PaymentVerify, db: AsyncSession = Depends(getDb), user: User = Depends(getCurrentUser)):
    try:
        client.utility.verify_payment_signature({
            "razorpay_order_id": data.order_id,
            "razorpay_payment_id": data.payment_id,
            "razorpay_signature": data.signature
        })

        result = await db.execute(
            select(Booking).where(
                Booking.order_id == data.order_id
            )
        )

        existingBooking = result.scalars().first()

        if not existingBooking:
            raise HTTPException(
                detail="booking not found",
                status_code=404
            )

        if existingBooking.status != BookingStatus.PENDING:
            raise HTTPException(
                detail="booking already processed",
                status_code=400
            )

        existingBooking.status = BookingStatus.CONFIRMED
        existingBooking.payment_id = data.payment_id

        result = await db.execute(
            select(BookingSeat).where(
                BookingSeat.booking_id == existingBooking.id
            )
        )

        bookingSeats = result.scalars().all()

        seat_ids = [
            seat.seat_id
            for seat in bookingSeats
        ]

        await db.execute(
            update(EventSeat)
            .where(
                EventSeat.event_id == existingBooking.event_id,
                EventSeat.seat_id.in_(seat_ids)
            )
            .values(
                status=SeatStatus.SOLD,
                timeout_at=None
            )
        )

        await db.commit()

        return {
            "message": "payment verified successfully",
            "status": 200
        }

    except razorpay.errors.SignatureVerificationError:
        await db.rollback()

        raise HTTPException(
            detail="invalid payment signature",
            status_code=400
        )

    except HTTPException:
        await db.rollback()
        raise

    except Exception:
        await db.rollback()

        raise HTTPException(
            detail="verification failed",
            status_code=500
        )

@router.get("")
async def getBookings(db: AsyncSession = Depends(getDb), user: User = Depends(getCurrentUser)):
    stmt = (
        select(
            Booking.id,
            Booking.total_amount,
            Event.name.label("event_name"),
            Event.description,
            Event.display_image,
            Event.event_on,
            Venue.name.label("venue_name"),
            Venue.address,
            Booking.status,
            Booking.created_at
        )
        .outerjoin(Event, Event.id == Booking.event_id)
        .outerjoin(Venue, Venue.id == Event.venue_id)
        .where(
            Booking.user_id == user.id,
            Booking.status == BookingStatus.CONFIRMED
        )
    )

    result = await db.execute(stmt)
    bookings = result.mappings().all()
    return {
        "data": bookings,
        "message": "get bookings successful",
        "status": 200
    }

@router.get("/{bookingId}")
async def getBookingDetails(bookingId: int, db: AsyncSession = Depends(getDb), user: User = Depends(getCurrentUser)):
    stmt = (
        select(
            Section.name.label("section_name"),
            Seat.row_number,
            Seat.code,
            BookingSeat.price
        )
        .outerjoin(
            Seat,
            Seat.id == BookingSeat.seat_id
        )
        .outerjoin(
            Section,
            Section.id == Seat.section_id
        )
        .where(
            BookingSeat.booking_id == bookingId
        )
    )

    result = await db.execute(stmt)

    booking_seats = result.mappings().all()
    return {
        "data": booking_seats,
        "message": "get booked seats successful",
        "status": 200
    }