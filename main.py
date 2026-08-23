from dotenv import load_dotenv


load_dotenv()
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import users, all
from routers.venues import venues
from routers.events import events
from routers.bookings import bookings
from contextlib import asynccontextmanager
import asyncio
from helpers.helper import update_seats

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(
        update_seats()
    )
    yield
    task.cancel()

app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:4200"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_credentials=True,
    allow_headers=["*"]
)

@app.get("/")
def root():
    return {
        "message": "Server running",
        "status": 200
    }

app.include_router(
    all.router,
    prefix="/global",
    tags=["Global"]
)

app.include_router(
    users.router,
    prefix="/users",
    tags=["Users"]
)

app.include_router(
    venues.router,
    prefix="/venues",
    tags=["Venues"]
)

app.include_router(
    events.router,
    prefix="/events",
    tags=["Events"]
)

app.include_router(
    bookings.router,
    prefix="/bookings",
    tags=["Bookings"]
)