// Who may open which group of pages. The backend enforces the same rules.
export const isStaff = (user) => user.role === 'admin' || user.role === 'librarian'
export const isAdmin = (user) => user.role === 'admin'
export const isStudent = (user) => user.role === 'student'
export const canManageResources = (user) => Boolean(user.can_manage_resources)

export function initials(user) {
  return `${user.first_name?.[0] || ''}${user.last_name?.[0] || ''}`.toUpperCase() || '?'
}
