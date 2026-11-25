# Development Progress

Library Seat & Study Room Reservation Portal. This file records what is built,
what has been verified, and what is left. Updated at the end of each work
session.

**Last updated:** 2026-11-23

## Status at a glance

| Area | State |
|---|---|
| Backend (Django REST API) | Complete. 215 automated tests pass. |
| Frontend (React + Vite) | Complete. Builds, and lints with no warnings. |
| Library revision (real stakeholder data) | Complete and tested (details below). |
| PWA (manifest, service worker, icons) | Complete (unchanged by the revision). |
| Public website (landing page) | Complete and tested (revision 2, below). |
| Documentation | `README.md`, `frontend/README.md`, `docs/Functional_Requirements.pdf` and `.md` (see `docs/`). |

The system is **deployed** (Render Static Site + Render Web Service + Supabase
PostgreSQL). Revision 5 is in the working tree and **not committed yet**; pushing
it makes Render apply migrations `users.0004` and `users.0005` to Supabase.

## Session of 2026-11-23: revision 5 (student details, filters, footer)

1. **Student ID** `023A-12345`: hyphen inserted automatically, checked by the
   server (prefixes 019A-023A in `users/student_info.py`), unique in any spelling.
   Old IDs are kept until replaced: `manage.py update_student_ids` (CSV template).
2. **Year level** 1st-4th Year only (model choices, migration `users.0004`, no SQL).
3. **Mobile number** 11 digits starting with 09, checked by the server.
4. **Names** capitalized (KYLA MAE -> Kyla Mae), in the forms and on the server.
5. **Program** dropdown of the nine full official names. Migration `users.0005`
   maps BSIT / BS Accountancy / BS Information Technology to full names.
6. Same rules for Student Assistants created by the Admin (shared
   `components/common/StudentFields.jsx` and `StudentInfoValidationMixin`).
7. **Landing footer:** centered "DLL Library · Dalubhasaan ng Lungsod ng Lucena".
8. **Reports:** Admin only (sidebar, route, `/api/reports/usage/`).
9. **Users page:** sign-in activity filter and sort (recently signed in,
   recently added, name A-Z / Z-A), reset button; server-side.

Live data found (Supabase, 2026-11-23, read-only): 33 accounts; 27 of 28 student
IDs in the old format (no mapping to new IDs exists in the data); no Year 5/6;
all 4 phone numbers valid; no all-capital names; 17 program values that are not
DLL programs (BS Psychology 4, BS Computer Science 4, BS Civil Engineering 3,
BS Nursing 3, BA Communication 3) are left unchanged.

Backup before this revision: `backend/backup-supabase-before-revision-5.json`.

| Check | Result |
|---|---|
| Backend tests (SQLite) | 215 passed |
| Migrations on a copy of the live data, forward and back | Passed, only program names changed |
| `sqlmigrate users 0004` on Supabase | No-op (no SQL) |
| Revision 5 in a real browser (isolated copy) | 69 / 69 |
| Every portal page, all roles | No errors |
| Lint / build | Clean |

## Session of 2026-11-18: revision 4 (QR camera, backup, Render)

1. **Camera QR scanner** on the Check-in Desk (`QrScannerDialog.jsx`,
   `useQrCamera.js`, `utils/checkInScan.js`, library `jsqr`). Manual entry is
   unchanged. It uses the existing lookup and check-in API.
2. **Backup:** `backend/backup.json` (git-ignored), made by
   `manage.py create_backup`. `manage.py restore_backup` restores it once into a
   new database and refuses a database that already has accounts.
3. **Render preparation:** `render.yaml`, `backend/build.sh`, `backend/start.sh`,
   `DATABASE_URL`, WhiteNoise, gunicorn, psycopg, media served in production.
4. **Guide:** `docs/RENDER_DEPLOYMENT_GUIDE.md`.
5. **Fix:** a reservation reminder can no longer be sent twice by two processes.

### Verification (2026-11-18, revision 4)

| Check | Result |
|---|---|
| Backend tests (SQLite) | 192 passed |
| Scanner in a real browser, simulated camera (development and production builds) | 54 / 54 each |
| Backup restored into a separate database, every row compared | Passed (2,467 records) |
| Production settings rehearsal (hosts, CORS, static files, media, scheduler) | Passed |
| `render.yaml` against Render's published schema | Valid |
| Lint / build | Clean |

**Not tested yet:** the deployment itself, a physical camera, gunicorn (it does
not run on Windows), and the restore and test suite on a real PostgreSQL server.
The backup data passed a static check of PostgreSQL's stricter rules.

## Session of 2026-11-18: revision 3 (rooms, no-shows, tables)

1. **Room reservation removed.** Pages, routes, menu items, dashboard shortcuts,
   the `/api/study-rooms/` API and room booking in the service are gone. Past room
   reservations (125) are kept and readable; all rooms are archived.
2. **15-minute automatic no-show.** The deadline is exactly start + 15 minutes
   (no longer configurable). `reservations/scheduler.py` runs every 30 seconds
   inside the web server, with no browser needed.
3. **Grouped tables.** Student map, Manage Seats map and the seat list show each
   table's six seats together, Table 1 to 15.
4. **Whole-table availability.** *Manage table* in Manage Seats; single-seat
   availability still works on its own. New field `Seat.out_with_table`.

Dashboards: the study room meter, stat and ranking were replaced by computers.

Migrations: `library.0007`, `seats.0003`, `reservations.0005`, `users.0003`,
`activity.0003`. Backup: `backend/db.backup-before-revision-3.sqlite3`.

### Verification (2026-11-18)

| Check | Result |
|---|---|
| Backend tests | 183 passed |
| Live server, no browser or web requests: overdue reservations cancelled | Passed |
| Revision 3 in a real browser | 65 / 65 |
| Revision 1 workflows | 81 / 81 |
| Revision 2 (branding, login, install, website, settings) | 59 / 59 |
| Website at four widths | 32 / 32 |
| Installed app (production build) | 14 / 14 |
| Every portal page, all roles, four widths | No errors |
| Lint / build | Clean |

Requirement: the Django server must be running for no-shows to be processed.

## Session of 2026-11-17: revision 2 (branding, website, installation)

Only what was asked; the app's design is otherwise unchanged.

1. **Branding:** "DLL Library" (sidebar, login page, browser tab, installed app
   name). The logo reads "DLL Library / Reservation Portal".
2. **Sign-in after another user signs out:** each person now lands on their
   own dashboard. Pressing Sign out forgets the page that was open; a page
   remembered from an expired session or a bookmark is reopened only for the
   same person and only if their role may open it.
3. **Install app** is shown in every role's sidebar (it was hidden because the
   browser's install offer was only listened for after the sidebar appeared,
   and it often fires before that). It opens the browser's own install
   dialog when offered, otherwise step-by-step instructions; it is hidden in
   the installed app.
4. **Header:** library status and the notification bell only. Profile and
   Sign out remain in the sidebar.
5. **Public website** at `/` built from the library's information board
   (services, library card, rules, personnel, hours, contact), with Home, Our
   Services, About, Contact, Install and Login. Responsive with a menu below
   900 px.
6. **Library Settings** has two new tabs, Library information and Landing
   page, for the Admin to edit all of it (including photos). The hours come
   from the existing Opening hours tab.
7. **Login page:** a Back button to the website in a browser; none in the
   installed app.
8. **Installed app:** opens on the login page (or the dashboard when signed
   in), never the website, and stays signed in after being closed.

Backend: four models in the `library` app (`LibraryProfile`, `LandingItem`,
`LibraryPersonnel`, `LandingPhoto`), migrations `library.0005` (tables) and
`library.0006` (the board's content), public read endpoint and Admin-only
editing endpoints, media uploads (Pillow added to `requirements.txt`).

### Verification (2026-11-17)

| Check | Result |
|---|---|
| Backend tests | 160 passed (10 new for the website and its settings) |
| Revision 2 in a real browser (branding, role switching, install, header, website, settings) | 58 / 59; the one miss was a wrong test assumption (see below) |
| Website at 1440 / 1280 / 820 / 390 px | 32 / 32 |
| Installed app (production build, standalone mode, persistent profile) | 14 / 14 |
| Revision 1 workflows (approval, tables, computers, assistant) | 81 / 81 |
| Every portal page, all roles, four widths | No errors or sideways scrolling |
| Lint / build | Clean |

The miss: the test expected the Contact section at the top of the window, but
Contact is the last section, so the page correctly stops at the bottom with
the whole section in view.

Notes:

- Seats T03-6 and T05-2 were set "Out of service (Missing Chair)" from the
  Admin account on Nov 16, so Tables 3 and 5 cannot be requested whole. This
  is correct behaviour and was left as it is.
- The personnel names are copied exactly from the board ("Ms. Mjie", ...).
  The board shows first names only; edit them in Library Settings if needed.
- No email address is on the board, so none is shown until one is entered.
- No library photos are uploaded yet; the website shows its navy banner until
  the Admin adds some in Library Settings > Landing page.

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
- The desk accepts a camera scan, a typed code or a handheld scanner. The camera
  needs HTTPS (or localhost).
- Notifications are in-app only (no email or SMS).
- No password reset by email; an Admin resets a forgotten password.
- Installing on a phone needs HTTPS; `localhost` works for desktop.

## Possible next steps (not started)

- Commit and push revision 5, then check the Render deploy logs.
- Collect students' real IDs and apply them with `update_student_ids`.
