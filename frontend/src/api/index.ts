import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export const authApi = {
  login: (username: string, password: string) => {
    const formData = new URLSearchParams()
    formData.append('username', username)
    formData.append('password', password)
    return api.post('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
  },
  register: (data: any) => api.post('/auth/register', data),
  getMe: () => api.get('/auth/me'),
}

export const studyRoomApi = {
  list: (params?: any) => api.get('/study-rooms', { params }),
  get: (id: number) => api.get(`/study-rooms/${id}`),
  create: (data: any) => api.post('/study-rooms', data),
  update: (id: number, data: any) => api.put(`/study-rooms/${id}`, data),
  delete: (id: number) => api.delete(`/study-rooms/${id}`),
}

export const shiftApi = {
  list: (params?: any) => api.get('/shifts', { params }),
  get: (id: number) => api.get(`/shifts/${id}`),
  create: (data: any) => api.post('/shifts', data),
  update: (id: number, data: any) => api.put(`/shifts/${id}`, data),
  publish: (id: number) => api.post(`/shifts/${id}/publish`),
  cancel: (id: number) => api.post(`/shifts/${id}/cancel`),
  delete: (id: number) => api.delete(`/shifts/${id}`),
}

export const signupApi = {
  list: (params?: any) => api.get('/signups', { params }),
  get: (id: number) => api.get(`/signups/${id}`),
  create: (data: any) => api.post('/signups', data),
  approve: (id: number, reviewNotes?: string) =>
    api.put(`/signups/${id}/approve`, null, { params: { review_notes: reviewNotes } }),
  reject: (id: number, reviewNotes?: string) =>
    api.put(`/signups/${id}/reject`, null, { params: { review_notes: reviewNotes } }),
  cancel: (id: number) => api.delete(`/signups/${id}`),
  checkConflict: (shiftId: number) =>
    api.get('/signups/check/conflict', { params: { shift_id: shiftId } }),
}

export const attendanceApi = {
  list: (params?: any) => api.get('/attendance', { params }),
  getByShift: (shiftId: number) => api.get(`/attendance/shift/${shiftId}`),
  checkIn: (shiftId: number) => api.post('/attendance/check-in', null, { params: { shift_id: shiftId } }),
  checkOut: (shiftId: number) => api.post('/attendance/check-out', null, { params: { shift_id: shiftId } }),
  my: () => api.get('/attendance/my'),
}

export const leaveApi = {
  list: (params?: any) => api.get('/leave', { params }),
  get: (id: number) => api.get(`/leave/${id}`),
  create: (data: any) => api.post('/leave', data),
  approve: (id: number, reviewNotes?: string) =>
    api.put(`/leave/${id}/approve`, null, { params: { review_notes: reviewNotes } }),
  reject: (id: number, reviewNotes?: string) =>
    api.put(`/leave/${id}/reject`, null, { params: { review_notes: reviewNotes } }),
  listReplacements: (params?: any) => api.get('/leave/replacements/todos', { params }),
  assignReplacement: (todoId: number, assignedTo: number) =>
    api.put(`/leave/replacements/${todoId}/assign`, null, { params: { assigned_to: assignedTo } }),
  completeReplacement: (todoId: number) =>
    api.put(`/leave/replacements/${todoId}/complete`),
}

export const volunteerApi = {
  list: (params?: any) => api.get('/volunteers', { params }),
  get: (id: number) => api.get(`/volunteers/${id}`),
  getMyProfile: () => api.get('/volunteers/profile/me'),
  updateTraining: (id: number, data: any) =>
    api.put(`/volunteers/profile/${id}/training`, null, { params: data }),
}

export const statsApi = {
  overview: () => api.get('/stats/overview'),
  volunteerHours: () => api.get('/stats/volunteer-hours'),
  roomUsage: () => api.get('/stats/room-usage'),
}

export const auditApi = {
  list: (params?: any) => api.get('/audit', { params }),
}

export const healthCheck = () => axios.get('/health')

export default api
