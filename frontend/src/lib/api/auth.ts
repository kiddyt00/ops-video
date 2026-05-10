import { api } from '@/lib/api'

// ─── Types ────────────────────────────────────────────────────────────

export interface User {
  id: string
  email: string
  username: string
  full_name: string | null
  role: 'user' | 'admin'
  is_active: boolean
  is_verified: boolean
  created_at: string
  updated_at: string
  last_login_at: string | null
}

export interface RegisterInput {
  email: string
  username: string
  password: string
  full_name?: string
}

export interface LoginInput {
  email: string
  password: string
}

export interface TokenPair {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

// ─── Token Storage ─────────────────────────────────────────────────────

const TOKEN_KEY = 'ops-video-tokens'

function getTokens(): TokenPair | null {
  if (typeof window === 'undefined') return null
  try {
    const raw = localStorage.getItem(TOKEN_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

function setTokens(tokens: TokenPair) {
  localStorage.setItem(TOKEN_KEY, JSON.stringify(tokens))
}

export function clearTokens() {
  localStorage.removeItem(TOKEN_KEY)
}

export function getAccessToken(): string | null {
  return getTokens()?.access_token ?? null
}

// ─── API Methods ───────────────────────────────────────────────────────

export const authApi = {
  register: (data: RegisterInput) =>
    api.post<User>('/auth/register', data).then(r => r.data),

  login: (data: LoginInput) =>
    api.post<TokenPair>('/auth/login', data).then(r => {
      setTokens(r.data)
      return r.data
    }),

  refresh: () => {
    const tokens = getTokens()
    if (!tokens?.refresh_token) return Promise.reject(new Error('No refresh token'))
    return api.post<TokenPair>('/auth/refresh', { refresh_token: tokens.refresh_token }).then(r => {
      setTokens(r.data)
      return r.data
    })
  },

  me: () => api.get<User>('/auth/me').then(r => r.data),

  logout: () => {
    const tokens = getTokens()
    clearTokens()
    if (tokens?.access_token) {
      return api.post('/auth/logout').catch(() => { /* ignore */ })
    }
    return Promise.resolve()
  },

  updateProfile: (data: { username?: string; full_name?: string; avatar_url?: string }) =>
    api.put<User>('/auth/me', data).then(r => r.data),
}

// ─── Axios Interceptor ─────────────────────────────────────────────────

let isRefreshing = false
let refreshPromise: Promise<TokenPair> | null = null

api.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    // Only retry 401s on auth-protected endpoints (skip login/register)
    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      !originalRequest.url?.includes('/auth/login') &&
      !originalRequest.url?.includes('/auth/register') &&
      !originalRequest.url?.includes('/auth/refresh')
    ) {
      originalRequest._retry = true

      if (!isRefreshing) {
        isRefreshing = true
        refreshPromise = authApi.refresh().catch(() => {
          clearTokens()
          if (typeof window !== 'undefined') {
            window.location.href = '/login'
          }
          return Promise.reject(error)
        }).finally(() => {
          isRefreshing = false
          refreshPromise = null
        })
      }

      const tokens = await refreshPromise
      if (tokens) {
        originalRequest.headers.Authorization = `Bearer ${tokens.access_token}`
        return api(originalRequest)
      }
    }

    return Promise.reject(error)
  }
)
