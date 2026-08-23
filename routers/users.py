from fastapi import APIRouter, Depends, HTTPException
from schemas.schema import UserReq, LoginReq
from pwdlib import PasswordHash
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from dependency.dependency import getDb
from models.models import User
from helpers.helper import createAccessToken

password_hash = PasswordHash.recommended()

router = APIRouter()

@router.get("/")
def getAllUsers():
    return {}


@router.post("/register")
async def registerUser(data: UserReq, db: AsyncSession = Depends(getDb)):
    result = await db.execute(
        select(User).filter((User.email == data.email) | (User.username == data.username))
    )
    existingUser = result.scalars().first()

    if existingUser:
        raise HTTPException(
            detail="user already exists",
            status_code=409
        )
    hashedPassword = password_hash.hash(data.password)
    user = User(
        username=data.username,
        email=data.email,
        password=hashedPassword
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return {
        "data": {
            "token": createAccessToken(user.id)
        },
        "message": "user registration successful",
        "status": 201
    }

@router.post("/login")
async def loginUser(data: LoginReq, db: AsyncSession = Depends(getDb)):
    result = await db.execute(
        select(User).filter((User.email == data.identifier) | (User.username == data.identifier))
    )
    existingUser = result.scalars().first()

    if not existingUser or not password_hash.verify(data.password, existingUser.password):
        raise HTTPException(
            detail="username or password is incorrect",
            status_code=400
        )

    return {
        "data": {
            "token": createAccessToken(existingUser.id)
        },
        "message": "user login successful",
        "status": 200
    }

@router.post("/{user_id}")
def getUser():
    return {}
