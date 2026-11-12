# Development Progress

Library Seat & Study Room Reservation Portal. This file records what is built,
what has been verified, and what is left. Updated at the end of each work
session.

**Last updated:** 2026-11-13

## Status at a glance

| Area | State |
|---|---|
| Backend (Django REST API) | Complete. 112 automated tests pass. |
| Frontend (React + Vite) | Complete. Builds, and lints with no warnings. |
| Frontend/backend integration | Complete. Every screen uses the real API. |
| PWA (manifest, service worker, icons) | Complete. Installable; offline behaviour verified. |
| Browser testing | Done on desktop, laptop, tablet and phone widths (results below). |
| Documentation | `README.md` (setup, architecture, API) and `frontend/README.md`. |

Nothing has been committed to git yet; all work is in the working tree.

## What was done in the latest session (2026-11-13)

1. Replaced the Vite starter `App.jsx` / `main.jsx` with the real route map and
   app entry (service worker registration, fonts, global styles).
2. First build and lint of the frontend; fixed the six lint warnings.
3. Browser testing, which found and fixed:
   - **Blank page after login.** The top bar read the opening hours before
     they had loaded. Fixed, and an error boundary was added so a rendering
     error can never leave a white screen.
   - **Users page scrolled sideways on a laptop.** Tables now measure the space
     they have and switch to a card layout only when they truly do not fit;
     the Users table was slimmed so it stays a table on laptops and tablets.
   - **Reservation cards squeezed in narrow columns** (check-in desk). Cards now
     wrap according to their own width.
   - **Duration dropdown clipped** in the room booking panel.
   - Seat map aisles drawn narrower than seats.
4. A first-time visitor no longer triggers a failed "restore session" request.
5. Wrote `README.md`, `frontend/README.md` and this file.

## Verification results

### Automated backend tests

`python manage.py test` - **112 passed**. They cover registration and login,
the refresh cookie, role permissions, every booking rule, double-booking
protection, cancellation, check-in/out, automatic no-shows and completion,
maintenance and closures cancelling reservations, dashboards and reports.

### Concurrency (live server)

12 students sent a booking for the same seat and time at the same instant:
**1 created, 11 refused** with "slot taken".

### Browser tests (real browser against the real backend)

| Suite | Result |
|---|---|
| Student workflows | 44 / 44 |
| Admin and librarian workflows | 51 / 51 |
| Responsive navigation | 41 / 41 |
| PWA (production build) | 15 / 16 in the test browser; the one miss is the browser's private mode refusing installs. In a normal profile the browser reports **no installability errors**. |
| Expired authentication | 6 / 6 |
| Every page, every role, at 1440 / 1280 / 820 / 390 px | No console errors, failed requests or sideways scrolling |

The checklist from the project brief:

| # | Item | Verified |
|---|---|---|
| 1 | Student registration | Yes |
| 2 | Student login and logout | Yes |
| 3 | Admin login | Yes |
| 4 | Admin creating a Librarian account | Yes (and self-registration cannot produce one) |
| 5 | Role-based access restrictions | Yes, in the UI and by direct API calls (403/404) |
| 6 | Viewing available seats | Yes |
| 7 | Viewing available study rooms | Yes |
| 8 | Creating a seat reservation | Yes |
| 9 | Creating a study room reservation | Yes, including an invited classmate |
| 10 | Preventing conflicting reservations | Yes (409), plus the concurrency test |
| 11 | Cancelling a reservation | Yes |
| 12 | Availability updates after a change | Yes: a second student's open map updated by itself within seconds |
| 13 | Refreshing a protected page keeps the login | Yes |
| 14 | Refreshing a form keeps its draft | Yes: registration, seat booking, room booking, settings, filters; passwords never stored; drafts cleared on submit and on sign-out |
| 15 | Responsive navigation | Yes: no hamburger on desktop/laptop; drawer with overlay on tablet/phone |
| 16 | PWA installability and offline fallback | Yes: app opens offline with a clear message; booking is blocked, never faked |
| 17 | Backend and frontend communication | Yes |

The browser tests were run with temporary scripts that are not part of the
repository. The backend tests are, in each app's `tests.py` / `tests/`.

## Known limitations

- **Real-time is polling**, not push: screens refresh every 5 seconds
  (availability) to 15 seconds (dashboards).
- **QR codes are displayed, not scanned by camera.** The check-in desk accepts
  the code typed in, or scanned by a handheld scanner that types it. Students
  can also check themselves in from the app.
- **Notifications are in-app only.** No email, SMS or push notifications.
- **Maintenance is on/off**, not scheduled for a future date range.
- **No password reset by email.** An admin resets a forgotten password.
- Installing on a **phone** needs HTTPS (or a tunnel); `localhost` works for
  desktop installation. See the README.
- SQLite is fine for coursework and demonstrations. For real multi-user use,
  switch to PostgreSQL through the `DB_*` environment variables.

## Possible next steps (not started)

- Commit the work to git.
- Keep the browser tests in the repository as a repeatable suite.
- Deploy (see README section 11).
