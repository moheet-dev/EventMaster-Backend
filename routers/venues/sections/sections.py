from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import aliased
from models.models import User, Venue, Section, Seat
from schemas.schema import SectionReq, SectionModel
from dependency.dependency import getDb, getCurrentUser
from routers.venues.sections.seats.seats import seat_router

section_router = APIRouter()

section_router.include_router(
    seat_router,
    prefix="/{sectionId}",
    tags=["Seats"]
)


@section_router.get("")
async def getAllSections(venueId: int, db: AsyncSession = Depends(getDb), user: User = Depends(getCurrentUser)):
    result = await db.execute(select(Venue).filter(Venue.id == venueId))
    existingVenue = result.scalars().first()

    if not existingVenue or existingVenue.created_by != user.id:
        raise HTTPException(
            detail="venue does not exists",
            status_code=400
        )

    stmt = (
        select(
            Section.id,
            Section.name,
            Section.tier,
            Section.venue_id,
            func.count(Seat.id).label("seat_count")
        )
        .outerjoin(
            Seat,
            Section.id == Seat.section_id
        )
        .filter(
            Section.venue_id == venueId
        )
        .group_by(
            Section.id,
            Section.name,
            Section.tier,
            Section.venue_id
        )
        .order_by(
            Section.tier
        )
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


@section_router.post("/add-section")
async def addSection(venueId: int, data: SectionReq, db: AsyncSession = Depends(getDb), user: User = Depends(getCurrentUser)):
    result = await db.execute(select(Venue).filter(Venue.id == venueId))
    existingVenue = result.scalars().first()

    if not existingVenue or existingVenue.created_by != user.id:
        raise HTTPException(
            detail="venue does not exists",
            status_code=400
        )

    result = await db.execute(select(func.count()).select_from(Section).filter(Section.venue_id == venueId))
    currentSectionCount = result.scalar()

    section = Section(
        name = data.name,
        venue_id = venueId,
        tier = currentSectionCount + 1
    )

    db.add(section)
    await db.commit()

    return {
        "message": "section creation successful",
        "status": 200
    }

@section_router.post("/{sectionId}/update-section")
async def updateSection(venueId: int, sectionId: int, data: SectionReq, db: AsyncSession = Depends(getDb), user: User = Depends(getCurrentUser)):
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
    
    existingSection.name = data.name

    await db.commit()

    return {
        "message": "section update successful",
        "status": 200
    }


@section_router.patch("/update-tier")
async def updateSectionTier(venueId: int, updatedSections: list[SectionModel], db: AsyncSession = Depends(getDb), user: User = Depends(getCurrentUser)):
    result = await db.execute(select(Venue).filter(Venue.id == venueId, Venue.created_by == user.id))
    existingVenue = result.scalars().first()

    if not existingVenue or existingVenue.created_by != user.id:
        raise HTTPException(
            detail="venue does not exists",
            status_code=400
        )
    
    result = await db.execute(select(func.count()).select_from(Section).filter(Section.venue_id == venueId))
    numberOfSections = result.scalar()

    if numberOfSections != len(updatedSections):
        raise HTTPException(
            detail="Bad request",
            status_code=400
        )
    
    result = await db.execute(select(Section).filter(Section.venue_id == venueId))
    sections = result.scalars().all()

    section_map = {
        section.id: section
        for section in sections
    }

    checkSection = [0]*numberOfSections
    for updatedSection in updatedSections:
        section = section_map.get(updatedSection.id)
        if not section or updatedSection.tier < 1 or updatedSection.tier > numberOfSections or checkSection[updatedSection.tier - 1] == 1:
            raise HTTPException(
                detail="Bad request",
                status_code=400
            )
        checkSection[updatedSection.tier - 1] = 1
        section.tier = updatedSection.tier

    await db.commit()

    return {
        "message": "section tier update successful",
        "status": 200
    }
