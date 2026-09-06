import { api } from './client'

export type UserRole = 'admin' | 'editor' | 'viewer'

export interface CurrentUser {
  id: number
  email: string
  role: UserRole
  is_active: boolean
}

interface LoginResponse {
  access_token: string
  token_type: string
}

export async function login(email: string, password: string): Promise<LoginResponse> {
  const response = await api.post<LoginResponse>('/auth/login', { email, password })
  return response.data
}

export async function getCurrentUser(): Promise<CurrentUser> {
  const response = await api.get<CurrentUser>('/auth/me')
  return response.data
}
