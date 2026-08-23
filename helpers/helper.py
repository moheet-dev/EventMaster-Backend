import jwt
import os
from datetime import datetime, timezone, timedelta
import cloudinary
import cloudinary.utils
import time
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from models.models import EventSeat, SeatStatus
from database.database import SessionLocal
from datetime import datetime, timezone

lock_async = asyncio.Lock()
section_locks: dict[int, asyncio.Lock] = {}

SECRET_KEY=os.getenv("SECRET_KEY")
ALGORITHM=os.getenv("ALGORITHM")
CLOUDINARY_CLOUD_NAME=os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY=os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET=os.getenv("CLOUDINARY_API_SECRET")
CLOUDINARY_UPLOAD_FOLDER=os.getenv("CLOUDINARY_UPLOAD_FOLDER")

cloudinary.config(
    cloud_name = CLOUDINARY_CLOUD_NAME,
    api_key = CLOUDINARY_API_KEY,
    api_secret = CLOUDINARY_API_SECRET,
)

def createAccessToken(userId: int):
    expire = datetime.now(timezone.utc) + timedelta(days=1)

    payload = {
        "sub": str(userId),
        "exp": expire
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

def createUploadSignature():
    timestamp = int(time.time())
    params = {
        "timestamp": timestamp
    }
    signature = cloudinary.utils.api_sign_request(
        params_to_sign=params,
        api_secret=CLOUDINARY_API_SECRET
    )

    return {
        "signature": signature,
        "timestamp": timestamp,
        "api_key": CLOUDINARY_API_KEY,
        "cloud_name": CLOUDINARY_CLOUD_NAME
    }

async def update_seats():
    while True:
        try:
            async with SessionLocal() as db:
                stmt = (
                    update(EventSeat)
                    .where(
                        EventSeat.status == SeatStatus.HELD,
                        EventSeat.timeout_at < datetime.now(timezone.utc)
                    )
                    .values(
                        status = SeatStatus.AVAILABLE,
                        timeout_at = None
                    )
                )
                await db.execute(stmt)
                await db.commit()
        except:
            pass
        await asyncio.sleep(60)

async def get_section_lock(sectionId: int):
    async with lock_async:
        if sectionId not in section_locks:
            section_locks[sectionId] = asyncio.Lock()
        
        return section_locks[sectionId]