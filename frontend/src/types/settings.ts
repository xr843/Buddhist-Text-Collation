/**
 * 设置相关类型定义
 */

export interface APIConfig {
  key: string
  baseUrl: string
  model: string
  temperature: number
  maxTokens: number
}

export interface UIConfig {
  theme: 'light'                       // 仅支持浅色模式
  fontSize: number
  leftPanelWidth: number
  rightPanelWidth: number
  zenMode: boolean                     // 专注模式
  showPaperTexture: boolean            // 纸张纹理（保留，默认开启）
  showDiffIcons: boolean               // 差异图标
}

export interface QuotaConfig {
  dailyLimit: number // 每日Token限额
  warningThreshold: number // 预警阈值（元）
  usedToday: number // 今日已用Token数
  lastResetDate: string // 上次重置日期
}

export interface Settings {
  api: APIConfig
  ui: UIConfig
  quota: QuotaConfig
}
