// Labels and colour tones used consistently across the whole app.

export const ROLES = {
  admin: 'Admin',
  librarian: 'Librarian',
  assistant: 'Student Assistant',
  student: 'Student',
}

/** Reservation status -> label and badge tone. */
export const RESERVATION_STATUS = {
  pending: { label: 'Pending', tone: 'yellow' },
  confirmed: { label: 'Confirmed', tone: 'blue' },
  checked_in: { label: 'Checked in', tone: 'green' },
  completed: { label: 'Completed', tone: 'gray' },
  cancelled: { label: 'Cancelled', tone: 'red' },
  rejected: { label: 'Rejected', tone: 'red' },
  no_show: { label: 'No-show', tone: 'orange' },
}

/** State of a seat for the selected time window. */
export const AVAILABILITY = {
  available: { label: 'Available', tone: 'green' },
  reserved: { label: 'Reserved', tone: 'yellow' },
  occupied: { label: 'Occupied', tone: 'blue' },
  mine: { label: 'Your reservation', tone: 'blue' },
  unavailable: { label: 'Unavailable', tone: 'gray' },
}

export const RESOURCE_STATUS = {
  active: { label: 'In service', tone: 'green' },
  maintenance: { label: 'Maintenance', tone: 'orange' },
  inactive: { label: 'Out of service', tone: 'gray' },
}

/** How a whole table stands, from its six seats. */
export const TABLE_STATE = {
  available: { label: 'Fully available', tone: 'green' },
  reserved: { label: 'Has reservations', tone: 'blue' },
  partial: { label: 'Partially available', tone: 'orange' },
  out_of_service: { label: 'Out of service', tone: 'red' },
}

export const ZONE_TYPES = {
  quiet: 'Quiet study',
  general: 'General study',
  collaborative: 'Collaborative',
  computer: 'Computer area',
}

export const SEAT_FEATURES = [
  { key: 'has_power_outlet', label: 'Power outlet' },
  { key: 'has_computer', label: 'Computer' },
  { key: 'is_accessible', label: 'Wheelchair accessible' },
]

export const ACTIVITY_CATEGORIES = {
  auth: 'Sign-ins',
  user: 'Accounts',
  reservation: 'Reservations',
  resource: 'Seats',
  settings: 'Library settings',
}

export const WEEKDAYS = [
  'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday',
]
