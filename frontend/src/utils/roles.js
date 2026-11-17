// Who may open which group of pages. The backend enforces the same rules.
// Library staff: admins, librarians and student assistants.
export const isStaff = (user) => ['admin', 'librarian', 'assistant'].includes(user.role)
// Decides on reservations (approve, reject, cancel, book for a student).
// Student assistants help at the desk but do not make these decisions.
export const canManageReservations = (user) => user.role === 'admin' || user.role === 'librarian'
export const isAdmin = (user) => user.role === 'admin'
export const isStudent = (user) => user.role === 'student'
export const canManageResources = (user) => Boolean(user.can_manage_resources)

export function initials(user) {
  return `${user.first_name?.[0] || ''}${user.last_name?.[0] || ''}`.toUpperCase() || '?'
}
