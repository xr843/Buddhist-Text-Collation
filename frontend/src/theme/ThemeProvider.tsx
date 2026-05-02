/**
 * 主题提供者组件
 *
 * 功能：
 * - 应用 Ant Design 主题配置
 * - 异步加载 Noto Serif SC 字体
 */
import { useEffect } from 'react'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { useSettingsStore } from '../store/settingsStore'
import { createThemeConfig } from '../theme/theme'

interface ThemeProviderProps {
  children: React.ReactNode
}

export default function ThemeProvider({ children }: ThemeProviderProps) {
  const { settings } = useSettingsStore()
  const { zenMode } = settings.ui

  // 生成 Ant Design 主题配置（仅浅色模式）
  const antdThemeConfig = createThemeConfig('light')

  // 应用专注模式
  useEffect(() => {
    const root = document.documentElement
    if (zenMode) {
      root.classList.add('zen-mode')
    } else {
      root.classList.remove('zen-mode')
    }
  }, [zenMode])

  // 异步加载 Noto Serif SC 字体
  useEffect(() => {
    // 检查是否已加载
    const existingLink = document.querySelector('link[href*="Noto+Serif+SC"]')
    if (existingLink) return

    const link = document.createElement('link')
    link.href = 'https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600;700&display=swap'
    link.rel = 'stylesheet'
    link.crossOrigin = 'anonymous'

    // 字体加载完成后添加类标记
    link.onload = () => {
      document.documentElement.classList.add('noto-serif-loaded')
    }

    document.head.appendChild(link)
  }, [])

  return (
    <ConfigProvider
      locale={zhCN}
      theme={antdThemeConfig}
    >
      {children}
    </ConfigProvider>
  )
}
