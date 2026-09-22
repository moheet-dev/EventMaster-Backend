from fastapi import APIRouter, Depends, HTTPException, Query
from app.models.models import User, Event, EventSeat, EventSection, Seat, Venue, Section, Booking, SeatStatus, BookingStatus, BookingSeat
from app.schemas.schema import EventReq, SectionReq, SectionWiseStat
from app.dependency.dependency import getCurrentUser, getDb
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc, literal, select, func, and_
from math import ceil
from datetime import date, timedelta, datetime, timezone

router = APIRouter()

@router.get("")
async def getAllEvents(
        nameSearch: str | None = None, 
        venueSearch: int | None = None, 
        from_date: date | None = None,
        to_date: date | None = None,
        page: int = Query(default=1, ge=1),
        limit: int = Query(default=10, ge=1, le=100),
        db: AsyncSession = Depends(getDb), 
        user: User = Depends(getCurrentUser),
    ):

    stmt = select(Event.id, Event.name, Event.description, Event.display_image, Event.venue_id, 
                Event.event_on, Event.created_at, Event.created_by, literal(0).label("rank"))

    if nameSearch:
        tsquery = func.plainto_tsquery("english", nameSearch)
        rank = func.ts_rank(Event.tsv, tsquery)
        stmt = select(Event.id, Event.name, Event.description, Event.display_image, Event.venue_id, 
                Event.event_on, Event.created_at, Event.created_by, rank.label("rank")).where(Event.tsv.op("@@")(tsquery))
    if venueSearch is not None:
        stmt = stmt.filter(Event.venue_id == venueSearch)
    if from_date is not None:
        stmt = stmt.filter(from_date <= Event.event_on)
    if to_date is not None:
        stmt = stmt.filter(to_date + timedelta(days=1) > Event.event_on)

    count_result = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total = count_result.scalar()

    offset = (page - 1) * limit
    totalPages = ceil(total / limit)

    result = await db.execute(stmt.offset(offset).limit(limit).order_by(desc("rank")))
    rows = result.all()

    events = [
        dict(row._mapping)
        for row in rows
    ]

    return {
        "data": events,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": totalPages
        },
        "message": "all event get successful",
        "status": 200
    }

@router.get("/{eventId}")
async def getEvent(eventId: int, db: AsyncSession = Depends(getDb), user: User = Depends(getCurrentUser)):
    result = await db.execute(select(Event).filter(Event.id == eventId))
    event = result.scalars().first()

    if not event:
        raise HTTPException(
            detail="event not found",
            status_code=404
        )

    return {
        "data": event,
        "message": "event found",
        "status": 200
    }

@router.post("/add")
async def createEvent(data: EventReq, eventSections: list[SectionReq], db: AsyncSession = Depends(getDb), user: User = Depends(getCurrentUser)):
    result = await db.execute(select(Venue).filter(Venue.id == data.venue_id, Venue.created_by == user.id))
    venue = result.scalars().first()

    if not venue:
        raise HTTPException(
                detail="Invalid Request",
                status_code=400
            )

    result = await db.execute(select(Section).filter(Section.venue_id == data.venue_id))
    sections = result.scalars().all()

    if len(sections) != len(eventSections):
        raise HTTPException(
            detail="Bad request",
            status_code=400
        )
    sectionIds = {section.id for section in sections}
    if sectionIds != {section.id for section in eventSections}:
        raise HTTPException(
                detail="Invalid Request",
                status_code=400
            )

    for section in eventSections:
        if section.price <= 0:
            raise HTTPException(
                detail="Invalid Request",
                status_code=400
            )

    newEvent = Event(
        name = data.name,
        description = data.description,
        display_image = data.display_image,
        venue_id = data.venue_id,
        created_by = user.id,
        event_on = data.event_on
    )
    try:
        db.add(newEvent)
        await db.flush()

        newEventSections = []
        newEventSeats = []
        for section in eventSections:
            newEventSection = EventSection(
                event_id = newEvent.id,
                section_id = section.id,
                price = section.price
            )

            result = await db.execute(select(Seat).filter(Seat.section_id == section.id))
            seats = result.scalars().all()

            for seat in seats:
                newEventSeat = EventSeat(
                    event_id = newEvent.id,
                    seat_id = seat.id,
                )
                newEventSeats.append(newEventSeat)
            newEventSections.append(newEventSection)

        db.add_all(newEventSeats)
        db.add_all(newEventSections)

        await db.commit()
    except:
        await db.rollback()
        raise

    return {
        "message": "event creation successful",
        "status": 201
    }

@router.patch("/update/{eventId}")
async def updateEvent(eventId: int, data: EventReq, db: AsyncSession = Depends(getDb), user: User = Depends(getCurrentUser)):
    result = await db.execute(select(Event).filter(Event.id == eventId, Event.created_by == user.id))
    existingEvent = result.scalars().first()

    if not existingEvent or existingEvent.created_by != user.id:
        raise HTTPException(
            detail="event does not exists",
            status_code=400
        )

    existingEvent.name = data.name
    existingEvent.description = data.description
    existingEvent.display_image = data.display_image
    existingEvent.event_on = data.event_on

    await db.commit()
    await db.refresh(existingEvent)

    return {
        "data": existingEvent,
        "message": "event update successful",
        "status": 200
    }

@router.get("/{eventId}/dashboard")
async def getEventData(eventId: int, db: AsyncSession = Depends(getDb), user: User = Depends(getCurrentUser)):
    stmt = (
        select(Event)
        .where(Event.id == eventId)
    )
    result = await db.execute(stmt)
    existingEvent = result.scalar_one_or_none()

    if not existingEvent:
        raise HTTPException(
            detail="event not found",
            status_code=404
        )

    stmt = (
        select(
            EventSeat.status,
            Section.name,
            Section.tier,
            EventSection.price
        )
        .select_from(EventSeat)
        .outerjoin(
            Seat,
            Seat.id == EventSeat.seat_id
        )
        .outerjoin(
            Section,
            Section.id == Seat.section_id
        )
        .outerjoin(
            EventSection,
            and_(EventSection.section_id == Section.id,
            EventSection.event_id == EventSeat.event_id)
        )
        .where(
            EventSeat.event_id == existingEvent.id
        )
        .order_by(Section.tier)
    )
    result = await db.execute(stmt)
    data = result.all()
    seats = [
        dict(row._mapping)
        for row in data
    ]

    bookedSeats = 0
    pendingSeats = 0
    section_wise = {}
    for seat in seats:
        if seat["status"] == SeatStatus.HELD:
            pendingSeats += 1
        if seat["tier"] not in section_wise:
            section_wise[seat["tier"]] = SectionWiseStat(
                name=seat["name"],
                tier=seat["tier"],
                price=seat["price"]
            )
        section_wise[seat["tier"]].capacity += 1
        if seat["status"] == SeatStatus.SOLD:
            section_wise[seat["tier"]].revenue += seat["price"]
            section_wise[seat["tier"]].sold += 1
            bookedSeats += 1
        if seat["status"] == SeatStatus.AVAILABLE:
            section_wise[seat["tier"]].available += 1
        

    stmt = (
        select(Booking)
        .where(
            Booking.event_id == existingEvent.id
        )
    )
    result = await db.execute(stmt)
    bookings = result.scalars().all()

    all_total_amount = sum(booking.total_amount for booking in bookings if booking.status == BookingStatus.CONFIRMED)

    days_since_live = datetime.now(timezone.utc).date() - existingEvent.created_at.date()
    booking_health = { "total": len(bookings) }
    for bookingStatus in BookingStatus:
        booking_health[bookingStatus.value] = 0
    for booking in bookings:
        booking_health[booking.status] += 1

    stmt = (
        select(
            Booking.status,
            Booking.created_at
        )
        .select_from(BookingSeat)
        .outerjoin(
            Booking,
            Booking.id == BookingSeat.booking_id
        )
        .where(
            Booking.event_id == existingEvent.id,
            Booking.status == BookingStatus.CONFIRMED
        )
        .order_by(Booking.created_at)
    )
    result = await db.execute(stmt)
    bookingSeats = result.all()

    sales_trend = {}
    for seat in bookingSeats:
        days_passed = (seat.created_at.date() - existingEvent.created_at.date()).days + 1
        if seat.status == BookingStatus.CONFIRMED:
            if days_passed not in sales_trend:
                sales_trend[days_passed] = 0
            sales_trend[days_passed] += 1


    return {
        "data": {
            "total_seats": len(seats),
            "booked_seats": bookedSeats,
            "held_seats": pendingSeats,
            "available_seats": len(seats) - bookedSeats - pendingSeats,
            "total_revenue": all_total_amount,
            "days_since_live": days_since_live.days + 1,
            "days_booked_since_live": sales_trend,
            "booking_health": booking_health,
            "section_wise": section_wise
        },
        "message": "get booking details successful",
        "status": 200
    }

