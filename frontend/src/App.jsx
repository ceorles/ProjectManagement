import { lazy } from 'react'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import ErrorBoundary from './components/common/ErrorBoundary'
import { GuestOnly, RequireAuth, RequireRole } from './components/layout/RouteGuards'
import { AuthProvider } from './context/AuthProvider'
import { ToastProvider } from './context/ToastProvider'
import LoginPage from './pages/auth/LoginPage'
import LandingPage from './pages/landing/LandingPage'
import RegisterPage from './pages/auth/RegisterPage'
import NotFoundPage from './pages/shared/NotFoundPage'
import {
  canManageResources, isAdmin, isStaff, isStudent,
} from './utils/roles'

// Pages behind the login are loaded on demand, which keeps the first load
// small on phones. <AppLayout> shows a loading state while one is fetched.
const DashboardPage = lazy(() => import('./pages/shared/DashboardPage'))
const SeatBookingPage = lazy(() => import('./pages/booking/SeatBookingPage'))
const ReservationDetailPage = lazy(() => import('./pages/shared/ReservationDetailPage'))
const NotificationsPage = lazy(() => import('./pages/shared/NotificationsPage'))
const ProfilePage = lazy(() => import('./pages/shared/ProfilePage'))
const MyReservationsPage = lazy(() => import('./pages/student/MyReservationsPage'))
const CheckInDeskPage = lazy(() => import('./pages/librarian/CheckInDeskPage'))
const ManageReservationsPage = lazy(() => import('./pages/librarian/ManageReservationsPage'))
const ReportsPage = lazy(() => import('./pages/librarian/ReportsPage'))
const ManageSeatsPage = lazy(() => import('./pages/librarian/ManageSeatsPage'))
const UsersPage = lazy(() => import('./pages/admin/UsersPage'))
const SettingsPage = lazy(() => import('./pages/admin/SettingsPage'))
const ActivityLogPage = lazy(() => import('./pages/admin/ActivityLogPage'))

export default function App() {
  return (
    <BrowserRouter>
      <ErrorBoundary>
      <ToastProvider>
        <AuthProvider>
          <Routes>
            {/* The public website. (The installed app skips it and opens on sign-in.) */}
            <Route path="/" element={<LandingPage />} />

            <Route element={<GuestOnly />}>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
            </Route>

            <Route element={<RequireAuth />}>
              {/* Every signed-in user */}
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/seats" element={<SeatBookingPage />} />
              <Route path="/reservations/:id" element={<ReservationDetailPage />} />
              <Route path="/notifications" element={<NotificationsPage />} />
              <Route path="/profile" element={<ProfilePage />} />

              <Route element={<RequireRole allow={isStudent} />}>
                <Route path="/reservations" element={<MyReservationsPage />} />
              </Route>

              {/* Librarians, admins and student assistants */}
              <Route element={<RequireRole allow={isStaff} />}>
                <Route path="/desk" element={<CheckInDeskPage />} />
                <Route path="/manage/reservations" element={<ManageReservationsPage />} />
              </Route>

              {/* Admins only */}
              <Route element={<RequireRole allow={isAdmin} />}>
                <Route path="/reports" element={<ReportsPage />} />
              </Route>

              {/* Admins, and librarians the admin has allowed */}
              <Route element={<RequireRole allow={canManageResources} />}>
                <Route path="/manage/seats" element={<ManageSeatsPage />} />
              </Route>

              <Route element={<RequireRole allow={isAdmin} />}>
                <Route path="/admin/users" element={<UsersPage />} />
                <Route path="/admin/settings" element={<SettingsPage />} />
                <Route path="/admin/activity" element={<ActivityLogPage />} />
              </Route>

              <Route path="*" element={<NotFoundPage />} />
            </Route>
          </Routes>
        </AuthProvider>
      </ToastProvider>
      </ErrorBoundary>
    </BrowserRouter>
  )
}
