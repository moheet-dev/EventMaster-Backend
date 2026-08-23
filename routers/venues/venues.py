from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.models import User, Venue
from schemas.schema import VenueReq, SectionReq
from dependency.dependency import getDb, getCurrentUser
from routers.venues.sections.sections import section_router

router = APIRouter()

router.include_router(
    section_router,
    prefix="/{venueId}",
    tags=["Sections"]
)


@router.get("")
async def getAllVenues(db: AsyncSession = Depends(getDb), user: User = Depends(getCurrentUser)):
    result = await db.execute(select(Venue))
    venues = result.scalars().all()

    return {
        "data": venues,
        "message": "all venue get successful",
        "status": 200
    }

@router.post("/add")
async def addVenue(data: VenueReq, db: AsyncSession = Depends(getDb), user: User = Depends(getCurrentUser)):
    venue = Venue(
        name = data.name,
        address = data.address,
        display_image = data.display_image,
        created_by = user.id
    )

    db.add(venue)
    await db.commit()

    return {
        "message": "venue creation successful",
        "status": 201
    }

@router.patch("/update/{venueId}")
async def updateVenue(venueId: int, data: VenueReq, db: AsyncSession = Depends(getDb), user: User = Depends(getCurrentUser)):
    result = await db.execute(select(Venue).filter(Venue.id == venueId))
    existingVenue = result.scalars().first()

    if not existingVenue or existingVenue.created_by != user.id:
        raise HTTPException(
            detail="venue does not exists",
            status_code=400
        )

    existingVenue.name = data.name
    existingVenue.address = data.address
    existingVenue.display_image = data.display_image

    await db.commit()
    await db.refresh(existingVenue)

    return {
        "data": existingVenue,
        "message": "venue update successful",
        "status": 200
    }