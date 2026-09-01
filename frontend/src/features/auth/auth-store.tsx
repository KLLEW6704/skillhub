import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { apiRequest, TOKEN_KEY } from '../../lib/api'
import type { TokenResponse, User } from '../../lib/types'

interface AuthContextValue {
  user: User | null
  isLoading: boolean
  login: (username: string, password: string) => Promise<User>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setLoading] = useState(Boolean(localStorage.getItem(TOKEN_KEY)))

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    setUser(null)
  }, [])

  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY)
    if (!token) {
      setLoading(false)
      return
    }
    apiRequest<User>('/api/v1/auth/me')
      .then(setUser)
      .catch(logout)
      .finally(() => setLoading(false))
  }, [logout])

  useEffect(() => {
    window.addEventListener('skillhub:unauthorized', logout)
    return () => window.removeEventListener('skillhub:unauthorized', logout)
  }, [logout])

  const login = useCallback(async (username: string, password: string) => {
    const body = new URLSearchParams({ username, password })
    const token = await apiRequest<TokenResponse>('/api/v1/auth/login', { method: 'POST', body })
    localStorage.setItem(TOKEN_KEY, token.access_token)
    const current = await apiRequest<User>('/api/v1/auth/me')
    setUser(current)
    return current
  }, [])

  const value = useMemo(() => ({ user, isLoading, login, logout }), [user, isLoading, login, logout])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside AuthProvider')
  return context
}
