'use client'

import { useState, useEffect, useCallback } from 'react'
import { authApi, clearTokens, getAccessToken, type User, type LoginInput, type RegisterInput } from '@/lib/api/auth'

interface AuthState {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  error: string | null
}

export function useAuth() {
  const [state, setState] = useState<AuthState>({
    user: null,
    isLoading: true,
    isAuthenticated: false,
    error: null,
  })

  // Load user on mount if token exists
  useEffect(() => {
    const token = getAccessToken()
    if (!token) {
      setState(prev => ({ ...prev, isLoading: false }))
      return
    }

    authApi.me()
      .then(user => setState({ user, isLoading: false, isAuthenticated: true, error: null }))
      .catch(() => {
        clearTokens()
        setState({ user: null, isLoading: false, isAuthenticated: false, error: null })
      })
  }, [])

  const login = useCallback(async (input: LoginInput) => {
    setState(prev => ({ ...prev, error: null }))
    try {
      await authApi.login(input)
      const user = await authApi.me()
      setState({ user, isLoading: false, isAuthenticated: true, error: null })
      return user
    } catch (e) {
      const msg = e instanceof Error ? e.message : '登录失败'
      setState(prev => ({ ...prev, error: msg }))
      throw e
    }
  }, [])

  const register = useCallback(async (input: RegisterInput) => {
    setState(prev => ({ ...prev, error: null }))
    try {
      await authApi.register(input)
      // Auto-login after register
      const user = await login({ email: input.email, password: input.password })
      return user
    } catch (e) {
      const msg = e instanceof Error ? e.message : '注册失败'
      setState(prev => ({ ...prev, error: msg }))
      throw e
    }
  }, [login])

  const logout = useCallback(async () => {
    try {
      await authApi.logout()
    } finally {
      setState({ user: null, isLoading: false, isAuthenticated: false, error: null })
    }
  }, [])

  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }))
  }, [])

  return {
    ...state,
    login,
    register,
    logout,
    clearError,
  }
}
