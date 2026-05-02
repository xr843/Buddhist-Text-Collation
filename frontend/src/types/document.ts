/**
 * 文档相关类型定义
 */

export interface Document {
  id: number
  name: string
  content: string
  type: 'original' | 'punctuated' | 'comparison' // 原文/已标点/对比结果
  charCount: number
  createdAt: Date
  updatedAt: Date
  groupId?: number
  tags?: string[]
  metadata?: DocumentMetadata
}

export interface DocumentMetadata {
  translator?: string // 译者
  dynasty?: string // 朝代
  source?: string // 来源（如CBETA编号）
  versionLabel?: string // 版本标签
  notes?: string // 备注
}

export interface DocumentGroup {
  id: number
  name: string
  description?: string
  createdAt: Date
  documentIds: number[]
}

export interface DocumentUploadResult {
  success: boolean
  document?: Document
  error?: string
}
