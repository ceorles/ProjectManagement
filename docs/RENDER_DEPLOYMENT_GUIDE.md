# DLL Library: Render Deployment Guide

This guide puts DLL Library online, one step at a time. You do not need any
deployment experience. Do the parts in order and do not skip the checks.

**What you will end up with**

| Part | Render service | Folder in the project | Example address |
|---|---|---|---|
| Website and PWA (React) | Static Site | `frontend` | `https://dll-library.onrender.com` |
| API and no-show scheduler (Django) | Web Service | `backend` | `https://dll-library-api.onrender.com` |
| Database | Render PostgreSQL | none | Private connection |
| Uploaded photos | Persistent Disk | none | Attached to the Web Service |

Visitors only ever use the website address. The website quietly forwards `/api`
and `/media` requests to the backend. This keeps people signed in, including on
iPhones and iPads, which block login cookies shared between two different sites.

> **Replace the example addresses.** Render may add letters to a name that is
> already taken, such as `dll-library-api-x7k2.onrender.com`. Wherever this guide
> shows an address, use the real one from your Render dashboard.

---

## 1. Before Deployment

### What you need

- [ ] A **GitHub account** with this project's repository.
- [ ] **GitHub Desktop** installed and signed in.
- [ ] A **Render account** from <https://render.com>, with a payment card if you
      choose the recommended paid plan.
- [ ] A **Supabase account** from <https://supabase.com>, only if you choose
      Supabase for the database.
- [ ] The database backup at `backend/backup.json`.
- [ ] Python on your computer, with the project's `backend/venv` folder. You will
      use it once to restore the backup.

### Choose a plan

| | **Recommended** | Free trial setup |
|---|---|---|
| Web Service | Starter (paid) | Free |
| Database | Render PostgreSQL Basic (paid) | Supabase Free |
| Website | Static Site (free) | Static Site (free) |
| Stays awake for no-show cancellation | **Yes** | Only with an outside ping (Part 9) |
| Uploaded photos survive restarts | **Yes**, with a disk | **No** |
| Good for real library use | **Yes** | Demonstrations and testing |

**Recommendation: use Render PostgreSQL with a Starter Web Service and a 1 GB
disk.** Everything stays in one dashboard, and the database connects over Render's
private network. Render shows the exact monthly price before you confirm anything,
so check it at <https://render.com/pricing>.

Do **not** use Render's Free PostgreSQL for real data. Render deletes a free
database after its 30-day period and grace period end.

### Your backup files

**Database:** `backend/backup.json` holds your accounts, password hashes, seats,
reservations, notifications, settings and landing page text.

**Uploaded photos are not inside `backup.json`.** The file only records each
photo's name. At the time this guide was written, the project had **no uploaded
photos**, so there is nothing to transfer. If you add photos on your computer
before deploying, back them up in PowerShell:

```powershell
cd E:\Andrei\Code\ProjectManagement\backend
Compress-Archive -Path media\* -DestinationPath media-backup.zip
```

### Keep the backup safe

`backup.json` contains names, email addresses and password hashes.

- Git is already set to ignore `backend/backup*.json` and `backend/media-backup*.zip`.
- Never upload these files to GitHub, chat apps or public drives.
- Keep a copy in a private, password-protected location, such as an encrypted USB
  drive.
- Delete extra copies after the deployment has been checked.

### If you keep using the local system before deploying

The backup is a snapshot. To include newer changes, create it again right before
you restore:

```powershell
cd E:\Andrei\Code\ProjectManagement\backend
.\venv\Scripts\python.exe manage.py create_backup --replace
```

The old file is kept as `backup.previous.json`.

---

## 2. Push the Latest Code to GitHub

1. Open **GitHub Desktop** and select the **ProjectManagement** repository.
2. Open the **Changes** tab and read the list of files on the left.
3. **Stop and check.** These must **not** appear in the list:
   - `backend/backup.json`
   - `backend/.env` or `frontend/.env`
   - `backend/db.sqlite3` or any `db.backup-*.sqlite3` file
   - anything in `backend/media/`

   If one appears, do not commit. Right-click it and choose **Ignore file**.
4. In the **Summary** box at the bottom left, type: `Add QR scanner and prepare Render deployment`
5. Click **Commit to main**.
6. Click **Push origin** at the top.
7. Click **Repository > View on GitHub** and confirm that `render.yaml` is visible
   at the top level and `backend/build.sh` exists.

---

## 3. Create the Database

Choose **one** option.

### Option A: Render PostgreSQL (recommended)

1. In the Render dashboard, click **New > Postgres**.
2. Fill in:
   - **Name:** `dll-library-db`
   - **Database:** `dll_library`
   - **User:** `dll_library`
   - **Region:** **Singapore**. Use the same region for the Web Service.
   - **PostgreSQL Version:** 17
   - **Plan:** Basic, the smallest paid size
3. Click **Create Database** and wait until the status says **Available**.
4. Open the database's **Connect** menu. You need two values:
   - **Internal Database URL**, used by the Web Service in Part 4.
   - **External Database URL**, used by your computer once in Part 7.

Treat both like passwords.

### Option B: Supabase PostgreSQL

1. At <https://supabase.com/dashboard>, click **New project**.
2. Name it `dll-library`, create a strong database password and save it privately.
3. Choose the **Southeast Asia (Singapore)** region, then create the project.
4. Click **Connect** at the top of the project page.
5. Choose the **Session pooler** connection string. It looks like this:

   ```text
   postgresql://postgres.PROJECTREF:YOUR-PASSWORD@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres
   ```

6. Replace `YOUR-PASSWORD` with your database password. If the password contains
   symbols such as `@`, `#` or `/`, it is easiest to reset it to one that only
   uses letters and numbers.

Use the **Session pooler** string. Supabase's direct connection uses IPv6, which
Render may not be able to reach. Use this same string in Part 4 and Part 7.

Supabase may pause a Free project that has too little activity. If the site cannot
reach the database, check for a **Paused** label in the Supabase dashboard.

---

## 4. Deploy the Django Backend

1. In Render, click **New > Web Service**.
2. Choose **Build and deploy from a Git repository**, connect GitHub if asked, and
   select the **ProjectManagement** repository.
3. Fill in exactly:

   | Setting | Value |
   |---|---|
   | **Name** | `dll-library-api` |
   | **Language** | Python 3 |
   | **Branch** | `main` |
   | **Region** | Singapore |
   | **Root Directory** | `backend` |
   | **Build Command** | `bash build.sh` |
   | **Start Command** | `bash start.sh` |
   | **Instance Type** | Starter |

4. Under **Advanced**, set **Health Check Path** to `/api/health/`.
5. Under **Advanced > Add Disk**, enter:

   | Setting | Value |
   |---|---|
   | **Name** | `dll-library-media` |
   | **Mount Path** | `/var/data` |
   | **Size** | 1 GB |

6. Add the backend variables from Part 5.
7. Click **Deploy Web Service**.
8. Watch the **Logs** until you see that the service is live. The first build takes
   several minutes. `build.sh` installs the packages, collects static files and
   creates the database tables.
9. Copy the service address from the top of the page.
10. Open this address, using your real backend name:

    ```text
    https://dll-library-api.onrender.com/api/health/
    ```

    You should see `"status":"ok"` and `"scheduler":{"running":true`.

> **Using the Blueprint instead:** `render.yaml` describes these services. In Render
> choose **New > Blueprint**, select the repository, and enter the values it asks
> for. You still need to do Parts 7 to 10. The manual steps above are easier to
> follow the first time.

---

## 5. Configure Production Environment Variables

Add these in the Render dashboard, under each service's **Environment** tab. Never
put real values in a file that goes to GitHub.

### Backend: Web Service `dll-library-api`

| Variable | Purpose | Value |
|---|---|---|
| `PYTHON_VERSION` | Python used on Render | `3.13.14` |
| `DJANGO_SECRET_KEY` | Secret used to sign logins | Click **Generate** in Render |
| `DJANGO_DEBUG` | Hides error details from visitors | `False` |
| `DATABASE_URL` | Database connection | Render **Internal Database URL**, or the Supabase **Session pooler** string |
| `DJANGO_ALLOWED_HOSTS` | Addresses Django answers to, with no `https://` | `dll-library-api.onrender.com,dll-library.onrender.com` |
| `CORS_ALLOWED_ORIGINS` | Website allowed to call the API | `https://dll-library.onrender.com` |
| `CSRF_TRUSTED_ORIGINS` | Website trusted for form posts | `https://dll-library.onrender.com` |
| `REFRESH_COOKIE_SECURE` | Sends the login cookie over HTTPS only | `True` |
| `REFRESH_COOKIE_SAMESITE` | Login cookie rule | `Lax` |
| `LIBRARY_TIME_ZONE` | Library time zone | `Asia/Manila` |
| `MEDIA_DIR` | Where uploaded photos are saved | `/var/data/media` |
| `RESERVATION_SCHEDULER_ENABLED` | Turns on no-show cancellation | `True` |
| `RESERVATION_SCHEDULER_INTERVAL_SECONDS` | How often it runs | `30` |

You do not know the website address until Part 6. Enter your best guess now, then
correct these three variables after Part 6 if the real address is different.

### Frontend: Static Site `dll-library`

| Variable | Purpose | Value |
|---|---|---|
| `NODE_VERSION` | Node.js used for the build | `24` |
| `VITE_API_BASE_URL` | Where the app sends API requests | `/api` |

`VITE_API_BASE_URL` stays `/api` because the website forwards those requests to the
backend. Vite variables are read during the build, so **after changing one, run
Manual Deploy > Clear build cache & deploy.**

---

## 6. Deploy the React Frontend

1. In Render, click **New > Static Site** and select the **ProjectManagement** repository.
2. Fill in exactly:

   | Setting | Value |
   |---|---|
   | **Name** | `dll-library` |
   | **Branch** | `main` |
   | **Root Directory** | `frontend` |
   | **Build Command** | `npm ci && npm run build` |
   | **Publish Directory** | `dist` |

3. Add the frontend variables from Part 5.
4. Click **Deploy Static Site** and wait until it is live.
5. Open the site's **Redirects/Rewrites** page and add these rules **in this order**.
   Use your real backend address in the first two.

   | Source | Destination | Action |
   |---|---|---|
   | `/api/*` | `https://dll-library-api.onrender.com/api/*` | Rewrite |
   | `/media/*` | `https://dll-library-api.onrender.com/media/*` | Rewrite |
   | `/*` | `/index.html` | Rewrite |

6. Open the site's **Headers** page and add:

   | Path | Name | Value |
   |---|---|---|
   | `/sw.js` | `Cache-Control` | `no-cache` |
   | `/index.html` | `Cache-Control` | `no-cache` |

7. Return to the backend's **Environment** tab. Make sure `DJANGO_ALLOWED_HOSTS`,
   `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS` contain the real website address.
   Save, and let the backend redeploy.
8. Test the forwarding by opening:

   ```text
   https://dll-library.onrender.com/api/health/
   ```

   You should see the same `"status":"ok"` message as in Part 4.

### If the forwarding test fails

Check the rule spelling first. If `/api/health/` still does not answer, connect the
website directly to the backend:

1. Static Site: set `VITE_API_BASE_URL` to `https://dll-library-api.onrender.com/api`,
   then run **Clear build cache & deploy**.
2. Web Service: set `REFRESH_COOKIE_SAMESITE` to `None`.

This works in most browsers, but iPhones and iPads may ask people to sign in again
each time they reopen the app.

---

## 7. Restore Existing Database Data Using backup.json

**Do this once, before you share the website with anyone.**

You run the restore **from your own computer**. `backup.json` never has to be
uploaded to Render, and the method works on every Render plan.

### The correct order

1. The production database exists (Part 3).
2. The backend is deployed, so migrations have already created the tables (Part 4).
3. You restore the backup (below).
4. You verify the data.

### Why this restore is safe

Use `restore_backup` instead of running Django's `loaddata` directly. It runs
`loaddata` for you and adds these protections:

- It **refuses to run** if the database already has any account, so it cannot be
  applied twice or overwrite live data.
- It removes the default content that migrations add, so nothing is duplicated.
- If anything fails, the whole restore is undone.
- It compares the record counts before finishing.

### Step by step

1. Open **PowerShell** and go to the backend folder:

   ```powershell
   cd E:\Andrei\Code\ProjectManagement\backend
   ```

2. Install the production packages on your computer:

   ```powershell
   .\venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

3. Point this PowerShell window at the production database. Paste your **External
   Database URL** from Render, or your Supabase **Session pooler** string:

   ```powershell
   $env:DATABASE_URL = "PASTE-THE-CONNECTION-STRING-HERE"
   ```

4. Confirm no migrations are waiting. Every line should show `[X]`:

   ```powershell
   .\venv\Scripts\python.exe manage.py showmigrations
   ```

5. Restore the backup:

   ```powershell
   .\venv\Scripts\python.exe manage.py restore_backup backup.json
   ```

6. Check that the **Database** line shows your production database host, **not**
   `db.sqlite3`. Type `RESTORE` and press Enter.
7. Wait for **Restore complete.**
8. Check the restored records:

   ```powershell
   .\venv\Scripts\python.exe manage.py shell -c "from users.models import User; from seats.models import Seat; from reservations.models import Reservation as R; print('Accounts', User.objects.count()); print('Seats', Seat.objects.filter(has_computer=False).count()); print('Computers', Seat.objects.filter(has_computer=True).count()); print('Reservations', R.objects.count())"
   ```

   With the current backup you should see:

   ```text
   Accounts 32
   Seats 90
   Computers 4
   Reservations 934
   ```

9. **Disconnect this window from production:**

   ```powershell
   Remove-Item Env:DATABASE_URL
   ```

10. Open the website and sign in with your real Admin, Librarian, Student Assistant
    and Student accounts. Passwords are the same as before.

### If the restore says the database already has accounts

**Stop.** The backup was already restored, or someone has registered. Do not delete
anything from a database people are using. If the site is brand new and nobody is
using it yet, the cleanest fix is to create a new empty database, update
`DATABASE_URL`, redeploy, and restore again.

---

## 8. Configure Media Storage

Render's normal file system is temporary. Files saved there disappear on each deploy
or restart, so photos must be stored on the disk from Part 4.

**Check these two settings:**

- The disk is mounted at `/var/data`.
- `MEDIA_DIR` is `/var/data/media`.

**Test it:**

1. Sign in as Admin and open **Library Settings > Landing page**.
2. Upload a small test photo and confirm it appears on the landing page.
3. In the Web Service, click **Manual Deploy > Deploy latest commit**.
4. After the deploy, confirm the photo is still there. Remove the test photo if you
   do not want to keep it.

**Moving existing photos:** you currently have none. If you add some locally later,
the simplest way to move them is to upload each one again in **Library Settings**.

**Free Web Service:** Render's free plan has no disk, so uploaded photos will vanish.
The website still works and shows its navy banner, but do not rely on uploads on
that plan.

**Backing up photos later:** download them from the disk through the service's
**Shell** page, or keep the original photos in a private folder.

---

## 9. Configure Automatic Reservation Cancellation

The 15-minute no-show cancellation runs **inside the Web Service**. Every 30 seconds
a background timer cancels overdue reservations, releases their seats and notifies
each student once. No extra Cron Job or Worker is needed, as long as the Web Service
stays awake.

| Plan | What happens |
|---|---|
| **Starter (recommended)** | Always awake, so cancellations happen on time. |
| **Free** | Render puts the service to sleep after 15 minutes without visitors, and the timer stops. Overdue reservations are processed when it wakes up. |

### Verify it

1. Open `https://dll-library-api.onrender.com/api/health/`.
2. Confirm `"running":true`, a recent `"last_run"` time, and `"last_error":null`.
3. Do a real test with a test student:
   - Reserve a seat for the current time slot and approve it as Librarian.
   - Do not check in.
   - About 15 minutes after the reservation's start time, confirm that its status is
     **No-show**, the seat is available again, and the student has one notification.

### Only if you use the Free plan

Keep the service awake with a free outside monitor such as <https://cron-job.org>:

- **URL:** `https://dll-library-api.onrender.com/api/health/`
- **Schedule:** every 10 minutes

Free services can still restart, and Render limits free running hours each month, so
this is suitable for demonstrations only.

---

## 10. Final Deployment Testing

Use a phone and a computer. Tick each item.

**Website and accounts**

- [ ] Landing page loads with services, rules, personnel, hours and contact details.
- [ ] Log in and log out work.
- [ ] Admin, Librarian, Student Assistant and Student each reach the correct dashboard.
- [ ] A new student can register.
- [ ] Refreshing a page such as `/desk` or `/reservations` does not show a 404.
- [ ] Typing a page address directly opens that page.

**Reservations**

- [ ] A student can request a seat and a whole table.
- [ ] A student can request a computer.
- [ ] The request appears as Pending, and the Librarian is notified.
- [ ] The Librarian approves it, and the student is notified.
- [ ] Seat availability updates within a few seconds.

**QR code and check-in**

- [ ] An approved reservation shows a QR code.
- [ ] **Check-in Desk > Scan QR Code** asks for camera permission.
- [ ] The camera preview appears, and scanning checks the student in.
- [ ] Scanning the same code again says **Already checked in**.
- [ ] Typing a code by hand still works.
- [ ] A reservation left unchecked is cancelled after 15 minutes.

**Settings and media**

- [ ] Admin changes in Library Settings save and appear on the landing page.
- [ ] An uploaded photo still appears after a redeploy.

**Installed app**

- [ ] **Install app** appears, and the app installs.
- [ ] The installed app opens on the login page or dashboard, not the landing page.
- [ ] After closing and reopening, you are still signed in.
- [ ] The camera scanner works inside the installed app.
- [ ] The browser's developer tools show API calls going to your `onrender.com` site,
      never `localhost`.

---

## 11. Common Deployment Errors

Always read the service's **Logs** tab first. The last red lines usually name the problem.

| Problem | Likely cause | What to do |
|---|---|---|
| **Application failed to start** | Missing variable or wrong command | Confirm Root Directory is `backend` and Start Command is `bash start.sh`. Read the Logs. |
| **`DJANGO_SECRET_KEY is not set`** | Variable missing | Add it in the Environment tab and generate a value. |
| **Database connection failure** | Wrong connection string | Web Service: use the **Internal** URL. Your computer: use the **External** URL. Supabase: use the **Session pooler** string and check that the project is not paused. |
| **`password authentication failed`** | Wrong password in the string | Copy the string again. With Supabase, reset the password to letters and numbers only. |
| **Bad Request (400)** | Address missing from allowed hosts | Add both addresses to `DJANGO_ALLOWED_HOSTS`, with no `https://`. |
| **CORS error in the browser** | Website address does not match | Set `CORS_ALLOWED_ORIGINS` to the exact website address, starting with `https://` and with no ending `/`. |
| **CSRF error** | Website address not trusted | Set `CSRF_TRUSTED_ORIGINS` the same way. |
| **Signed out after every refresh** | Forwarding rule or cookie setting is wrong | Recheck the `/api/*` rule and confirm `REFRESH_COOKIE_SECURE=True`. |
| **Django admin has no styling** | Static files were not collected | Confirm Build Command is `bash build.sh`, then redeploy. |
| **404 after refreshing a page** | SPA rule missing | Add the `/*` to `/index.html` rewrite as the **last** rule. |
| **API calls return the web page instead of data** | Rules are in the wrong order | Put `/api/*` and `/media/*` above `/*`. |
| **Install app does not appear** | Not on HTTPS, already installed, or old cache | Use the `https://` address, then clear site data and reload. On iPhone use **Share > Add to Home Screen**. |
| **Old version keeps showing** | The service worker is still updating | Close every tab of the site and open it again. |
| **Camera does not open** | Permission denied or not on HTTPS | Allow the camera in browser settings and use the `https://` address. Close other apps using the camera. |
| **QR code does not scan** | Glare, blur or a very small code | Raise the phone's screen brightness, hold it steady, fill the yellow frame, or type the code by hand. |
| **Photos disappear** | No disk, or the wrong folder | Confirm the disk is mounted at `/var/data` and `MEDIA_DIR=/var/data/media`. |
| **Photo shows a broken image** | Rule or file missing | Check the `/media/*` rule, then upload the photo again. |
| **No-shows are not cancelled** | The service is asleep or the timer stopped | Open `/api/health/` and check `"running":true` and `last_error`. Use the Starter plan. |
| **Restore: `Run python manage.py migrate first`** | The backend has not finished deploying | Wait for a successful deploy, then try again. |
| **Restore: `already has N accounts`** | The data is already there | Do not run it again. See the end of Part 7. |
| **Restore: `backup.json was not found`** | PowerShell is in the wrong folder | Run `cd E:\Andrei\Code\ProjectManagement\backend` first. |
| **Restore fails with another error** | A record was refused | Nothing was changed, because the restore undoes itself. Copy the last lines of the error and fix that record before trying again. |

---

## Quick reference

| Task | Where | Command or value |
|---|---|---|
| Backend build | Render Web Service | `bash build.sh` |
| Backend start | Render Web Service | `bash start.sh` |
| Frontend build | Render Static Site | `npm ci && npm run build` |
| Frontend publish folder | Render Static Site | `dist` |
| Create a new backup | Your computer, in `backend` | `.\venv\Scripts\python.exe manage.py create_backup --replace` |
| Restore once | Your computer, in `backend` | `.\venv\Scripts\python.exe manage.py restore_backup backup.json` |
| Check the server and scheduler | Browser | `https://YOUR-BACKEND.onrender.com/api/health/` |
