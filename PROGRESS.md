# Development Progress

Library Seat & Study Room Reservation Portal. This file records what is built,
what has been verified, and what is left. Updated at the end of each work
session.

**Last updated:** 2026-11-16

## Status at a glance

| Area | State |
|---|---|
| Backend (Django REST API) | Complete. 150 automated tests pass. |
| Frontend (React + Vite) | Complete. Builds, and lints with no warnings. |
| Library revision (real stakeholder data) | Complete and tested (details below). |
| PWA (manifest, service worker, icons) | Complete (unchanged by the revision). |
| Documentation | `README.md`, `frontend/README.md`, `docs/Functional_Requirements.pdf` and `.md`. |

The revision is in the working tree and **not committed yet** (the previous
state is the last commit, so the changes can be reviewed with `git diff`).

## Session of 2026-11-16: revision to match the real library

Scope: only what the stakeholder revision asked for. Design, layout, colours and
navigation style are unchanged.

### 1. Actual capacity and seating

- One floor: **First Floor**.
- **Reading Hall: 15 tables x 6 chairs = 90 seats**, numbered `T01-1` ... `T15-6`.
  Each seat has a `table_number`; the seat map draws the six chairs around a
  labelled table.
- **Computer Area: 4 computers**, `PC-1` ... `PC-4`, separate from the 90 seats.
- `python manage.py setup_library` creates this layout and is safe to re-run.

### 2. Seat, group and table requests

- One request can hold 1 to 6 seats. Up to 2 need no reason; 3 or more, including
  a whole table, require a reason, which the Librarian sees.
- Tapping a table's name selects all six chairs.
- A computer is always requested on its own, one per student at a time.

### 3. Librarian approval (the critical fix)

- A student's request is saved as **Pending**. It is never Confirmed automatically.
- Every active Librarian and Admin gets an in-app notification linking to the request.
- The Librarian (or Admin) approves (Pending -> Confirmed) or rejects
  (Pending -> Rejected, places released). The student is notified either way.
- Pending requests hold their seats, so they cannot be double-booked; rejected,
  withdrawn and expired requests release them.
- A request not reviewed before its time expires on its own.
- The operations dashboard shows the pending count and a Pending requests list.

### 4-6. Removals

- Zones Quiet Zone East, Quiet Zone West and Collaborative Commons, the Second
  and Third floors, and five of the six rooms are **archived** (hidden
  everywhere, kept for history). Nothing was deleted.
- **Manage Rooms** page, route and menu item removed. One study room remains
  reservable by students ("Study Room", First Floor).
- The Floors dialog was removed from Manage Seats (one floor).
- **Near window** removed from the database, API, forms, seat details and seed data.

### 7. Student Assistant role

Created by the Admin, never by public registration. Can: operations dashboard,
seat map with occupants, reservation list, check-in desk, check students in and
out, own notifications and profile. Cannot: approve, reject or cancel
reservations, record no-shows, reserve for a student, view reports, manage
seats, accounts or settings.

### Database

- Backup taken before migrating: `backend/db.backup-before-library-revision.sqlite3`.
- Migrations: `library.0004`, `seats.0002`, `study_rooms.0002`, `users.0002`,
  `reservations.0003`, `reservations.0004` (data: one `ReservationSeat` row for
  each existing seat reservation).
- All accounts and all earlier reservations are intact. Archived: 2 floors,
  5 zones, 136 seats, 5 rooms.
- `seed_demo` added demo history on the new seats and the demo Student
  Assistant account (`assistant@library.edu`).

## Verification results (2026-11-16)

| Check | Result |
|---|---|
| Backend tests (`python manage.py test`) | **150 passed** (38 new: approval, tables, computers, assistant, layout) |
| Revised workflow in a real browser | **81 / 81** |
| Every page for all four roles at 1440 / 1280 / 820 / 390 px | No errors, no sideways scrolling |
| `npm run lint` / `npm run build` | Clean |
| `setup_library` run a second time | No changes (idempotent) |

The browser run covered the full scenario from the brief: student requests a
seat -> Pending -> Librarian is notified -> opens the request from the
notification -> sees student, ID, date, time, seat, count, submission date and
status -> approves -> Confirmed -> student is notified -> the seat is refused to
others. It also covered rejection, whole-table and group requests with the
reason rule, computers (one per request, no overlaps), release of places after
rejection and withdrawal, Admin notifications, Student Assistant permissions,
and the interface checks (two zones, 15 tables / 90 seats, 4 computers, no
Manage Rooms, no extra floors, no Near window).

## Things to know

- The demo accounts `admin@library.edu` and `librarian@library.edu` are
  **deactivated** in the current database (they were found that way and left
  alone). Browser tests used `librarian2@library.edu` and a temporary admin
  that was deleted afterwards, along with all other test records.
- Reports count usage only on seats and areas that still exist. Totals still
  include earlier reservations made on the retired seats.
- The Admin can approve and reject as well as the Librarian. Student Assistants
  cannot.
- The remaining study room cannot be edited from the interface now that Manage
  Rooms is gone; it can be changed in the Django admin site (`/admin/`).

## Known limitations

- Real-time is polling (5 to 15 seconds), not push.
- QR codes are displayed, not camera-scanned; the desk accepts a typed code or
  a handheld scanner.
- Notifications are in-app only (no email or SMS).
- No password reset by email; an Admin resets a forgotten password.
- Installing on a phone needs HTTPS; `localhost` works for desktop.

## Possible next steps (not started)

- Commit the revision.
- Decide whether the study room should stay reservable (see "Things to know").
