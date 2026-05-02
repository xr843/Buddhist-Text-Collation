/**
 * Studio相关类型定义
 */

export type StudioToolType =
  // 核心专业工具
  | 'punctuation'
  | 'comparison'
  | 'collation'
  // 通用工具
  | 'audio'
  | 'mindmap'
  | 'study-guide'
  | 'faq'

export interface StudioTool {
  id: StudioToolType
  name: string
  description: string
  icon: string
  category: 'core' | 'general'
  enabled: boolean
}

export interface StudioOutput {
  id: number
  toolType: StudioToolType
  name: string
  content: any // 根据toolType不同，content结构不同
  createdAt: Date
  documentIds: number[] // 关联的文档
  fileSize?: number
}

export interface LayoutConfig {
  leftWidth: number // 左栏宽度
  rightWidth: number // 右栏宽度
  leftCollapsed: boolean
  rightCollapsed: boolean
}
