from fastapi import APIRouter, Depends, HTTPException, Query
from models.models import User, Event, EventSeat, EventSection, Seat, Venue, Section
from schemas.schema import EventReq, SectionReq
from dependency.dependency import getCurrentUser, getDb
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from math import ceil
from datetime import date, timedelta

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
    stmt = select(Event)

    if nameSearch is not None:
        stmt = stmt.filter(Event.name.ilike(f"%{nameSearch}%"))
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

    result = await db.execute(stmt.offset(offset).limit(limit))
    events = result.scalars().all()

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