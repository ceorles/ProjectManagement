# Frontend

React 19 + Vite 8 client for the Library Seat & Study Room Reservation Portal.
Setup, architecture and API documentation are in the [project README](../README.md).

```bash
npm install
npm run dev        # development server at http://localhost:5173
npm run lint       # oxlint
npm run build      # production build in dist/ (includes the service worker)
npm run preview    # serve the production build at http://localhost:4173
```

The Django backend must be running (by default at `http://127.0.0.1:8000`);
requests to `/api` are forwarded to it. To change that, copy `.env.example` to
`.env` and edit it.

## Where things are

| Folder | Contents |
|---|---|
| `src/services/` | The only code that calls the API. `apiClient.js` handles tokens and errors; `index.js` has one function per endpoint. |
| `src/context/` | Session (`AuthProvider`), library hours and rules (`LibraryProvider`), toasts. |
| `src/hooks/` | `useApiQuery` (loading + polling), `useFormDraft` (refresh-safe forms), `useAction` (double-submit-safe buttons), and smaller helpers. |
| `src/components/` | Reusable pieces grouped by feature: `common`, `layout`, `reservations`, `seats`, `rooms`, `dashboard`. Each group has one stylesheet. |
| `src/pages/` | One file per screen, grouped by who uses it: `auth`, `booking`, `student`, `librarian`, `admin`, `shared`. |
| `src/utils/` | Date/time formatting, booking options, draft storage, labels and colours. |
| `src/styles/` | `tokens.css` (colours, sizes) and `base.css` (reset, layout helpers). |

Colours are defined once in `src/styles/tokens.css`: blue is the primary colour
and yellow the accent.
