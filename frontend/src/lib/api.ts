import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

// Global error interceptor — surface API errors for React Query to consume
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      'Unknown error occurred'
    return Promise.reject(new Error(message))
  }
)
