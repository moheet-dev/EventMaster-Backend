# 🎭 EventMaster — Backend API

A full-featured **event booking platform** backend built with **FastAPI** and **SQLAlchemy (async)**. EventMaster enables venue managers to set up venues, define sections/seats, create events, and lets users browse and book tickets with real-time seat holding and integrated **Razorpay** payment processing.

---

## 🚀 Tech Stack

| Layer | Technology |
|---|---|
| **Framework** | FastAPI (async) |
| **ORM** | SQLAlchemy (async) with `mapped_column` declarative style |
| **Database** | PostgreSQL (via async engine) |
| **Auth** | JWT (PyJWT) — Bearer token, 1-day expiry |
| **Password Hashing** | `pwdlib` (recommended hash) |
| **Payments** | Razorpay — order creation & signature verification |
| **Image Storage** | Cloudinary (signed upload flow) |
| **CORS** | Localhost:4200 + Vercel production origin |
| **Background Tasks** | `asyncio` task (seat-timeout cleanup loop) |

---

## 📁 Project Structure

```
eventmaster/
├── main.py                          # App entry point, router registration, lifespan
├── database/
│   └── database.py                  # Async SQLAlchemy engine + session factory
├── models/
│   └── models.py                    # All ORM models (User, Venue, Event, Booking …)
├── schemas/
│   └── schema.py                    # Pydantic request/response schemas
├── dependency/
│   └── dependency.py                # DB session + JWT auth dependency injection
├── helpers/
│   └── helper.py                    # JWT utils, Cloudinary signature, seat-timeout task
└── routers/
    ├── all.py                       # Global endpoints (upload signature)
    ├── users.py                     # Auth — register / login
    ├── venues/
    │   ├── venues.py                # Venue CRUD
    │   └── sections/
    │       ├── sections.py          # Section CRUD + tier management
    │       └── seats/
    │           └── seats.py         # Seat CRUD
    ├── events/
    │   └── events.py                # Event CRUD with search/pagination
    └── bookings/
        ├── bookings.py              # Booking flow + payment verify + history
        └── eventSections/
            ├── eventSections.py     # Event section listing with live availability
            └── eventSeats/
                └── eventSeats.py   # Per-section seat map with real-time status
```

---

## 🗄️ Data Model

```mermaid
erDiagram
    User {
        int id PK
        string username
        string email
        string password
        datetime created_at
    }

    Venue {
        int id PK
        string name
        text address
        text display_image
        int created_by FK
        datetime created_at
    }

    Section {
        int id PK
        string name
        int tier
        int venue_id FK
    }

    Seat {
        int id PK
        string code
        int row_number
        int section_id FK
    }

    Event {
        int id PK
        string name
        text description
        text display_image
        int venue_id FK
        int created_by FK
        datetime event_on
        datetime created_at
    }

    EventSection {
        int event_id FK
        int section_id FK
        decimal price
    }

    EventSeat {
        int event_id FK
        int seat_id FK
        enum status
        datetime timeout_at
    }

    Booking {
        int id PK
        int user_id FK
        int event_id FK
        decimal total_amount
        enum status
        string order_id
        string payment_id
        datetime created_at
    }

    BookingSeat {
        int booking_id FK
        int seat_id FK
        decimal price
    }

    User ||--o{ Venue : "creates"
    User ||--o{ Event : "creates"
    User ||--o{ Booking : "makes"
    Venue ||--o{ Section : "has"
    Venue ||--o{ Event : "hosts"
    Section ||--o{ Seat : "contains"
    Section ||--o{ EventSection : "priced in"
    Event ||--o{ EventSection : "has sections"
    Event ||--o{ EventSeat : "tracks seats"
    Event ||--o{ Booking : "booked via"
    Seat ||--o{ EventSeat : "tracked as"
    Seat ||--o{ BookingSeat : "appears in"
    Booking ||--o{ BookingSeat : "contains"
```

### Enums

| Enum | Values |
|---|---|
| `SeatStatus` | `AVAILABLE` · `HELD` · `SOLD` |
| `BookingStatus` | `PENDING` · `CONFIRMED` · `CANCELLED` · `EXPIRED` |

---

## 🔑 Features In Detail

### 1. Authentication

All protected endpoints require a `JWT Bearer` token in the `Authorization` header. Tokens are issued at registration and login and expire after **24 hours**.

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/users/register` | ❌ | Register a new user. Returns JWT. |
| `POST` | `/users/login` | ❌ | Login with email/username + password. Returns JWT. |

- Passwords are hashed using `pwdlib` with a recommended algorithm.
- Login accepts either **username or email** as the identifier.
- Duplicate username or email returns `409 Conflict`.

---

### 2. Venue Management

Venues are physical locations that host events. Only the **creator** of a venue can manage it.

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/venues` | ✅ | List all venues. |
| `POST` | `/venues/add` | ✅ | Create a new venue. |
| `PATCH` | `/venues/update/{venueId}` | ✅ | Update venue details (owner only). |

**Venue fields:** `name`, `address`, `display_image` (Cloudinary URL)

---

### 3. Section Management

A venue is divided into **sections** (e.g., VIP, General, Balcony). Sections have a tiered ordering system for pricing priority.

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/venues/{venueId}` | ✅ | List all sections with seat counts, ordered by tier. |
| `POST` | `/venues/{venueId}/add-section` | ✅ | Add a section (tier auto-increments). |
| `POST` | `/venues/{venueId}/{sectionId}/update-section` | ✅ | Rename a section. |
| `PATCH` | `/venues/{venueId}/update-tier` | ✅ | Reorder section tiers (full list must be provided). |

- Only the **venue owner** can manage sections.
- Tier values must be unique, sequential, and within bounds.

---

### 4. Seat Management

Each section contains physical **seats** identified by a row number and a code (e.g., `A`, `B`, `C`).

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/venues/{venueId}/{sectionId}` | ✅ | List all seats grouped by row. |
| `POST` | `/venues/{venueId}/{sectionId}/add-seat` | ✅ | Add a seat to a section. |

- Response groups seats as `{ row_number: [code1, code2, …] }`.
- `row_number` must be ≥ 1.

---

### 5. Event Management

Events are tied to a specific venue. When an event is created, the system **automatically instantiates `EventSeat` records** for every seat in the venue (status: `AVAILABLE`), and creates `EventSection` pricing records.

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/events` | ✅ | List events with search filters and pagination. |
| `GET` | `/events/{eventId}` | ✅ | Get a single event by ID. |
| `POST` | `/events/add` | ✅ | Create an event (venue owner only). |
| `PATCH` | `/events/update/{eventId}` | ✅ | Update event metadata. |

**Search / Filter parameters for `GET /events`:**

| Parameter | Type | Description |
|---|---|---|
| `nameSearch` | `string` | Case-insensitive partial match on event name |
| `venueSearch` | `int` | Filter by venue ID |
| `from_date` | `date` | Events on or after this date |
| `to_date` | `date` | Events on or before this date |
| `page` | `int` (≥1) | Pagination page number (default: 1) |
| `limit` | `int` (1–100) | Results per page (default: 10) |

**Event creation rules:**
- The caller must be the **venue owner**.
- A pricing entry (`SectionReq` with `price > 0`) must be supplied for **every section** of the venue — no more, no less.
- On success, `EventSeat` rows are bulk-inserted for all seats, and `EventSection` rows record per-section pricing.

---

### 6. Booking Flow

The booking system uses **per-section asyncio locks** to prevent race conditions when multiple users try to book the same seats simultaneously.

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant API as EventMaster API
    participant DB as PostgreSQL
    participant RZP as Razorpay

    User->>API: POST /bookings/book {event_id, section_id, seats[]}
    API->>DB: Validate event + section exist
    API->>API: Acquire per-section asyncio lock
    API->>DB: SELECT EventSeats FOR UPDATE (pessimistic lock)
    API->>DB: Check all requested seats are AVAILABLE
    API->>DB: Set seat status to HELD, timeout_at = now+5min
    API->>DB: Create Booking record (status=PENDING)
    API->>DB: Create BookingSeat records
    API->>RZP: Create Razorpay order (amount in paise)
    API-->>User: { order_id, amount }

    User->>RZP: Complete payment in frontend
    RZP-->>User: { order_id, payment_id, signature }

    User->>API: POST /bookings/book/verify {order_id, payment_id, signature}
    API->>RZP: Verify HMAC payment signature
    API->>DB: Update Booking status to CONFIRMED
    API->>DB: Update EventSeat status to SOLD, clear timeout_at
    API-->>User: { message: "payment verified successfully" }
```

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/bookings/book` | ✅ | Initiate booking + create Razorpay order |
| `POST` | `/bookings/book/verify` | ✅ | Verify payment signature + confirm booking |
| `GET` | `/bookings` | ✅ | List all **confirmed** bookings for the logged-in user |
| `GET` | `/bookings/{bookingId}` | ✅ | Get seat details for a specific booking |

**Booking rules:**
- Seats are `HELD` for exactly **5 minutes** after a booking is initiated.
- If payment is not verified within 5 minutes, the background cleanup task resets them to `AVAILABLE`.
- A per-section asyncio lock ensures **atomic seat selection** — no double-booking is possible.
- Payment signature is verified using Razorpay HMAC before any DB state is changed.

---

### 7. Event Sections & Seat Map (Booking UI Endpoints)

These endpoints power the seat selection UI:

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/bookings/{eventId}/sections/` | ✅ | Get all sections for an event with pricing and seat counts |
| `GET` | `/bookings/{eventId}/sections/{sectionId}/seats` | ✅ | Get real-time seat map for a section |

**Seat map response format:**
```json
{
  "data": {
    "1": [
      { "seat_id": 1, "code": "A", "status": "AVAILABLE", "timeout_at": null },
      { "seat_id": 2, "code": "B", "status": "HELD", "timeout_at": "2026-08-26T18:25:00Z" }
    ],
    "2": [
      { "seat_id": 3, "code": "A", "status": "SOLD", "timeout_at": null }
    ]
  }
}
```

Seats are grouped by `row_number` and ordered by `row_number ASC, code ASC`.

---

### 8. Image Upload (Cloudinary Signed Upload)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/global/upload-signature` | ✅ | Generate a signed Cloudinary upload signature |

Returns `{ signature, timestamp, api_key, cloud_name }` so the frontend can upload images directly to Cloudinary without exposing the API secret.

---

### 9. Background: Seat Timeout Cleanup

A persistent `asyncio` background task runs every **60 seconds** for the lifetime of the server process:

```mermaid
flowchart TD
    A([Server Start]) --> B["asyncio.create_task — update_seats"]
    B --> C{Every 60 seconds}
    C --> D["SELECT EventSeats WHERE status = HELD AND timeout_at < NOW()"]
    D --> E["UPDATE status to AVAILABLE, clear timeout_at"]
    E --> C
    F([Server Shutdown]) --> G[task.cancel]
```

This guarantees that seats held by users who never completed payment are automatically released, keeping seat availability accurate.

---

## 🔄 End-to-End Application Flow

```mermaid
flowchart TD
    subgraph Setup ["Venue and Event Setup - Admin / Creator"]
        A([Register or Login]) --> B[Create Venue]
        B --> C[Add Sections to Venue]
        C --> D[Add Seats to Each Section]
        D --> E["Create Event at Venue with per-section pricing"]
        E --> F[EventSeat rows auto-created for all seats]
    end

    subgraph Browse ["Browsing - Any Authenticated User"]
        G([Login]) --> H["GET /events — search and paginate"]
        H --> I["GET /events/eventId — event details"]
        I --> J["GET /bookings/eventId/sections — sections and prices"]
        J --> K["GET /bookings/eventId/sections/sectionId/seats — live seat map"]
    end

    subgraph Book ["Booking and Payment"]
        K --> L[User selects AVAILABLE seats]
        L --> M["POST /bookings/book — seats HELD for 5 min"]
        M --> N[Frontend opens Razorpay checkout]
        N --> O{Payment completed?}
        O -- Yes --> P["POST /bookings/book/verify — seats SOLD, booking CONFIRMED"]
        O -- No or Timeout --> Q[Background task resets seats to AVAILABLE]
    end

    subgraph History ["Booking History"]
        P --> R["GET /bookings — confirmed bookings list"]
        R --> S["GET /bookings/bookingId — seat details per booking"]
    end
```

---

## ⚙️ Environment Variables

Create a `.env` file in the project root with the following keys:

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@host:port/dbname

# JWT
SECRET_KEY=your_jwt_secret_key
ALGORITHM=HS256

# Cloudinary
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
CLOUDINARY_UPLOAD_FOLDER=your_upload_folder

# Razorpay
RAZORPAY_ID=your_razorpay_key_id
RAZORPAY_SECRET=your_razorpay_key_secret
```

---

## 🏃 Running Locally

```bash
# 1. Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the server
uvicorn main:app --reload

# 4. Open interactive API docs
# http://localhost:8000/docs
```

---

## 🔒 Security Notes

- All mutating endpoints require a valid JWT (checked via `getCurrentUser` dependency).
- Venue/section/seat mutations are restricted to the **resource creator** — checked at the handler level.
- Seat selection uses **pessimistic locking** (`SELECT … FOR UPDATE`) combined with **asyncio per-section locks** to prevent concurrent double-booking.
- Payment is never confirmed without verifying the **Razorpay HMAC signature** server-side.
- Cloudinary uploads are performed directly from the client using a **server-generated signed signature**, keeping the API secret server-side only.

---

## 🌐 Deployed Frontend

The CORS configuration allows requests from:
- `http://localhost:4200` (local Angular dev server)
- `https://event-master-ui-rouge.vercel.app` (production frontend on Vercel)
