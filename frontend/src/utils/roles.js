export const isStaff = (user) => ['admin', 'librarian', 'assistant'].includes(user.role)
export const canManageReservations = (user) => user.role === 'admin' || user.role === 'librarian'
export const isAdmin = (user) => user.role === 'admin'
export const isStudent = (user) => user.role === 'student'
export const canManageResources = (user) => Boolean(user.can_manage_resources)

const ROUTE_RULES = [
  [/^\/admin(\/|$)/, isAdmin],
  [/^\/manage\/seats(\/|$)/, canManageResources],
  [/^\/reports(\/|$)/, canManageReservations],
  [/^\/(desk|manage\/reservations)(\/|$)/, isStaff],
  [/^\/reservations\/?$/, isStudent],
]

export function canOpen(pathname, user) {
  const rule = ROUTE_RULES.find(([pattern]) => pattern.test(pathname))
  return rule ? rule[1](user) : true
}

export function initials(user) {
  return `${user.first_name?.[0] || ''}${user.last_name?.[0] || ''}`.toUpperCase() || '?'
}
