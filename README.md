# Library Seat & Study Room Reservation Portal

A real-time booking application for our school library. Students request
seats, whole tables, computers or the study room for their preferred schedule;
the Librarian approves or rejects each request; Student Assistants help with
daily operations; and an administrator manages accounts, seating and rules.

The system models the actual library: **one floor (First Floor)**, a **Reading
Hall with 15 tables of 6 chairs (90 seats)**, a **Computer Area with 4
computers**, and one study room.

- **Backend:** Django 6.1 + Django REST Framework (`backend/`)
- **Frontend:** React 19 + Vite 8, installable as a Progressive Web App (`frontend/`)
- **Database:** SQLite by default (PostgreSQL/MySQL through environment variables)

See [PROGRESS.md](PROGRESS.md) for what has been built and tested, and
[docs/Functional_Requirements.pdf](docs/Functional_Requirements.pdf) for the list of
functional requirements.

---

## 1. Quick start

You need **Python 3.12+** and **Node.js 20.19+** (or 22.12+). Use two terminals.

### Backend

```bash
cd backend

# Create and activate a virtual environment (skip if backend/venv already exists)
python -m venv venv
venv\Scripts\activate            # Windows
# source venv/bin/activate       # macOS / Linux

pip install -r requirements.txt

# Configuration: copy the example and set a secret key
copy .env.example .env           # Windows   (cp .env.example .env on macOS / Linux)
python -c "import secrets; print(secrets.token_urlsafe(50))"
# paste the printed value into .env as DJANGO_SECRET_KEY

python manage.py migrate
python manage.py setup_library   # the real layout: 15 tables / 90 seats / 4 computers
python manage.py seed_demo       # optional: demo accounts and sample reservations
python manage.py runserver
```

The API is now at `http://127.0.0.1:8000/api/`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**. Requests to `/api` are forwarded to the Django
server automatically, so no further setup is needed.

### Demo accounts

`python manage.py seed_demo` creates these (password for all: `LibraryDemo#2026`,
or choose your own with `--password`):

| Role | Email | Notes |
|---|---|---|
| Admin | `admin@library.edu` | Full access |
| Librarian | `librarian@library.edu` | May also manage seats |
| Librarian | `librarian2@library.edu` | Reservations only |
| Student Assistant | `assistant@library.edu` | Helps with check-ins and monitoring |
| Student | `student1@university.edu` ... `student24@university.edu` | |

The command also runs `setup_library` (see below), creates the study room if
there is none, and adds three weeks of past reservations so the reports have
data. Run it again during opening hours on the day of a demonstration and it
adds seats in use "right now" plus a few pending requests for the Librarian to
approve. It never duplicates existing data, and it does not change accounts
that already exist (for example, ones you have deactivated).

### The library layout

`python manage.py setup_library` makes the seating match the real library:

- First Floor only
- Reading Hall: tables 1-15, six chairs each, numbered `T01-1` ... `T15-6` (90 seats)
- Computer Area: `PC-1` ... `PC-4`
- one study room

Floors, zones, seats and rooms that are not part of this are **archived, not
deleted**: they disappear from every screen and report, but past reservations
that used them stay on record. The command is safe to run again; it changes
nothing once the layout is in place.

**Change these passwords, or do not seed, on anything other than your own machine.**

### Creating the Admin account yourself

Without the demo data, create the administrator with:

```bash
python manage.py createsuperuser
```

It asks for an email, first name, last name and password, and creates an
account with the **Admin** role. Sign in with it, then create Librarian and
Student Assistant accounts under **Users**. (Only students can register
themselves.)

---

## 2. Commands

| Task | Command (from the folder shown) |
|---|---|
| Install backend dependencies | `backend`: `pip install -r requirements.txt` |
| Create / update the database | `backend`: `python manage.py migrate` |
| Create the Admin account | `backend`: `python manage.py createsuperuser` |
| Set up the real seating layout | `backend`: `python manage.py setup_library` |
| Load demo data | `backend`: `python manage.py seed_demo` |
| Start the backend | `backend`: `python manage.py runserver` |
| Run backend tests | `backend`: `python manage.py test` |
| Process due reservations manually | `backend`: `python manage.py process_reservations` |
| Install frontend dependencies | `frontend`: `npm install` |
| Start the frontend (development) | `frontend`: `npm run dev` |
| Check code style | `frontend`: `npm run lint` |
| Build the frontend for production | `frontend`: `npm run build` (output in `frontend/dist/`) |
| Rebuild the functional requirements PDF | project root: `python docs/build_functional_requirements.py` (needs `pip install reportlab`) |
| Try the production build locally | `frontend`: `npm run preview` (http://localhost:4173) |

---

## 3. Environment variables

### Backend: `backend/.env` (template: `backend/.env.example`)

| Variable | Purpose | Default |
|---|---|---|
| `DJANGO_SECRET_KEY` | Signs tokens and cookies. **Required.** | none |
| `DJANGO_DEBUG` | `True` for local development only | `False` |
| `DJANGO_ALLOWED_HOSTS` | Hostnames the backend answers to | `localhost,127.0.0.1` |
| `LIBRARY_TIME_ZONE` | Time zone the library operates in | `Asia/Manila` |
| `CORS_ALLOWED_ORIGINS` | Frontend origins allowed to call the API directly | the Vite dev/preview URLs |
| `REFRESH_COOKIE_SECURE` | `True` when served over HTTPS | `False` with debug on |
| `REFRESH_COOKIE_SAMESITE` | SameSite policy of the login cookie | `Lax` |
| `ACCESS_TOKEN_MINUTES` / `REFRESH_TOKEN_DAYS` | Token lifetimes | `10` / `7` |
| `DB_ENGINE`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | Use another database | SQLite file |

### Frontend: `frontend/.env` (template: `frontend/.env.example`; optional)

| Variable | Purpose | Default |
|---|---|---|
| `VITE_API_BASE_URL` | Where the app sends API requests | `/api` |
| `VITE_BACKEND_ORIGIN` | Django server that `/api` is forwarded to in dev/preview | `http://127.0.0.1:8000` |
| `VITE_APP_NAME` | Name shown in the app and when installed | `LibReserve` |
| `VITE_INSTITUTION_NAME` | Shown under the app name | `University Library` |

The backend address is defined once, in these variables. No component contains a URL.

---

## 4. Installing the app (PWA)

The portal can be installed and opened like a native app.

- **Android (Chrome/Edge):** open the site, then menu > **Install app** (or use
  the **Install app** button in the sidebar or on the Profile page).
- **iPhone/iPad (Safari):** Share > **Add to Home Screen**.
- **Desktop (Chrome/Edge):** the install icon in the address bar, or the
  **Install app** button in the sidebar.

Things to know:

- Installation needs the **production build** (`npm run build` then
  `npm run preview`, or a real deployment). The development server does not
  register the service worker.
- Browsers only allow installation from `https://` or from `localhost`. To test
  on a phone over Wi-Fi you need HTTPS (for example a tunnelling tool), and the
  phone's address must be added to `DJANGO_ALLOWED_HOSTS`.
- **Offline behaviour:** the app itself opens without a connection and says
  clearly that it is offline. It never shows cached availability as if it were
  live, and it never pretends a reservation succeeded: creating, cancelling and
  checking in all require an answer from the server.

---

## 5. How it is organised

```text
ProjectManagement/
├── backend/
│   ├── config/            Project settings, URL root, shared permissions,
│   │                      error format, pagination, test fixtures
│   ├── users/             Accounts, roles, login/registration, account management
│   ├── library/           Floor, opening hours, closures, booking rules,
│   │                      the real seating layout (setup_library), seed_demo
│   ├── seats/             Zones, tables and seats, seat map availability
│   ├── study_rooms/       The study room and its facilities
│   ├── reservations/      Reservations and all booking rules (the core)
│   ├── notifications/     In-app notifications
│   ├── activity/          Audit log
│   ├── reports/           Dashboards and usage reports
│   ├── manage.py
│   └── requirements.txt
├── docs/                  Functional requirements (PDF, Markdown, generator)
└── frontend/
    ├── public/            Icons used by the installed app
    └── src/
        ├── components/
        │   ├── common/        Buttons, cards, forms, dialogs, tables, states
        │   ├── layout/        Sidebar, top bar, route guards
        │   ├── reservations/  Date/time picker, cards, actions, QR pass, timeline
        │   ├── seats/         Seat map, seat dialog, seat forms
        │   ├── rooms/         Room card, invite list
        │   └── dashboard/     Stat tiles, occupancy meter, charts
        ├── pages/
        │   ├── auth/          Login, registration
        │   ├── booking/       Seat map, room list, room page (all roles)
        │   ├── student/       Student dashboard, my reservations
        │   ├── librarian/     Operations dashboard, check-in desk, reservations,
        │   │                  reports, seat management
        │   ├── admin/         Dashboard, users, settings, activity log
        │   └── shared/        Reservation detail, notifications, profile
        ├── services/      The only place that calls the API
        ├── context/       Session, library information, toasts
        ├── hooks/         Data loading/polling, form drafts, actions
        ├── utils/         Dates, booking options, storage, constants
        ├── styles/        Design tokens and base styles
        ├── App.jsx        Route map
        └── main.jsx
```

Each backend app has its own models, serializers, views, URLs and tests. Booking
rules live in `reservations/services.py`, not in the views.

---

## 6. Roles

| | Student | Student Assistant | Librarian | Admin |
|---|:-:|:-:|:-:|:-:|
| Register themselves | yes | no | no | no |
| Request seats, tables, computers, the room; check in/out; cancel own | yes | - | - | - |
| See all reservations, the live seat map and who is seated | - | yes | yes | yes |
| Check students in and out | - | yes | yes | yes |
| **Approve or reject requests** | - | **no** | **yes** | yes |
| Cancel a student's reservation, mark no-shows, reserve for a student | - | no | yes | yes |
| View usage reports | - | no | yes | yes |
| Add/edit seats and tables, maintenance | - | no | if allowed by Admin | yes |
| Create and deactivate accounts (incl. Librarians, Student Assistants) | - | no | no | yes |
| Opening hours, closures, booking rules, activity log | - | no | no | yes |

Access is enforced **in the backend** on every request (`config/permissions.py`
and the reservation services). The frontend additionally hides pages a role
cannot use, but that is only for convenience.

---

## 7. How reservations work

### Statuses

```text
PENDING ──librarian approves──▶ CONFIRMED ──check in──▶ CHECKED IN ──▶ COMPLETED
   │                                │                      (check out or end time)
   ├── librarian rejects ─▶ REJECTED ├── cancelled ────▶ CANCELLED
   └── withdrawn, or not             └── no check-in ──▶ NO-SHOW
       reviewed in time ─▶ CANCELLED
```

- **Every request a student submits starts as Pending.** It is never Confirmed
  until a Librarian (or the Admin) approves it.
- Pending, Confirmed and Checked in all *hold* the requested places, so two
  students can never be waiting on the same seat. Any other status releases them.
- A request nobody reviews before its reserved time expires automatically (it
  is cancelled, the places are released, and it is not counted against the student).
- A reservation a Librarian enters on a student's behalf is Confirmed at once,
  because the person who approves is the one who made it.

### What can be requested

| Request | Reason required? |
|---|---|
| 1 or 2 seats | No |
| 3 to 5 seats | Yes |
| A whole table (6 seats) | Yes |
| 1 computer | No (only one computer per request, and per student at a time) |
| The study room | Purpose is optional |

One request covers at most six seats, all in the same area. The reason is shown
to the Librarian on the dashboard and on the request page.

### Notifications

| Event | Who is notified |
|---|---|
| Student submits a request | Every active Librarian and Admin, and the student (request received) |
| Librarian approves | The student (and classmates invited to the room) |
| Librarian rejects | The student, with the reason |
| Cancelled by staff, expired, no-show, reminder, checked in | The student |

Notifications are rows in the database, counted on the bell, and each one links
to its reservation.

### Rules checked by the server on every request

- Times are in 30-minute slots, inside opening hours, not on a closure day.
- Not in the past (the slot currently in progress may still be requested, for walk-ins).
- Within the advance-booking limit and the minimum/maximum duration.
- Every seat is in service and exists in the current layout; a room's group size fits its capacity.
- More than two seats needs a reason; computers are one at a time.
- The student is within their limits (active reservations, per day) and is not
  suspended for repeated no-shows.
- Every requested place is free for the whole time, and the student has no
  other reservation at the same time.

All limits are settings the Admin can change (Library Settings > Reservation rules).

### Why two people cannot get the same seat

1. The request runs inside a database transaction that checks for an
   overlapping pending or confirmed reservation on each seat before saving.
2. On top of that, every active reservation owns one row per seat per
   30-minute slot in the `ReservationSlot` table, which has a **unique
   constraint** on (seat, slot) and (room, slot). If two requests ever got past
   step 1 at the same instant, the database itself rejects the second one.

### Check-in, no-shows and automatic updates

- Check-in opens 10 minutes before the start and closes 15 minutes after
  (configurable; for a request approved late, the 15 minutes count from the
  approval). Students check in from the app; staff, including Student
  Assistants, can do it at the desk by typing or scanning the reservation code.
- A confirmed reservation nobody checks in to becomes a **no-show**: the place
  is released, the student is notified, and it counts towards the no-show limit.
- A checked-in reservation is completed automatically at its end time.
- These time-based changes are applied by a lightweight step that runs before
  API requests (at most every 10 seconds), so no background worker is needed.
  On a production server the same job can be scheduled instead:
  `python manage.py process_reservations`.

### Real-time updates

Availability screens re-fetch every 5 seconds while they are visible (and
immediately when the tab regains focus or the connection returns); dashboards
every 15 seconds. Polling was chosen over WebSockets because it needs no extra
server process or message broker and cannot silently disconnect. The server
remains the final judge: even if a screen were a few seconds old, a request
for a taken seat is refused.

---

## 8. Database design

| Model (app) | What it is | Key relationships |
|---|---|---|
| `User` (users) | One account table for all roles; `role` is admin, librarian, assistant or student | |
| `Floor` (library) | A level of the building (the library has one) | has many zones and study rooms |
| `OperatingHours` (library) | Opening hours for one weekday (7 rows) | |
| `Closure` (library) | A date the library is closed | |
| `ReservationPolicy` (library) | The booking rules (single row) | |
| `Zone` (seats) | A seating area: Reading Hall or Computer Area | belongs to a floor; has many seats |
| `Seat` (seats) | One chair or computer, with its table number, map position, features and status | belongs to a zone |
| `Facility` (study_rooms) | Equipment such as a whiteboard | many-to-many with rooms |
| `StudyRoom` (study_rooms) | The bookable room with capacity and status | belongs to a floor |
| `Reservation` (reservations) | A request by one student for a time range, with its status, the Librarian's decision and history timestamps | student -> User; decided_by -> User; room -> StudyRoom |
| `ReservationSeat` (reservations) | One seat of a seat reservation (1 to 6 per request) | reservation, seat |
| `ReservationSlot` (reservations) | One row per seat (or room) per 30-minute slot of an active reservation; the double-booking guard | reservation, seat/room, student |
| `ReservationParticipant` (reservations) | A classmate invited to a room reservation | reservation <-> User |
| `Notification` (notifications) | A message for one user | belongs to a user |
| `ActivityLog` (activity) | Who did what, and when | actor -> User (optional) |

Notable constraints:

- Unique (seat, slot), (room, slot) and (student, slot) on `ReservationSlot`.
- A reservation is for seats or for the room, never both, and must end after it starts.
- Unique seat number; unique (zone, row, column); unique room number; unique student ID and email.
- Seats sharing a `table_number` form one table (six chairs in the Reading Hall).
- `Floor`, `Zone`, `Seat` and `StudyRoom` have an `is_archived` flag. Records
  that have reservations are never deleted; they are archived (or, for
  accounts, deactivated), so history is always preserved.

Migrations added for the library revision: `library.0004`, `seats.0002`,
`study_rooms.0002`, `users.0002`, `reservations.0003` (schema) and
`reservations.0004` (copies each existing seat reservation into `ReservationSeat`).

---

## 9. Main API endpoints

All under `/api/`. Every endpoint except register, login, refresh, logout and
health requires `Authorization: Bearer <access token>`.

| Area | Endpoints |
|---|---|
| Auth | `POST auth/register/`, `POST auth/login/`, `POST auth/refresh/`, `POST auth/logout/`, `GET/PATCH auth/me/`, `POST auth/change-password/` |
| Users (admin) | `GET/POST users/`, `GET/PATCH users/{id}/`, `POST users/{id}/activate/`, `deactivate/`, `set-password/`; `GET users/students/` (staff), `GET users/lookup/` |
| Library | `GET library/overview/`, `GET/PUT library/hours/`, `GET/PATCH library/policy/`, `library/closures/`, `library/floors/` |
| Seats | `GET seats/availability/?date&start&end`, `GET seats/{id}/schedule/?date`, `seats/` and `seats/zones/` (CRUD), `POST seats/{id}/set-status/` |
| Study room | `GET study-rooms/availability/?date&start&end`, `GET study-rooms/{id}/schedule/?date`, `GET study-rooms/` |
| Reservations | `GET/POST reservations/` (`seats: [ids]` or `room`), `GET reservations/{id}/`, `POST reservations/{id}/approve/`, `reject/`, `cancel/`, `check-in/`, `check-out/`, `no-show/`; `GET reservations/lookup/?code`, `GET reservations/limits/` |
| Notifications | `GET notifications/`, `GET notifications/unread-count/`, `POST notifications/{id}/read/`, `POST notifications/read-all/`, `DELETE notifications/{id}/` |
| Reports | `GET reports/student-dashboard/`, `staff-dashboard/`, `admin-dashboard/`, `usage/?days=7|14|30|90` |
| Activity (admin) | `GET activity/` |

Errors always have the same shape:

```json
{ "error": { "code": "slot_taken", "message": "Seat T03-2 is already requested...", "fields": { } } }
```

Lists are paginated: `{ "count", "next", "previous", "results" }`.

---

## 10. Security and persistence notes

- **Login session.** The short-lived access token is kept only in the page's
  memory. The refresh token is an `HttpOnly` cookie that JavaScript cannot read,
  limited to the `/api/auth/` path. Nothing that grants access is stored in
  `localStorage`. Refreshing the page restores the session from the cookie, and
  an expired access token is renewed silently.
- **Page refresh.** Every page has its own URL, so refreshing, bookmarking and
  the back button keep you where you were. A signed-out visitor is sent to the
  login page and returned to the page they wanted afterwards.
- **Form drafts.** What you type into booking, registration, profile, account
  and settings forms is saved as you type and restored after a refresh. Drafts
  are stored per user, never include passwords, are cleared after a successful
  submit or cancel, and are all removed when you sign out.
- **Data.** Accounts, seats, rooms, reservations, notifications and logs live
  only in the Django database. The browser stores nothing but form drafts.
- Passwords are hashed and checked against Django's password validators;
  login and registration are rate-limited.

## 11. Deploying (outline)

1. Set `DJANGO_DEBUG=False`, a new `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`,
   `REFRESH_COOKIE_SECURE=True`, and a production database.
2. Serve Django with a production server (for example gunicorn or waitress).
3. `npm run build` and serve `frontend/dist/` as static files, sending unknown
   paths to `index.html` so that page URLs work on refresh.
4. Serve both from the same domain over HTTPS (frontend at `/`, API at `/api/`),
   or set `VITE_API_BASE_URL` and `CORS_ALLOWED_ORIGINS` if they are on
   different domains.
5. Schedule `python manage.py process_reservations` every minute.
