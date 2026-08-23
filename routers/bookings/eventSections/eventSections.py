from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from models.models import User, Event, EventSection, Section, Seat, EventSeat
from dependency.dependency import getDb, getCurrentUser
from routers.bookings.eventSections.eventSeats.eventSeats import event_seats_router

event_section_router = APIRouter()

event_section_router.include_router(
    event_seats_router,
    prefix="/{sectionId}/seats"
)

@event_section_router.get("/")
async def getEventSections(eventId: int, db: AsyncSession = Depends(getDb), user: User = Depends(getCurrentUser)):
    result = await db.execute(select(Event).filter(Event.id == eventId))
    existingEvent = result.scalars().first()

    if not existingEvent:
        raise HTTPException(
            detail="event does not exists",
            status_code=400
        )

    stmt = (
        select(
            Section.id,
            Section.name,
            Section.tier,
            Section.venue_id,
            func.count(EventSeat.seat_id).label("seat_count"),
            EventSection.price
        )
        .select_from(EventSection)
        .outerjoin(
            Section,
            EventSection.section_id == Section.id
        )
        .outerjoin(
            Seat,
            EventSection.section_id == Seat.section_id
        )
        .outerjoin(
            EventSeat,
            (Seat.id == EventSeat.seat_id) &
            (EventSection.event_id == EventSeat.event_id)
        )
        .filter(EventSection.event_id == eventId)
        .group_by(
            Section.id,
            Section.name,
            Section.tier,
            Section.venue_id,
            EventSection.price
        )
        .order_by(Section.tier)
    )

    result = await db.execute(stmt)
    sections = result.all()

    data = [
        dict(row._mapping)
        for row in sections
    ]

    return {
        "data": data,
        "message": "get all section successful",
        "status": 200
    }