/**
 * 认证状态管理
 */
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User, LoginRequest, RegisterRequest, UserUpdateRequest, PasswordChangeRequest } from '../types/auth'
import {
  authApi,
  saveAuthData,
  clearAuthData,
  getStoredToken,
  getStoredRefreshToken,
  getStoredUser,
} from '../services/authApi'

interface AuthState {
  // 状态
  user: User | null
  token: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null

  // 操作
  login: (data: LoginRequest) => Promise<void>
  register: (data: RegisterRequest) => Promise<void>
  logout: () => Promise<void>
  refreshAuth: () => Promise<boolean>
  updateProfile: (data: UserUpdateRequest) => Promise<void>
  changePassword: (data: PasswordChangeRequest) => Promise<void>
  checkAuth: () => Promise<void>
  clearError: () => void

  // 辅助方法
  isAdmin: () => boolean
  getToken: () => string | null
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // 初始状态
      user: getStoredUser(),
      token: getStoredToken(),
      refreshToken: getStoredRefreshToken(),
      isAuthenticated: !!getStoredToken(),
      isLoading: false,
      error: null,

      // 登录
      login: async (data: LoginRequest) => {
        set({ isLoading: true, error: null })
        try {
          const response = await authApi.login(data)
          saveAuthData(response)
          set({
            user: response.user,
            token: response.access_token,
            refreshToken: response.refresh_token || null,
            isAuthenticated: true,
            isLoading: false,
          })
        } catch (error: any) {
          const message = error.response?.data?.detail || error.message || '登录失败'
          set({ error: message, isLoading: false })
          throw new Error(message)
        }
      },

      // 注册
      register: async (data: RegisterRequest) => {
        set({ isLoading: true, error: null })
        try {
          const response = await authApi.register(data)
          saveAuthData(response)
          set({
            user: response.user,
            token: response.access_token,
            refreshToken: response.refresh_token || null,
            isAuthenticated: true,
            isLoading: false,
          })
        } catch (error: any) {
          const message = error.response?.data?.detail || error.message || '注册失败'
          set({ error: message, isLoading: false })
          throw new Error(message)
        }
      },

      // 退出登录
      logout: async () => {
        const { token } = get()
        if (token) {
          await authApi.logout(token)
        }
        clearAuthData()
        set({
          user: null,
          token: null,
          refreshToken: null,
          isAuthenticated: false,
          error: null,
        })
      },

      // 刷新认证
      refreshAuth: async () => {
        const { refreshToken } = get()
        if (!refreshToken) {
          return false
        }

        try {
          const response = await authApi.refreshToken(refreshToken)
          saveAuthData(response)
          set({
            user: response.user,
            token: response.access_token,
            refreshToken: response.refresh_token || null,
            isAuthenticated: true,
          })
          return true
        } catch (error) {
          // 刷新失败，清除认证状态
          clearAuthData()
          set({
            user: null,
            token: null,
            refreshToken: null,
            isAuthenticated: false,
          })
          return false
        }
      },

      // 更新用户资料
      updateProfile: async (data: UserUpdateRequest) => {
        const { token } = get()
        if (!token) {
          throw new Error('未登录')
        }

        set({ isLoading: true, error: null })
        try {
          const user = await authApi.updateUser(token, data)
          localStorage.setItem('buddhist_user', JSON.stringify(user))
          set({ user, isLoading: false })
        } catch (error: any) {
          const message = error.response?.data?.detail || error.message || '更新失败'
          set({ error: message, isLoading: false })
          throw new Error(message)
        }
      },

      // 修改密码
      changePassword: async (data: PasswordChangeRequest) => {
        const { token } = get()
        if (!token) {
          throw new Error('未登录')
        }

        set({ isLoading: true, error: null })
        try {
          await authApi.changePassword(token, data)
          set({ isLoading: false })
        } catch (error: any) {
          const message = error.response?.data?.detail || error.message || '修改密码失败'
          set({ error: message, isLoading: false })
          throw new Error(message)
        }
      },

      // 检查认证状态
      checkAuth: async () => {
        const { token, refreshAuth } = get()
        if (!token) {
          return
        }

        try {
          const user = await authApi.getCurrentUser(token)
          localStorage.setItem('buddhist_user', JSON.stringify(user))
          set({ user, isAuthenticated: true })
        } catch (error: any) {
          // Token可能过期，尝试刷新
          if (error.response?.status === 401) {
            const success = await refreshAuth()
            if (!success) {
              clearAuthData()
              set({
                user: null,
                token: null,
                refreshToken: null,
                isAuthenticated: false,
              })
            }
          }
        }
      },

      // 清除错误
      clearError: () => {
        set({ error: null })
      },

      // 是否是管理员
      isAdmin: () => {
        const { user } = get()
        return user?.role === 'admin'
      },

      // 获取当前token
      getToken: () => {
        return get().token
      },
    }),
    {
      name: 'buddhist-auth',
      partialize: (state) => ({
        // 只持久化这些字段
        user: state.user,
        token: state.token,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)

export default useAuthStore
