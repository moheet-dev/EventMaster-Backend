from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.models import User, Event, EventSection, Section, Seat, EventSeat
from dependency.dependency import getDb, getCurrentUser

event_seats_router = APIRouter()

@event_seats_router.get("")
async def getEventSeats(eventId: int, sectionId: int, db: AsyncSession = Depends(getDb), user: User = Depends(getCurrentUser)):
    result = await db.execute(select(Event).filter(Event.id == eventId))
    existingEvent = result.scalars().first()

    if not existingEvent:
        raise HTTPException(
            detail="event does not exists",
            status_code=400
        )

    stmt = (
        select(
            Seat.row_number,
            EventSeat.status,
            EventSeat.timeout_at,
            EventSeat.seat_id,
            Seat.code
        )
        .select_from(EventSection)
        .join(
            Seat,
            Seat.section_id == EventSection.section_id
        )
        .join(
            EventSeat,
            (EventSeat.seat_id == Seat.id) &
            (EventSeat.event_id == EventSection.event_id)
        )
        .filter(
            EventSection.event_id == eventId,
            EventSection.section_id == sectionId
        )
        .order_by(Seat.row_number, Seat.code)
    )

    result = await db.execute(stmt)
    seats = result.all()

    res = {}
    for seat in seats:
        if seat.row_number not in res:
            res[seat.row_number] = []
        res[seat.row_number].append({
            "status": seat.status,
            "timeout_at": seat.timeout_at,
            "seat_id": seat.seat_id,
            "code": seat.code
        })

    return {
        "data": res,
        "message": "get all seats successful",
        "status": 200
    }