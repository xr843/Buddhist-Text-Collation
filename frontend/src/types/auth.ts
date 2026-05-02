/**
 * 认证相关类型定义
 */

export interface User {
  id: number
  username: string
  email: string
  full_name?: string
  role: 'admin' | 'user'
  is_active: boolean
  institution?: string
  research_field?: string
  bio?: string
  avatar_url?: string
  created_at: string
  updated_at?: string
  last_login?: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
  full_name?: string
  institution?: string
}

export interface TokenResponse {
  access_token: string
  refresh_token?: string
  token_type: string
  expires_in: number
  user: User
}

export interface UserUpdateRequest {
  full_name?: string
  institution?: string
  research_field?: string
  bio?: string
  avatar_url?: string
}

export interface PasswordChangeRequest {
  old_password: string
  new_password: string
}

export interface AuthState {
  user: User | null
  token: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
}
