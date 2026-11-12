import { useAuth } from '../../hooks/useAuth'
import AdminDashboard from '../admin/AdminDashboard'
import LibrarianDashboard from '../librarian/LibrarianDashboard'
import StudentDashboard from '../student/StudentDashboard'

/** /dashboard shows the dashboard that belongs to the signed-in role. */
export default function DashboardPage() {
  const { user } = useAuth()
  if (user.role === 'admin') return <AdminDashboard />
  if (user.role === 'librarian') return <LibrarianDashboard />
  return <StudentDashboard />
}
