/**
 * 认证API服务
 */
import axios from 'axios'
import type {
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  User,
  UserUpdateRequest,
  PasswordChangeRequest,
} from '../types/auth'

// 创建专用的认证axios实例
const authAxios = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Token存储键名
const TOKEN_KEY = 'buddhist_auth_token'
const REFRESH_TOKEN_KEY = 'buddhist_refresh_token'
const USER_KEY = 'buddhist_user'

/**
 * 获取存储的token
 */
export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

/**
 * 获取存储的refresh token
 */
export function getStoredRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY)
}

/**
 * 获取存储的用户信息
 */
export function getStoredUser(): User | null {
  const userStr = localStorage.getItem(USER_KEY)
  if (userStr) {
    try {
      return JSON.parse(userStr)
    } catch {
      return null
    }
  }
  return null
}

/**
 * 保存认证信息到本地存储
 */
export function saveAuthData(data: TokenResponse): void {
  localStorage.setItem(TOKEN_KEY, data.access_token)
  if (data.refresh_token) {
    localStorage.setItem(REFRESH_TOKEN_KEY, data.refresh_token)
  }
  localStorage.setItem(USER_KEY, JSON.stringify(data.user))
}

/**
 * 清除认证信息
 */
export function clearAuthData(): void {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

/**
 * 认证API
 */
export const authApi = {
  /**
   * 用户注册
   */
  async register(data: RegisterRequest): Promise<TokenResponse> {
    const response = await authAxios.post<TokenResponse>('/api/v1/auth/register', data)
    return response.data
  },

  /**
   * 用户登录
   */
  async login(data: LoginRequest): Promise<TokenResponse> {
    const response = await authAxios.post<TokenResponse>('/api/v1/auth/login', data)
    return response.data
  },

  /**
   * 刷新Token
   */
  async refreshToken(refreshToken: string): Promise<TokenResponse> {
    const response = await authAxios.post<TokenResponse>('/api/v1/auth/refresh', {
      refresh_token: refreshToken,
    })
    return response.data
  },

  /**
   * 退出登录
   */
  async logout(token: string): Promise<void> {
    try {
      await authAxios.post('/api/v1/auth/logout', null, {
        headers: { Authorization: `Bearer ${token}` },
      })
    } catch {
      // 即使API调用失败，也清除本地存储
    }
  },

  /**
   * 获取当前用户信息
   */
  async getCurrentUser(token: string): Promise<User> {
    const response = await authAxios.get<User>('/api/v1/auth/me', {
      headers: { Authorization: `Bearer ${token}` },
    })
    return response.data
  },

  /**
   * 更新用户信息
   */
  async updateUser(token: string, data: UserUpdateRequest): Promise<User> {
    const response = await authAxios.put<User>('/api/v1/auth/me', data, {
      headers: { Authorization: `Bearer ${token}` },
    })
    return response.data
  },

  /**
   * 修改密码
   */
  async changePassword(token: string, data: PasswordChangeRequest): Promise<{ message: string }> {
    const response = await authAxios.put<{ message: string }>('/api/v1/auth/password', data, {
      headers: { Authorization: `Bearer ${token}` },
    })
    return response.data
  },
}

export default authApi
