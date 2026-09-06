import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useCallback, useMemo, useState, type ReactNode } from 'react'
import { getCurrentUser, login } from '../api/auth'
import { clearStoredAccessToken, getStoredAccessToken, storeAccessToken } from '../api/client'
import { AuthContext } from './AuthContext'

const CURRENT_USER_QUERY_KEY = ['current-user']

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  const [hasToken, setHasToken] = useState(() => Boolean(getStoredAccessToken()))
  const userQuery = useQuery({ queryKey: CURRENT_USER_QUERY_KEY, queryFn: getCurrentUser, enabled: hasToken })
  const logout = useCallback(() => {
    clearStoredAccessToken()
    setHasToken(false)
    queryClient.removeQueries({ queryKey: CURRENT_USER_QUERY_KEY })
  }, [queryClient])

  const loginWithPassword = useCallback(async (email: string, password: string) => {
    const response = await login(email, password)
    storeAccessToken(response.access_token)
    setHasToken(true)
    return queryClient.fetchQuery({ queryKey: CURRENT_USER_QUERY_KEY, queryFn: getCurrentUser })
  }, [queryClient])

  const value = useMemo(() => ({
    user: userQuery.data,
    hasToken,
    isLoading: hasToken && userQuery.isLoading,
    loginWithPassword,
    logout,
  }), [hasToken, loginWithPassword, logout, userQuery.data, userQuery.isLoading])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
