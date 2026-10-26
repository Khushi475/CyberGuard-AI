/**
 * Central API client.
 *
 * Every network call in the application goes through this module, which gives
 * one place for the base URL, the auth token, and - importantly for the error
 * handling requirement - the translation of any failure into a readable message.
 */
import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'
const TOKEN_KEY = 'cyberguard.token'
const USER_KEY = 'cyberguard.user'

export const tokenStore = {
  get: () => localStorage.getItem(TOKEN_KEY) || sessionStorage.getItem(TOKEN_KEY),
  set: (token, remember = true) => {
    const store = remember ? localStorage : sessionStorage
    const other = remember ? sessionStorage : localStorage
    store.setItem(TOKEN_KEY, token)
    other.removeItem(TOKEN_KEY)
  },
  clear: () => {
    localStorage.removeItem(TOKEN_KEY)
    sessionStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    sessionStorage.removeItem(USER_KEY)
  },
}

export const userStore = {
  get: () => {
    const raw = localStorage.getItem(USER_KEY) || sessionStorage.getItem(USER_KEY)
    try {
      return raw ? JSON.parse(raw) : null
    } catch {
      return null
    }
  },
  set: (user, remember = true) => {
    const store = remember ? localStorage : sessionStorage
    store.setItem(USER_KEY, JSON.stringify(user))
  },
}

const client = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

client.interceptors.request.use((config) => {
  const token = tokenStore.get()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

/** A network/HTTP failure converted into something a user can act on. */
export class ApiError extends Error {
  constructor(message, { status = 0, code = 'UNKNOWN', details = null } = {}) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.details = details
  }

  get isOffline() {
    return this.code === 'BACKEND_UNAVAILABLE'
  }

  get isAuth() {
    return this.status === 401
  }
}

let onUnauthorized = null
/** Registered by AuthContext so a 401 anywhere logs the user out cleanly. */
export const setUnauthorizedHandler = (handler) => {
  onUnauthorized = handler
}

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === 'ECONNABORTED') {
      return Promise.reject(
        new ApiError('The request timed out. The backend may be busy - please try again.', {
          code: 'TIMEOUT',
        }),
      )
    }

    if (!error.response) {
      return Promise.reject(
        new ApiError(
          'Cannot reach the CyberGuard AI backend. Start it with "python run.py" in the backend folder, then retry.',
          { code: 'BACKEND_UNAVAILABLE' },
        ),
      )
    }

    const { status, data } = error.response
    const message =
      data?.message ||
      (status === 404
        ? 'The requested resource was not found.'
        : status >= 500
          ? 'The server encountered an internal error. Check the backend console for details.'
          : 'The request could not be completed.')

    if (status === 401 && onUnauthorized) onUnauthorized()

    return Promise.reject(
      new ApiError(message, { status, code: data?.error || `HTTP_${status}`, details: data?.details }),
    )
  },
)

/** Unwraps the `{ success, data }` envelope the backend always returns. */
const unwrap = (response) => response.data?.data ?? response.data
/** Keeps the envelope when pagination/filters metadata is needed. */
const whole = (response) => response.data

export const api = {
  // --- auth ---------------------------------------------------------------
  login: (email, password) => client.post('/auth/login', { email, password }).then(unwrap),
  logout: () => client.post('/auth/logout').then(unwrap),
  me: () => client.get('/auth/me').then(unwrap),
  updateProfile: (payload) => client.put('/auth/profile', payload).then(unwrap),
  updatePreferences: (payload) => client.put('/auth/preferences', payload).then(unwrap),
  changePassword: (payload) => client.put('/auth/password', payload).then(unwrap),

  // --- dashboard & analytics ---------------------------------------------
  dashboardStats: (days = 14) => client.get('/dashboard/stats', { params: { days } }).then(unwrap),
  activityFeed: (limit = 15) => client.get('/dashboard/activity', { params: { limit } }).then(unwrap),
  threatLevel: () => client.get('/dashboard/threat-level').then(unwrap),
  analytics: (days = 30) => client.get('/analytics', { params: { days } }).then(unwrap),

  // --- events & detection -------------------------------------------------
  listEvents: (params) => client.get('/events', { params }).then(whole),
  getEvent: (id) => client.get(`/events/${id}`).then(unwrap),
  createEvent: (payload) => client.post('/events', payload).then(unwrap),
  analyzeEvent: (payload, persist = true) =>
    client.post('/events/analyze', payload, { params: { persist } }).then(unwrap),
  sampleEvents: () => client.get('/events/sample').then(unwrap),
  uploadLogs: (file, onProgress) => {
    const form = new FormData()
    form.append('file', file)
    return client
      .post('/events/upload', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 120000,
        onUploadProgress: (event) => {
          if (onProgress && event.total) {
            onProgress(Math.round((event.loaded * 100) / event.total))
          }
        },
      })
      .then(unwrap)
  },

  // --- threats & intelligence --------------------------------------------
  listThreats: (params) => client.get('/threats', { params }).then(whole),
  getThreat: (id) => client.get(`/threats/${id}`).then(unwrap),
  listIndicators: (params) => client.get('/threat-intelligence', { params }).then(whole),
  updateIndicator: (id, payload) => client.put(`/threat-intelligence/${id}`, payload).then(unwrap),

  // --- alerts -------------------------------------------------------------
  listAlerts: (params) => client.get('/alerts', { params }).then(whole),
  getAlert: (id) => client.get(`/alerts/${id}`).then(unwrap),
  updateAlert: (id, payload) => client.put(`/alerts/${id}`, payload).then(unwrap),
  escalateAlert: (id, payload = {}) => client.post(`/alerts/${id}/escalate`, payload).then(unwrap),

  // --- incidents ----------------------------------------------------------
  listIncidents: (params) => client.get('/incidents', { params }).then(whole),
  getIncident: (id) => client.get(`/incidents/${id}`).then(unwrap),
  createIncident: (payload) => client.post('/incidents', payload).then(unwrap),
  updateIncident: (id, payload) => client.put(`/incidents/${id}`, payload).then(unwrap),

  // --- assets -------------------------------------------------------------
  listAssets: (params) => client.get('/assets', { params }).then(whole),
  getAsset: (id) => client.get(`/assets/${id}`).then(unwrap),
  createAsset: (payload) => client.post('/assets', payload).then(unwrap),
  updateAsset: (id, payload) => client.put(`/assets/${id}`, payload).then(unwrap),
  deleteAsset: (id) => client.delete(`/assets/${id}`).then(unwrap),

  // --- reports ------------------------------------------------------------
  listReports: (params) => client.get('/reports', { params }).then(whole),
  previewReport: (days = 30) => client.get('/reports/preview', { params: { days } }).then(unwrap),
  getReport: (id) => client.get(`/reports/${id}`).then(unwrap),
  generateReport: (payload) => client.post('/reports/generate', payload).then(unwrap),
  downloadReport: (id, format = 'pdf') =>
    client.get(`/reports/${id}/download`, { params: { format }, responseType: 'blob' }),
  deleteReport: (id) => client.delete(`/reports/${id}`).then(unwrap),

  // --- system -------------------------------------------------------------
  health: () => client.get('/health').then(unwrap),
  systemStatus: () => client.get('/system/status').then(unwrap),
  reloadModel: () => client.post('/system/reload-model').then(unwrap),
  auditLogs: (limit = 100) => client.get('/audit-logs', { params: { limit } }).then(unwrap),
  apiIndex: () => client.get('').then(unwrap),
}

/** Turn a blob response into a browser download. */
export const saveBlob = (response, fallbackName) => {
  const disposition = response.headers?.['content-disposition'] || ''
  const match = disposition.match(/filename="?([^"]+)"?/)
  const filename = match ? match[1] : fallbackName
  const url = window.URL.createObjectURL(new Blob([response.data]))
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
  return filename
}

export default api
