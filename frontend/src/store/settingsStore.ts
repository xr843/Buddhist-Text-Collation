/**
 * 设置状态管理
 */
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Settings, APIConfig, UIConfig, QuotaConfig } from '../types/settings'

interface SettingsState {
  settings: Settings

  // API配置
  updateAPIConfig: (config: Partial<APIConfig>) => void
  getAPIConfig: () => APIConfig

  // UI配置
  updateUIConfig: (config: Partial<UIConfig>) => void
  getUIConfig: () => UIConfig

  // 专注模式
  toggleZenMode: () => void

  // 配额管理
  updateQuotaConfig: (config: Partial<QuotaConfig>) => void
  addTokenUsage: (tokens: number) => void
  resetDailyUsage: () => void
  getRemainingQuota: () => number
  isQuotaExceeded: () => boolean

  // 重置设置
  resetSettings: () => void
}

const defaultSettings: Settings = {
  api: {
    key: '',
    baseUrl: 'https://api.deepseek.com',
    model: 'deepseek-chat',
    temperature: 0.3,
    maxTokens: 4000,
  },
  ui: {
    theme: 'light',
    fontSize: 14,
    leftPanelWidth: 280,
    rightPanelWidth: 320,
    zenMode: false,
    showPaperTexture: true,
    showDiffIcons: true,
  },
  quota: {
    dailyLimit: 100000,
    warningThreshold: 10,
    usedToday: 0,
    lastResetDate: new Date().toISOString().split('T')[0],
  },
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set, get) => ({
      settings: defaultSettings,

      // API配置
      updateAPIConfig: (config) => {
        set((state) => ({
          settings: {
            ...state.settings,
            api: { ...state.settings.api, ...config },
          },
        }))
      },

      getAPIConfig: () => {
        return get().settings.api
      },

      // UI配置
      updateUIConfig: (config) => {
        set((state) => ({
          settings: {
            ...state.settings,
            ui: { ...state.settings.ui, ...config },
          },
        }))
      },

      getUIConfig: () => {
        return get().settings.ui
      },

      // 专注模式
      toggleZenMode: () => {
        set((state) => ({
          settings: {
            ...state.settings,
            ui: { ...state.settings.ui, zenMode: !state.settings.ui.zenMode },
          },
        }))
      },

      // 配额管理
      updateQuotaConfig: (config) => {
        set((state) => ({
          settings: {
            ...state.settings,
            quota: { ...state.settings.quota, ...config },
          },
        }))
      },

      addTokenUsage: (tokens) => {
        const today = new Date().toISOString().split('T')[0]
        const { lastResetDate, usedToday } = get().settings.quota

        // 如果是新的一天，重置使用量
        if (today !== lastResetDate) {
          set((state) => ({
            settings: {
              ...state.settings,
              quota: {
                ...state.settings.quota,
                usedToday: tokens,
                lastResetDate: today,
              },
            },
          }))
        } else {
          // 累加使用量
          set((state) => ({
            settings: {
              ...state.settings,
              quota: {
                ...state.settings.quota,
                usedToday: usedToday + tokens,
              },
            },
          }))
        }
      },

      resetDailyUsage: () => {
        const today = new Date().toISOString().split('T')[0]
        set((state) => ({
          settings: {
            ...state.settings,
            quota: {
              ...state.settings.quota,
              usedToday: 0,
              lastResetDate: today,
            },
          },
        }))
      },

      getRemainingQuota: () => {
        const { dailyLimit, usedToday } = get().settings.quota
        return Math.max(0, dailyLimit - usedToday)
      },

      isQuotaExceeded: () => {
        const { dailyLimit, usedToday } = get().settings.quota
        return usedToday >= dailyLimit
      },

      // 重置设置
      resetSettings: () => {
        set({ settings: defaultSettings })
      },
    }),
    {
      name: 'buddhist-settings',
    }
  )
)
