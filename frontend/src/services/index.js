/**
 * One function per backend endpoint, grouped by feature. Components import
 * from here and never build URLs themselves.
 */
import { api, refreshSession } from './apiClient'

const AJAX = { 'X-Requested-With': 'XMLHttpRequest' }

export const authService = {
  restore: () => refreshSession(),
  login: (email, password) => api.post('/auth/login/', { email, password }, { auth: false }),
  register: (data) => api.post('/auth/register/', data, { auth: false }),
  logout: () => api.post('/auth/logout/', {}, { auth: false, headers: AJAX }),
  updateProfile: (data) => api.patch('/auth/me/', data),
  changePassword: (data) => api.post('/auth/change-password/', data),
}

export const libraryService = {
  overview: () => api.get('/library/overview/'),
  saveHours: (hours) => api.put('/library/hours/', hours),
  closures: () => api.get('/library/closures/'),
  addClosure: (data) => api.post('/library/closures/', data),
  removeClosure: (id) => api.delete(`/library/closures/${id}/`),
  savePolicy: (data) => api.patch('/library/policy/', data),
  floors: () => api.get('/library/floors/'),
  createFloor: (data) => api.post('/library/floors/', data),
  updateFloor: (id, data) => api.patch(`/library/floors/${id}/`, data),
  deleteFloor: (id) => api.delete(`/library/floors/${id}/`),
}

export const seatService = {
  availability: (params) => api.get('/seats/availability/', params),
  schedule: (id, date) => api.get(`/seats/${id}/schedule/`, { date }),
  list: (params) => api.get('/seats/', params),
  create: (data) => api.post('/seats/', data),
  update: (id, data) => api.patch(`/seats/${id}/`, data),
  remove: (id) => api.delete(`/seats/${id}/`),
  setStatus: (id, data) => api.post(`/seats/${id}/set-status/`, data),
  zones: (params) => api.get('/seats/zones/', params),
  createZone: (data) => api.post('/seats/zones/', data),
  updateZone: (id, data) => api.patch(`/seats/zones/${id}/`, data),
  deleteZone: (id) => api.delete(`/seats/zones/${id}/`),
}

export const roomService = {
  availability: (params) => api.get('/study-rooms/availability/', params),
  schedule: (id, date) => api.get(`/study-rooms/${id}/schedule/`, { date }),
  list: (params) => api.get('/study-rooms/', params),
  get: (id) => api.get(`/study-rooms/${id}/`),
  create: (data) => api.post('/study-rooms/', data),
  update: (id, data) => api.patch(`/study-rooms/${id}/`, data),
  remove: (id) => api.delete(`/study-rooms/${id}/`),
  setStatus: (id, data) => api.post(`/study-rooms/${id}/set-status/`, data),
  facilities: () => api.get('/study-rooms/facilities/'),
  createFacility: (name) => api.post('/study-rooms/facilities/', { name }),
}

export const reservationService = {
  list: (params) => api.get('/reservations/', params),
  get: (id) => api.get(`/reservations/${id}/`),
  create: (data) => api.post('/reservations/', data),
  cancel: (id, reason = '') => api.post(`/reservations/${id}/cancel/`, { reason }),
  checkIn: (id) => api.post(`/reservations/${id}/check-in/`),
  checkOut: (id) => api.post(`/reservations/${id}/check-out/`),
  markNoShow: (id) => api.post(`/reservations/${id}/no-show/`),
  lookup: (code) => api.get('/reservations/lookup/', { code }),
  limits: () => api.get('/reservations/limits/'),
}

export const notificationService = {
  list: (params) => api.get('/notifications/', params),
  unreadCount: () => api.get('/notifications/unread-count/'),
  markRead: (id) => api.post(`/notifications/${id}/read/`),
  markAllRead: () => api.post('/notifications/read-all/'),
  remove: (id) => api.delete(`/notifications/${id}/`),
}

export const userService = {
  list: (params) => api.get('/users/', params),
  create: (data) => api.post('/users/', data),
  update: (id, data) => api.patch(`/users/${id}/`, data),
  activate: (id) => api.post(`/users/${id}/activate/`),
  deactivate: (id) => api.post(`/users/${id}/deactivate/`),
  setPassword: (id, new_password) => api.post(`/users/${id}/set-password/`, { new_password }),
  searchStudents: (search) => api.get('/users/students/', { search }),
  lookupStudent: (student_id) => api.get('/users/lookup/', { student_id }),
}

export const reportService = {
  studentDashboard: () => api.get('/reports/student-dashboard/'),
  staffDashboard: () => api.get('/reports/staff-dashboard/'),
  adminDashboard: () => api.get('/reports/admin-dashboard/'),
  usage: (days) => api.get('/reports/usage/', { days }),
}

export const activityService = {
  list: (params) => api.get('/activity/', params),
}
