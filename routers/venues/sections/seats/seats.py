from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.models import User, Venue, Section, Seat
from schemas.schema import SeatReq
from dependency.dependency import getDb, getCurrentUser

seat_router = APIRouter()


@seat_router.get("")
async def getAllSeats(venueId: int, sectionId: int, db: AsyncSession = Depends(getDb), user: User = Depends(getCurrentUser)):
    result = await db.execute(select(Venue).filter(Venue.id == venueId))
    existingVenue = result.scalars().first()

    result = await db.execute(select(Section).filter(Section.id == sectionId, Section.venue_id == venueId))
    existingSection = result.scalars().first()

    if not existingVenue or existingVenue.created_by != user.id:
        raise HTTPException(
            detail="venue does not exists",
            status_code=400
        )
    if not existingSection:
        raise HTTPException(
            detail="section does not exists",
            status_code=400
        )

    result = await db.execute(
        select(Seat).filter(Seat.section_id == sectionId).order_by(Seat.row_number, Seat.code)
    )
    seats = result.scalars().all()

    rows = {}

    for seat in seats:
        if seat.row_number not in rows:
            rows[seat.row_number] = []
        rows[seat.row_number].append(seat.code)
    
    result_data = [
        {
            "row_number": row,
            "codes": codes
        }
        for row, codes in rows.items()
    ]

    return {
        "data": result_data,
        "message": "get all seat successful",
        "status": 200
    }


@seat_router.post("/add-seat")
async def addSeat(venueId: int, sectionId: int, data: SeatReq, db: AsyncSession = Depends(getDb), user: User = Depends(getCurrentUser)):
    result = await db.execute(select(Venue).filter(Venue.id == venueId))
    existingVenue = result.scalars().first()

    result = await db.execute(select(Section).filter(Section.id == sectionId, Section.venue_id == venueId))
    existingSection = result.scalars().first()

    if not existingVenue or existingVenue.created_by != user.id:
        raise HTTPException(
            detail="venue does not exists",
            status_code=400
        )
    if not existingSection:
        raise HTTPException(
            detail="section does not exists",
            status_code=400
        )
    
    if data.row_number < 1:
        raise HTTPException(
            detail="seat is invalid",
            status_code=400
        )
    
    seat = Seat(
        code = data.code,
        row_number = data.row_number,
        section_id = sectionId
    )

    db.add(seat)
    await db.commit()

    return {
        "message": "seat creation successful",
        "status": 200
    }
