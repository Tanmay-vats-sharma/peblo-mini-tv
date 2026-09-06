import { createContext } from 'react'
import type { CurrentUser } from '../api/auth'

export interface AuthContextValue {
  user: CurrentUser | undefined
  hasToken: boolean
  isLoading: boolean
  loginWithPassword: (email: string, password: string) => Promise<CurrentUser>
  logout: () => void
}

export const AuthContext = createContext<AuthContextValue | undefined>(undefined)
