from database.database import SessionLocal
from fastapi.security import OAuth2PasswordBearer
import jwt
from fastapi import Depends, HTTPException
import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")
SECRET_KEY=os.getenv("SECRET_KEY")
ALGORITHM=os.getenv("ALGORITHM")

async def getDb():
    async with SessionLocal() as db:
        yield db

async def getCurrentUser(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(getDb)):
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        userId = int(payload["sub"])
        if userId is None:
            raise HTTPException(
                detail="unauthenticated",
                status_code=401
            )
    except:
        raise HTTPException(
                detail="unauthenticated",
                status_code=401
            )

    result = await db.execute(select(User).filter(User.id == userId))
    existingUser = result.scalars().first()

    if not existingUser:
        raise HTTPException(
                detail="unauthenticated",
                status_code=401
            )

    return existingUser