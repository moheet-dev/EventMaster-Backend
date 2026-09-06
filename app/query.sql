CREATE TABLE users(
	id SERIAL PRIMARY KEY,
	username VARCHAR(50) UNIQUE NOT NULL,
	email VARCHAR(255) UNIQUE NOT NULL,
	password TEXT NOT NULL,
	created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE venues(
	id SERIAL PRIMARY KEY,
	name VARCHAR(250) NOT NULL,
	address TEXT NOT NULL,
	display_image TEXT,
	created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE events(
	id SERIAL PRIMARY KEY,
	name VARCHAR(100) NOT NULL,
	description TEXT NOT NULL,
	display_image TEXT,
	created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
	venue_id INT REFERENCES venues(id) ON UPDATE CASCADE ON DELETE SET NULL
);

CREATE TABLE sections(
	id SERIAL PRIMARY KEY,
	name VARCHAR(100) NOT NULL,
	tier INT NOT NULL,
	venue_id INT NOT NULL REFERENCES venues(id) ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE seats(
	id SERIAL PRIMARY KEY,
	code VARCHAR(100) NOT NULL,
	row_number INT NOT NULL,
	section_id INT NOT NULL REFERENCES sections(id) ON UPDATE CASCADE ON DELETE CASCADE,
	UNIQUE(section_id, code)
);

CREATE TYPE seat_status AS ENUM(
	'AVAILABLE',
	'HELD',
	'SOLD'
);

CREATE TABLE event_seats(
	event_id INT NOT NULL REFERENCES events(id) ON UPDATE CASCADE ON DELETE CASCADE,
	seat_id INT NOT NULL REFERENCES seats(id) ON UPDATE CASCADE ON DELETE CASCADE,
	status seat_status NOT NULL DEFAULT 'AVAILABLE',
	timeout_at TIMESTAMPTZ,

	PRIMARY KEY(event_id, seat_id)
);

CREATE TABLE event_sections(
	event_id INT NOT NULL REFERENCES events(id) ON UPDATE CASCADE ON DELETE CASCADE,
	section_id INT NOT NULL REFERENCES sections(id) ON UPDATE CASCADE ON DELETE CASCADE,
	price NUMERIC(10, 2) NOT NULL CHECK (price > 0),

	PRIMARY KEY(event_id, section_id)
);

CREATE INDEX idx_events_name_venue
ON events(name, venue_id);


ALTER TABLE venues
ADD COLUMN created_by INT REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE;


ALTER TABLE events
ADD COLUMN created_by INT REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE;

ALTER TABLE events
ADD COLUMN event_on TIMESTAMPTZ NOT NULL;

CREATE TYPE booking_status AS ENUM(
	'PENDING',
	'CONFIRMED',
	'CANCELLED',
	'EXPIRED'
);

CREATE TABLE bookings(
	id SERIAL PRIMARY KEY,
	user_id INT NOT NULL REFERENCES users(id) ON DELETE RESTRICT ON UPDATE CASCADE,
	event_id INT NOT NULL REFERENCES events(id) ON DELETE RESTRICT ON UPDATE CASCADE,
	total_amount NUMERIC(10, 2) NOT NULL CHECK (total_amount > 0),
	status booking_status NOT NULL DEFAULT 'PENDING',
	created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE booking_seats(
	booking_id INT NOT NULL REFERENCES bookings(id) ON DELETE RESTRICT ON UPDATE CASCADE,
	seat_id INT NOT NULL REFERENCES seats(id) ON DELETE RESTRICT ON UPDATE CASCADE,
	price NUMERIC(10, 2) NOT NULL CHECK (price > 0),
	PRIMARY KEY(booking_id, seat_id)
);

ALTER TABLE bookings
ADD COLUMN order_id TEXT UNIQUE;

ALTER TABLE bookings
ADD COLUMN payment_id TEXT UNIQUE;



















-- =========================================================
-- 1. USER
-- =========================================================

INSERT INTO users (username, email, password)
VALUES (
    'moheet',
    'moheet@example.com',
    '$argon2id$v=19$m=65536,t=3,p=4$5RJ+6zeeuyGwFGHt9ak72g$vd0px3/blxJw8pvledi8J5j4utY48p5Q6Xw/PKirTi0'
);


-- =========================================================
-- 2. VENUES
-- =========================================================

INSERT INTO venues (name, address, display_image, created_by)
VALUES
(
    'NCPA',
    'Nariman Point, Mumbai',
    'https://images.unsplash.com/photo-1492684223066-81342ee5ff30',
    1
),
(
    'Jio World Convention Centre',
    'Bandra Kurla Complex, Mumbai',
    'https://images.unsplash.com/photo-1540575467063-178a50c2df87',
    1
),
(
    'Wankhede Stadium',
    'Churchgate, Mumbai',
    'https://images.unsplash.com/photo-1471295253337-3ceaaedca402',
    1
);


-- =========================================================
-- 3. EVENTS
-- =========================================================

INSERT INTO events
(
    name,
    description,
    display_image,
    venue_id,
    created_by,
    event_on
)
VALUES
(
    'Mumbai Music Festival 2026',
    'A live music festival featuring some of the best artists and performers.',
    'https://images.unsplash.com/photo-1501386761578-eac5c94b800a',
    1,
    1,
    '2026-09-20 19:00:00+05:30'
),
(
    'Tech India Summit 2026',
    'A technology conference featuring talks on AI, cloud computing, robotics and software engineering.',
    'https://images.unsplash.com/photo-1540575467063-178a50c2df87',
    2,
    1,
    '2026-10-10 10:00:00+05:30'
),
(
    'Mumbai Premier League Final',
    'The grand final of the Mumbai Premier League.',
    'https://images.unsplash.com/photo-1540747913346-19e32dc3e97e',
    3,
    1,
    '2026-09-28 18:30:00+05:30'
);


-- =========================================================
-- 4. SECTIONS
-- =========================================================

-- NCPA / Music Festival
INSERT INTO sections (name, tier, venue_id)
VALUES
('VIP', 1, 1),
('Premium', 2, 1),
('Regular', 3, 1);

-- Jio World / Tech Summit
INSERT INTO sections (name, tier, venue_id)
VALUES
('VIP', 1, 2),
('Premium', 2, 2),
('Regular', 3, 2);

-- Wankhede / Cricket
INSERT INTO sections (name, tier, venue_id)
VALUES
('VIP', 1, 3),
('Premium', 2, 3),
('Regular', 3, 3);


-- =========================================================
-- 5. SEATS
-- =========================================================

-- NCPA
INSERT INTO seats (code, row_number, section_id)
VALUES
('A1', 1, 1),
('A2', 1, 1),
('A3', 1, 1),
('A4', 1, 1),
('B1', 2, 1),
('B2', 2, 1),
('B3', 2, 1),
('B4', 2, 1),

('A1', 1, 2),
('A2', 1, 2),
('A3', 1, 2),
('A4', 1, 2),
('B1', 2, 2),
('B2', 2, 2),
('B3', 2, 2),
('B4', 2, 2),

('A1', 1, 3),
('A2', 1, 3),
('A3', 1, 3),
('A4', 1, 3),
('B1', 2, 3),
('B2', 2, 3),
('B3', 2, 3),
('B4', 2, 3);


-- Jio World
INSERT INTO seats (code, row_number, section_id)
VALUES
('A1', 1, 4),
('A2', 1, 4),
('A3', 1, 4),
('A4', 1, 4),
('B1', 2, 4),
('B2', 2, 4),
('B3', 2, 4),
('B4', 2, 4),

('A1', 1, 5),
('A2', 1, 5),
('A3', 1, 5),
('A4', 1, 5),
('B1', 2, 5),
('B2', 2, 5),
('B3', 2, 5),
('B4', 2, 5),

('A1', 1, 6),
('A2', 1, 6),
('A3', 1, 6),
('A4', 1, 6),
('B1', 2, 6),
('B2', 2, 6),
('B3', 2, 6),
('B4', 2, 6);


-- Wankhede
INSERT INTO seats (code, row_number, section_id)
VALUES
('A1', 1, 7),
('A2', 1, 7),
('A3', 1, 7),
('A4', 1, 7),
('B1', 2, 7),
('B2', 2, 7),
('B3', 2, 7),
('B4', 2, 7),

('A1', 1, 8),
('A2', 1, 8),
('A3', 1, 8),
('A4', 1, 8),
('B1', 2, 8),
('B2', 2, 8),
('B3', 2, 8),
('B4', 2, 8),

('A1', 1, 9),
('A2', 1, 9),
('A3', 1, 9),
('A4', 1, 9),
('B1', 2, 9),
('B2', 2, 9),
('B3', 2, 9),
('B4', 2, 9);


-- =========================================================
-- 6. EVENT SECTIONS
-- =========================================================

-- Music Festival
INSERT INTO event_sections (event_id, section_id, price)
VALUES
(1, 1, 5000.00),
(1, 2, 3000.00),
(1, 3, 1500.00);

-- Tech Summit
INSERT INTO event_sections (event_id, section_id, price)
VALUES
(2, 4, 4000.00),
(2, 5, 2500.00),
(2, 6, 1000.00);

-- Cricket
INSERT INTO event_sections (event_id, section_id, price)
VALUES
(3, 7, 10000.00),
(3, 8, 5000.00),
(3, 9, 2000.00);


-- =========================================================
-- 7. EVENT SEATS
-- =========================================================

-- Event 1: Music Festival
INSERT INTO event_seats (event_id, seat_id)
SELECT 1, id
FROM seats
WHERE section_id IN (1, 2, 3);

-- Event 2: Tech Summit
INSERT INTO event_seats (event_id, seat_id)
SELECT 2, id
FROM seats
WHERE section_id IN (4, 5, 6);

-- Event 3: Cricket
INSERT INTO event_seats (event_id, seat_id)
SELECT 3, id
FROM seats
WHERE section_id IN (7, 8, 9);